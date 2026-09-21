from django.test import TestCase, override_settings
from model_bakery import baker
from productos.models import UnitOfMeasure, ProductGroup, Product
from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse
from django.utils import timezone
from contabilidad.models import StockType
from almacen.models import Warehouse, Kardex
from datetime import date, datetime
from decimal import Decimal
import tempfile

# Create your tests here.
"""class NewUnidadMedidaTestCase(TestCase):
    fixtures = ['usuarios.json','unidadesmedida.json']
    
    def test_index(self):
        resp = self.client.get("/")
        self.assertEqual(resp.status_code,200)
        
    def test_new_unidad_medida_view(self):
        self.client.login(username='test',password='test')
        resp = self.client.get('/productos/unit_of_measure_create/')
        self.assertEqual(200,resp.status_code)"""


class UnidadMedidaTest(TestCase):

    def setUp(self):
        self.um1 = baker.make(UnitOfMeasure)
        self.um2 = baker.make(UnitOfMeasure)
        self.um3 = baker.make(UnitOfMeasure)

    def test_creacion_unidad_medida(self):
        self.assertTrue(isinstance(self.um1, UnitOfMeasure))
        self.assertEqual(self.um1.__str__(), self.um1.description)

    def test_siguiente_unidad_medida(self):
        self.assertEqual(self.um3.pk, self.um2.next())

    def test_anterior_unidad_medida(self):
        self.assertEqual(self.um2.pk, self.um3.previous())

    def test_primera_unidad_medida(self):
        self.assertEqual(self.um1.pk, self.um3.next())

    def test_ultima_unidad_medida(self):
        self.assertEqual(self.um3.pk, self.um1.previous())


class GrupoProductosTest(TestCase):

    def setUp(self):
        self.gp1 = baker.make(ProductGroup, code='')
        self.gp2 = baker.make(ProductGroup, code='')
        self.gp3 = baker.make(ProductGroup, code='')

    def test_creacion_grupo_productos(self):
        self.assertTrue(isinstance(self.gp1, ProductGroup))
        self.assertEqual("1".zfill(6), self.gp1.code)
        self.assertEqual(self.gp1.__str__(), self.gp1.description)

    def test_siguiente_grupo_productos(self):
        self.assertEqual(self.gp2.pk, self.gp1.next())
        self.assertEqual(self.gp3.pk, self.gp2.next())

    def test_anterior_grupo_productos(self):
        self.assertEqual(self.gp1.pk, self.gp2.previous())
        self.assertEqual(self.gp2.pk, self.gp3.previous())

    def test_primer_grupo_productos(self):
        self.assertEqual(self.gp1.pk, self.gp3.next())

    def test_ultimo_grupo_productos(self):
        self.assertEqual(self.gp3.pk, self.gp1.previous())


class ProductoTest(TestCase):

    def setUp(self):
        self.gp1 = baker.make(ProductGroup, code='')
        self.gp2 = baker.make(ProductGroup, code='')
        self.p1 = baker.make(Product, code='', product_group=self.gp1)
        self.p2 = baker.make(Product, code='', product_group=self.gp1)
        self.p3 = baker.make(Product, code='', product_group=self.gp2, is_service=True)

    def test_creacion_producto(self):
        self.assertTrue(isinstance(self.p1, Product))
        self.assertEqual(self.gp1.code + "1".zfill(4), self.p1.code)
        self.assertEqual(self.gp1.code + "2".zfill(4), self.p2.code)
        self.assertEqual(self.p1.__str__(), self.p1.description)

    def test_siguiente_producto(self):
        self.assertEqual(self.p2.pk, self.p1.next())
        self.assertEqual(self.p3.pk, self.p2.next())

    def test_anterior_producto(self):
        self.assertEqual(self.p1.pk, self.p2.previous())
        self.assertEqual(self.p2.pk, self.p3.previous())

    def test_primer_producto(self):
        self.assertEqual(self.p1.pk, self.p3.next())

    def test_ultimo_producto(self):
        self.assertEqual(self.p3.pk, self.p1.previous())

    def test_creacion_servicio(self):
        self.assertEqual(self.p3.unit_of_measure.code, 'SERV')


class ConsultaDeStockTest(TestCase):
    """Product.stock recorria todos los almacenes con un .latest() cada uno, y
    las plantillas lo invocan varias veces en la misma page."""

    def test_una_sola_consulta_y_luego_cache(self):
        from almacen.models import Warehouse
        baker.make(Warehouse)
        baker.make(Warehouse)
        product = baker.make(Product)

        with self.assertNumQueries(1):
            product.stock

        with self.assertNumQueries(0):
            product.stock

    def test_previsto_es_una_sola_consulta(self):
        product = baker.make(Product)

        with self.assertNumQueries(1):
            product.forecast

        with self.assertNumQueries(0):
            product.forecast


