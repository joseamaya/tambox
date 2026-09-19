from django.test import TestCase, override_settings
from model_bakery import baker
from productos.models import UnidadMedida, GrupoProductos, Producto
from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse
from contabilidad.models import TipoExistencia
import tempfile

# Create your tests here.
"""class NewUnidadMedidaTestCase(TestCase):
    fixtures = ['usuarios.json','unidadesmedida.json']
    
    def test_index(self):
        resp = self.client.get("/")
        self.assertEqual(resp.status_code,200)
        
    def test_new_unidad_medida_view(self):
        self.client.login(username='test',password='test')
        resp = self.client.get('/productos/crear_unidad_medida/')
        self.assertEqual(200,resp.status_code)"""


class UnidadMedidaTest(TestCase):

    def setUp(self):
        self.um1 = baker.make(UnidadMedida)
        self.um2 = baker.make(UnidadMedida)
        self.um3 = baker.make(UnidadMedida)

    def test_creacion_unidad_medida(self):
        self.assertTrue(isinstance(self.um1, UnidadMedida))
        self.assertEqual(self.um1.__str__(), self.um1.descripcion)

    def test_siguiente_unidad_medida(self):
        self.assertEqual(self.um3.pk, self.um2.siguiente())

    def test_anterior_unidad_medida(self):
        self.assertEqual(self.um2.pk, self.um3.anterior())

    def test_primera_unidad_medida(self):
        self.assertEqual(self.um1.pk, self.um3.siguiente())

    def test_ultima_unidad_medida(self):
        self.assertEqual(self.um3.pk, self.um1.anterior())


class GrupoProductosTest(TestCase):

    def setUp(self):
        self.gp1 = baker.make(GrupoProductos, codigo='')
        self.gp2 = baker.make(GrupoProductos, codigo='')
        self.gp3 = baker.make(GrupoProductos, codigo='')

    def test_creacion_grupo_productos(self):
        self.assertTrue(isinstance(self.gp1, GrupoProductos))
        self.assertEqual("1".zfill(6), self.gp1.codigo)
        self.assertEqual(self.gp1.__str__(), self.gp1.descripcion)

    def test_siguiente_grupo_productos(self):
        self.assertEqual(self.gp2.pk, self.gp1.siguiente())
        self.assertEqual(self.gp3.pk, self.gp2.siguiente())

    def test_anterior_grupo_productos(self):
        self.assertEqual(self.gp1.pk, self.gp2.anterior())
        self.assertEqual(self.gp2.pk, self.gp3.anterior())

    def test_primer_grupo_productos(self):
        self.assertEqual(self.gp1.pk, self.gp3.siguiente())

    def test_ultimo_grupo_productos(self):
        self.assertEqual(self.gp3.pk, self.gp1.anterior())


class ProductoTest(TestCase):

    def setUp(self):
        self.gp1 = baker.make(GrupoProductos, codigo='')
        self.gp2 = baker.make(GrupoProductos, codigo='')
        self.p1 = baker.make(Producto, codigo='', grupo_productos=self.gp1)
        self.p2 = baker.make(Producto, codigo='', grupo_productos=self.gp1)
        self.p3 = baker.make(Producto, codigo='', grupo_productos=self.gp2, es_servicio=True)

    def test_creacion_producto(self):
        self.assertTrue(isinstance(self.p1, Producto))
        self.assertEqual(self.gp1.codigo + "1".zfill(4), self.p1.codigo)
        self.assertEqual(self.gp1.codigo + "2".zfill(4), self.p2.codigo)
        self.assertEqual(self.p1.__str__(), self.p1.descripcion)

    def test_siguiente_producto(self):
        self.assertEqual(self.p2.pk, self.p1.siguiente())
        self.assertEqual(self.p3.pk, self.p2.siguiente())

    def test_anterior_producto(self):
        self.assertEqual(self.p1.pk, self.p2.anterior())
        self.assertEqual(self.p2.pk, self.p3.anterior())

    def test_primer_producto(self):
        self.assertEqual(self.p1.pk, self.p3.siguiente())

    def test_ultimo_producto(self):
        self.assertEqual(self.p3.pk, self.p1.anterior())

    def test_creacion_servicio(self):
        self.assertEqual(self.p3.unidad_medida.codigo, 'SERV')


class ConsultaDeStockTest(TestCase):
    """Producto.stock recorria todos los almacenes con un .latest() cada uno, y
    las plantillas lo invocan varias veces en la misma pagina."""

    def test_una_sola_consulta_y_luego_cache(self):
        from almacen.models import Almacen
        baker.make(Almacen)
        baker.make(Almacen)
        producto = baker.make(Producto)

        with self.assertNumQueries(1):
            producto.stock

        with self.assertNumQueries(0):
            producto.stock

    def test_previsto_es_una_sola_consulta(self):
        producto = baker.make(Producto)

        with self.assertNumQueries(1):
            producto.previsto

        with self.assertNumQueries(0):
            producto.previsto


@override_settings(MEDIA_ROOT=tempfile.mkdtemp())
class CargarServiciosTest(TestCase):
    """`CargarServicios` devolvia dentro del bucle, asi que importaba solo la
    primera fila del CSV y el resto se perdia en silencio."""

    def setUp(self):
        self.client.force_login(User.objects.create_superuser('cargador', 'c@example.com', 'clave-segura'))

    def test_importa_todas_las_filas(self):
        baker.make(GrupoProductos, codigo='000001')
        contenido = '000001,SERVICIO UNO\n000001,SERVICIO DOS\n'
        archivo = SimpleUploadedFile('servicios.csv', contenido.encode('utf8'), content_type='text/csv')

        respuesta = self.client.post('/productos/cargar_servicios/', {'archivo': archivo})

        self.assertEqual(respuesta.status_code, 302)
        self.assertEqual(sorted(Producto.objects.values_list('descripcion', flat=True)),
                         ['SERVICIO DOS', 'SERVICIO UNO'])

    def test_sin_grupo_manda_a_crearlos(self):
        contenido = 'G99,SERVICIO UNO\n'
        archivo = SimpleUploadedFile('servicios.csv', contenido.encode('utf8'), content_type='text/csv')

        respuesta = self.client.post('/productos/cargar_servicios/', {'archivo': archivo})

        self.assertEqual(respuesta.status_code, 302)
        self.assertEqual(respuesta.url, reverse('productos:crear_grupo_productos'))
        self.assertEqual(Producto.objects.count(), 0)


@override_settings(MEDIA_ROOT=tempfile.mkdtemp())
class CargarProductosTest(TestCase):
    def setUp(self):
        self.client.force_login(User.objects.create_superuser('cargador', 'c@example.com', 'clave-segura'))

    def test_salta_la_fila_sin_tipo_de_existencia(self):
        baker.make(GrupoProductos, codigo='000001')
        baker.make(TipoExistencia, codigo_sunat='01')
        contenido = '000001,PRODUCTO UNO,UNIDAD X,12.50,01\n000001,PRODUCTO DOS,UNIDAD X,3.00,99\n'
        archivo = SimpleUploadedFile('productos.csv', contenido.encode('utf8'), content_type='text/csv')

        respuesta = self.client.post('/productos/cargar_productos/', {'archivo': archivo})

        self.assertEqual(respuesta.status_code, 302)
        self.assertEqual(list(Producto.objects.values_list('descripcion', flat=True)), ['PRODUCTO UNO'])
        self.assertEqual(UnidadMedida.objects.get(codigo='UNIDA').descripcion, 'UNIDAD X')