class ObtenerKardexTest(TestCase):
    """`get_kardex` hacia un `len()` que cargaba todas las filas y despues
    cuatro `aggregate` por separado: cinco consultas por producto, en reportes
    que recorren el catalogo entero."""

    def setUp(self):
        self.warehouse = baker.make(Warehouse)
        self.product = baker.make(Product)
        baker.make(Kardex, warehouse=self.warehouse, product=self.product,
                   operation_date=timezone.make_aware(datetime(2024, 1, 15, 12, 0)),
                   in_quantity=Decimal('10'), in_amount=Decimal('50'),
                   out_quantity=Decimal('2'), out_amount=Decimal('9'))

    def test_los_totales_salen_de_una_sola_consulta(self):
        with self.assertNumQueries(1):
            listado, quantity_i, valor_i, quantity_s, valor_s = self.product.get_kardex(
                self.warehouse, date(2024, 1, 1), date(2024, 1, 31))

        self.assertEqual((quantity_i, valor_i), (Decimal('10'), Decimal('50')))
        self.assertEqual((quantity_s, valor_s), (Decimal('2'), Decimal('9')))
        self.assertEqual(listado.count(), 1)

    def test_sin_movimientos_los_totales_son_cero(self):
        with self.assertNumQueries(1):
            _, quantity_i, valor_i, quantity_s, valor_s = self.product.get_kardex(
                self.warehouse, date(2024, 3, 1), date(2024, 3, 31))

        self.assertEqual((quantity_i, valor_i, quantity_s, valor_s), (0, 0, 0, 0))

    def test_el_grupo_usa_el_mismo_camino(self):
        group = self.product.product_group

        with self.assertNumQueries(1):
            _, quantity_i, valor_i, quantity_s, valor_s = group.get_kardex(
                self.warehouse, date(2024, 1, 1), date(2024, 1, 31))

        self.assertEqual((quantity_i, valor_i, quantity_s, valor_s),
                         (Decimal('10'), Decimal('50'), Decimal('2'), Decimal('9')))


@override_settings(MEDIA_ROOT=tempfile.mkdtemp())
class CargarServiciosTest(TestCase):
    """`ServiceImport` devolvia dentro del bucle, asi que importaba solo la
    primera fila del CSV y el resto se perdia en silencio."""

    def setUp(self):
        self.client.force_login(User.objects.create_superuser('cargador', 'c@example.com', 'key-segura'))

    def test_importa_todas_las_filas(self):
        baker.make(ProductGroup, code='000001')
        contenido = '000001,SERVICIO UNO\n000001,SERVICIO DOS\n'
        file = SimpleUploadedFile('servicios.csv', contenido.encode('utf8'), content_type='text/csv')

        respuesta = self.client.post('/productos/service_import/', {'file': file})

        self.assertEqual(respuesta.status_code, 302)
        self.assertEqual(sorted(Product.objects.values_list('description', flat=True)),
                         ['SERVICIO DOS', 'SERVICIO UNO'])

    def test_sin_grupo_manda_a_crearlos(self):
        contenido = 'G99,SERVICIO UNO\n'
        file = SimpleUploadedFile('servicios.csv', contenido.encode('utf8'), content_type='text/csv')

        respuesta = self.client.post('/productos/service_import/', {'file': file})

        self.assertEqual(respuesta.status_code, 302)
        self.assertEqual(respuesta.url, reverse('productos:product_group_create'))
        self.assertEqual(Product.objects.count(), 0)


@override_settings(MEDIA_ROOT=tempfile.mkdtemp())
class CargarProductosTest(TestCase):
    def setUp(self):
        self.client.force_login(User.objects.create_superuser('cargador', 'c@example.com', 'key-segura'))

    def test_salta_la_fila_sin_tipo_de_existencia(self):
        baker.make(ProductGroup, code='000001')
        baker.make(StockType, sunat_code='01')
        contenido = '000001,PRODUCTO UNO,UNIDAD X,12.50,01\n000001,PRODUCTO DOS,UNIDAD X,3.00,99\n'
        file = SimpleUploadedFile('productos.csv', contenido.encode('utf8'), content_type='text/csv')

        respuesta = self.client.post('/productos/product_import/', {'file': file})

        self.assertEqual(respuesta.status_code, 302)
        self.assertEqual(list(Product.objects.values_list('description', flat=True)), ['PRODUCTO UNO'])
        self.assertEqual(UnitOfMeasure.objects.get(code='UNIDA').description, 'UNIDAD X')


class BusquedaProductosTest(TestCase):
    """Los dos endpoints de busqueda leian `product.unit_of_measure.description`
    dentro del bucle: una consulta por resultado, en endpoints que el JavaScript
    llama en cada tecleo."""

    def setUp(self):
        self.client.force_login(User.objects.create_superuser('buscador', 'b@example.com', 'key-segura'))
        self.unit = baker.make(UnitOfMeasure, code='UND01', description='UNIDAD')
        baker.make(Product, code='COD0000001', description='PRODUCTO', unit_of_measure=self.unit)

    def extend(self, count):
        for number in range(count):
            baker.make(Product, description='PRODUCTO %s' % number, unit_of_measure=self.unit)

    def search(self, url, params):
        return self.client.get(url, params, HTTP_X_REQUESTED_WITH='XMLHttpRequest')

    def test_las_consultas_no_crecen_con_los_resultados(self):
        from django.db import connection
        from django.test.utils import CaptureQueriesContext

        url = '/productos/product_description_search/'
        params = {'description': 'PRODUCTO', 'search_type': 'TODOS'}
        with CaptureQueriesContext(connection) as un_resultado:
            self.search(url, params)

        self.extend(19)

        with CaptureQueriesContext(connection) as veinte_resultados:
            respuesta = self.search(url, params)

        self.assertEqual(len(un_resultado), len(veinte_resultados))
        data = respuesta.json()
        self.assertEqual(len(data), 20)
        self.assertEqual(data[0]['unit'], 'UNIDAD')

    def test_busqueda_por_code(self):
        respuesta = self.search('/productos/product_code_search/', {'code': 'COD0000001'})

        self.assertEqual(respuesta.status_code, 200)
        data = respuesta.json()
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]['unit'], 'UNIDAD')
