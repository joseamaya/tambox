from almacen.models import Warehouse, MovementType, Order, OrderDetail, \
    Movement, MovementDetail, Kardex
from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from model_bakery import baker
from datetime import date, datetime
from decimal import Decimal
import tempfile
from django.utils import timezone
from compras.models import PurchaseOrder
from contabilidad.models import DocumentType
from productos.models import Product, UnitOfMeasure


class AlmacenTest(TestCase):

    def setUp(self):
        self.a1 = baker.make(Warehouse)
        self.a2 = baker.make(Warehouse)
        self.a3 = baker.make(Warehouse)

    def test_creacion_profesion_mommy(self):
        self.assertTrue(isinstance(self.a1, Warehouse))
        self.assertEqual(self.a1.__str__(), self.a1.description)

    def test_siguiente_almacen(self):
        self.assertEqual(self.a3.pk, self.a2.siguiente())

    def test_anterior_almacen(self):
        self.assertEqual(self.a2.pk, self.a3.anterior())

    def test_primer_almacen(self):
        self.assertEqual(self.a1.pk, self.a3.siguiente())

    def test_ultimo_almacen(self):
        self.assertEqual(self.a3.pk, self.a1.anterior())


class TipoMovimientoTest(TestCase):

    def setUp(self):
        self.tm1 = baker.make(MovementType, code='')
        self.tm2 = baker.make(MovementType, code='')
        self.tm3 = baker.make(MovementType, code='')

    def test_creacion_tipo_movimiento_mommy(self):
        self.assertTrue(isinstance(self.tm1, MovementType))
        self.assertEqual(self.tm1.__str__(), self.tm1.description)

    def test_siguiente_tipo_movimiento(self):
        self.assertEqual(self.tm3.pk, self.tm2.siguiente())

    def test_anterior_tipo_movimiento(self):
        self.assertEqual(self.tm2.pk, self.tm3.anterior())

    def test_primer_tipo_movimiento(self):
        self.assertEqual(self.tm1.pk, self.tm3.siguiente())

    def test_ultimo_tipo_movimiento(self):
        self.assertEqual(self.tm3.pk, self.tm1.anterior())

    def test_tipo_movimiento_ingreso(self):
        tm1 = baker.make(MovementType, code='', increases=True)
        self.assertEqual("I", tm1.code[0])


class PedidoTest(TestCase):

    def setUp(self):
        self.fecha_actual = date.today()
        self.fecha_proxima = date(2017, 1, 1)
        self.pe1 = baker.make(Order, code='', date=self.fecha_actual)
        self.pe2 = baker.make(Order, code='', date=self.fecha_actual)
        self.pe3 = baker.make(Order, code='', date=self.fecha_actual)
        self.pe4 = baker.make(Order, code='', date=self.fecha_proxima)

    def test_creacion_pedido_mommy(self):
        self.assertTrue(isinstance(self.pe1, Order))
        self.assertEqual(self.pe1.__str__(), self.pe1.code)
        self.assertEqual("PE" + str(self.pe1.date.year) + "000001", self.pe1.code)
        self.assertEqual("PE" + str(self.pe2.date.year) + "000002", self.pe2.code)
        self.assertEqual("PE" + str(self.pe4.date.year) + "000001", self.pe4.code)

    def test_actualizacion_pedido(self):
        """`Order.save()` solo genera el code cuando esta vacio, asi que
        guardar un pedido existente no lo duplica ni le cambia el code."""
        code = self.pe1.code
        quantity = Order.objects.count()

        self.pe1.save()

        self.assertEqual(code, Order.objects.get(pk=self.pe1.pk).code)
        self.assertEqual(quantity, Order.objects.count())

    def test_siguiente_pedido(self):
        self.assertEqual(self.pe3.pk, self.pe2.siguiente())

    def test_anterior_pedido(self):
        self.assertEqual(self.pe2.pk, self.pe3.anterior())

    def test_primer_pedido(self):
        self.assertEqual(self.pe1.pk, self.pe4.siguiente())

    def test_ultimo_pedido(self):
        self.assertEqual(self.pe4.pk, self.pe1.anterior())


class DetallePedidoTest(TestCase):

    def setUp(self):
        self.fecha_actual = date.today()
        self.pe1 = baker.make(Order, code='', date=self.fecha_actual)
        self.dpe1 = baker.make(OrderDetail, order=self.pe1)

    def test_creacion_detalle_pedido(self):
        self.assertTrue(isinstance(self.dpe1, OrderDetail))
        self.assertEqual(self.dpe1.__str__(), self.dpe1.order.code + ' ' + str(self.dpe1.line_number))

    def test_cantidad_por_atender(self):
        resultado = self.dpe1.quantity - self.dpe1.served_quantity
        self.assertEqual(resultado, self.dpe1.cantidad_por_atender())


class MovimientoTest(TestCase):

    def test_creacion_movimiento(self):
        mov1 = baker.make(Movement, movement_id='', operation_date=timezone.now())
        self.assertTrue(isinstance(mov1, Movement))
        self.assertEqual(mov1.__str__(), mov1.movement_id)

    def test_creacion_movimiento_ingreso(self):
        movement_type = baker.make(MovementType, code='', increases=True)
        mov1 = baker.make(Movement, movement_id='', operation_date=timezone.now(), movement_type=movement_type)
        mov2 = baker.make(Movement, movement_id='', operation_date=timezone.now(), movement_type=movement_type)
        self.assertEqual("I" + str(mov1.operation_date.year) + str(1).zfill(7), mov1.movement_id)
        self.assertEqual("I" + str(mov2.operation_date.year) + str(2).zfill(7), mov2.movement_id)

    def test_creacion_movimiento_salida(self):
        movement_type = baker.make(MovementType, code='', increases=False)
        mov1 = baker.make(Movement, movement_id='', operation_date=timezone.now(), movement_type=movement_type)
        mov2 = baker.make(Movement, movement_id='', operation_date=timezone.now(), movement_type=movement_type)
        self.assertEqual("S" + str(mov1.operation_date.year) + str(1).zfill(7), mov1.movement_id)
        self.assertEqual("S" + str(mov2.operation_date.year) + str(2).zfill(7), mov2.movement_id)

    def test_siguiente_movimiento(self):
        movement_type = baker.make(MovementType, code='', increases=True)
        mov1 = baker.make(Movement, movement_id='', operation_date=timezone.now(), movement_type=movement_type)
        mov2 = baker.make(Movement, movement_id='', operation_date=timezone.now(), movement_type=movement_type)
        mov3 = baker.make(Movement, movement_id='', operation_date=timezone.now(), movement_type=movement_type)
        self.assertEqual(mov2.pk, mov1.siguiente())
        self.assertEqual(mov3.pk, mov2.siguiente())

    def test_anterior_movimiento(self):
        movement_type = baker.make(MovementType, code='', increases=False)
        mov1 = baker.make(Movement, movement_id='', operation_date=timezone.now(), movement_type=movement_type)
        mov2 = baker.make(Movement, movement_id='', operation_date=timezone.now(), movement_type=movement_type)
        mov3 = baker.make(Movement, movement_id='', operation_date=timezone.now(), movement_type=movement_type)
        self.assertEqual(mov1.pk, mov2.anterior())
        self.assertEqual(mov2.pk, mov3.anterior())

    def test_primer_movimiento(self):
        movement_type = baker.make(MovementType, code='', increases=True)
        mov1 = baker.make(Movement, movement_id='', operation_date=timezone.now(), movement_type=movement_type)
        mov2 = baker.make(Movement, movement_id='', operation_date=timezone.now(), movement_type=movement_type)
        self.assertEqual(mov1.pk, mov2.siguiente())

    def test_ultimo_movimiento(self):
        movement_type = baker.make(MovementType, code='', increases=False)
        mov1 = baker.make(Movement, movement_id='', operation_date=timezone.now(), movement_type=movement_type)
        mov2 = baker.make(Movement, movement_id='', operation_date=timezone.now(), movement_type=movement_type)
        self.assertEqual(mov2.pk, mov1.anterior())

    def test_eliminar_referencia(self):
        """Devuelve la orden referenciada a su estado segun lo que queda
        ingresado. Un refactor anterior renombro el metodo a
        `eliminar_referencia` y este test quedo apuntando al nombre viejo."""
        movement_type = baker.make(MovementType, code='', increases=True, requires_reference=True)
        reference = baker.make(PurchaseOrder, quotation=None)
        mov1 = baker.make(Movement, movement_id='', operation_date=timezone.now(), movement_type=movement_type,
                          reference=reference)

        mov1.eliminar_referencia()

        self.assertEqual(mov1.reference.status, PurchaseOrder.STATUS.PEND)


class ReporteInventarioTest(TestCase):
    """Ejecuta el armado del libro de Excel. `manage.py check` no ejecuta
    cuerpos de funcion, asi que sin esto un nombre sin importar en la funcion
    solo se descubriria al pedir el reporte."""

    def test_genera_el_libro(self):
        from almacen.reports import reporte_inventario

        libro = reporte_inventario(date.today())

        self.assertIsNotNone(libro.active)
        self.assertEqual(libro.active['A3'].value, 'CTA CONTABLE')

    def test_incluye_una_fila_por_producto(self):
        from almacen.reports import reporte_inventario
        from contabilidad.models import Account, StockType
        from productos.models import ProductGroup, Product, UnitOfMeasure

        account_number = baker.make(Account)
        grupo = baker.make(ProductGroup, code='GR0001', description='GRUPO UNO',
                           account=account_number, contains_products=True)
        unidad = baker.make(UnitOfMeasure, code='UND01')
        baker.make(Product, code='GR00010001', description='PRODUCTO UNO',
                   product_group=grupo, unit_of_measure=unidad,
                   stock_type=baker.make(StockType))

        libro = reporte_inventario(date.today())
        codigos = [celda.value for celda in libro.active['B']]

        self.assertIn('GR00010001', codigos)

    def test_las_consultas_no_crecen_con_los_productos(self):
        """El reporte resolvia el ultimo Kardex y la cuenta contable del grupo con
        una consulta por producto, y ademas un `count()` por grupo."""
        from almacen.reports import reporte_inventario
        from django.db import connection
        from django.test.utils import CaptureQueriesContext
        from contabilidad.models import Account, StockType
        from productos.models import ProductGroup, Product

        grupo = baker.make(ProductGroup, code='000001', account=baker.make(Account))
        unidad = baker.make(UnitOfMeasure)
        stock_type = baker.make(StockType)
        campos = {'product_group': grupo, 'unit_of_measure': unidad,
                  'stock_type': stock_type}
        baker.make(Product, code='', **campos)

        with CaptureQueriesContext(connection) as con_un_producto:
            reporte_inventario(date.today())

        for number in range(9):
            baker.make(Product, code='', **campos)

        with CaptureQueriesContext(connection) as con_diez:
            reporte_inventario(date.today())

        self.assertEqual(len(con_un_producto), len(con_diez))


class EstadoDeDetallePedidoTest(TestCase):
    """Solo lee campos de la instancia, y fija la regla compartida de clasificar()."""

    def test_atendido(self):
        self.assertEqual(OrderDetail(quantity=10, served_quantity=0).establecer_estado_atendido(),
                         OrderDetail.STATUS.PEND)
        self.assertEqual(OrderDetail(quantity=10, served_quantity=4).establecer_estado_atendido(),
                         OrderDetail.STATUS.ATEN_PARC)
        self.assertEqual(OrderDetail(quantity=10, served_quantity=10).establecer_estado_atendido(),
                         OrderDetail.STATUS.ATEN)
        self.assertEqual(OrderDetail(quantity=10, served_quantity=12).establecer_estado_atendido(),
                         OrderDetail.STATUS.ATEN)


@override_settings(MEDIA_ROOT=tempfile.mkdtemp())
class CargarCsvTest(TestCase):
    """Ejercita de punta a punta el lector de CSV y el mixin compartido, que es
    lo unico que garantiza que el refactor de los importadores funcione."""

    def setUp(self):
        self.client.force_login(User.objects.create_superuser('cargador', 'c@example.com', 'clave-segura'))

    def test_cargar_almacenes(self):
        contenido = 'AL01,ALMACEN UNO\nAL02,ALMACEN DOS\n'
        file = SimpleUploadedFile('almacenes.csv', contenido.encode('utf8'), content_type='text/csv')

        respuesta = self.client.post('/almacen/cargar_almacenes/', {'file': file})

        self.assertEqual(respuesta.status_code, 302)
        self.assertEqual(Warehouse.objects.filter(code__in=['AL01', 'AL02']).count(), 2)
        self.assertEqual(Warehouse.objects.get(code='AL01').description, 'ALMACEN UNO')

    def test_cargar_inventario_inicial(self):
        movement_type = baker.make(MovementType, code='I00', increases=True)
        baker.make(DocumentType, sunat_code='PEC')
        warehouse = baker.make(Warehouse)
        producto_uno = baker.make(Product, description='PRODUCTO UNO')
        producto_dos = baker.make(Product, description='PRODUCTO DOS')
        contenido = 'PRODUCTO UNO,10,5.0,\nPRODUCTO DOS,2,3.5,7.0\n'
        file = SimpleUploadedFile('inventario.csv', contenido.encode('utf8'), content_type='text/csv')

        respuesta = self.client.post('/almacen/cargar_inventario_inicial/',
                                     {'file': file,
                                      'date': '01/01/2024',
                                      'hora': '08:30',
                                      'almacenes': warehouse.pk})

        self.assertEqual(respuesta.status_code, 302)
        movement = Movement.objects.get()
        self.assertEqual(movement.movement_type, movement_type)
        detalles = list(MovementDetail.objects.order_by('line_number'))
        self.assertEqual([detalle.line_number for detalle in detalles], [1, 2])
        self.assertEqual([detalle.product for detalle in detalles], [producto_uno, producto_dos])
        self.assertEqual([detalle.quantity for detalle in detalles], [Decimal('10'), Decimal('2')])
        self.assertEqual(detalles[0].amount, Decimal('50'))
        self.assertEqual(detalles[1].amount, Decimal('7'))

    def test_cargar_inventario_inicial_sin_datos_basicos_avisa(self):
        """`I00` y `PEC` los crean los tableros de Warehouse y Contabilidad. Si el
        usuario no paso por ellos, antes salia un DoesNotExist y ahora la pagina
        dice que falta y donde crearlo."""
        warehouse = baker.make(Warehouse)
        contenido = 'PRODUCTO UNO,10,5.0,50.0\n'
        file = SimpleUploadedFile('inventario.csv', contenido.encode('utf8'), content_type='text/csv')

        respuesta = self.client.post('/almacen/cargar_inventario_inicial/',
                                     {'file': file,
                                      'date': '01/01/2024',
                                      'hora': '08:30',
                                      'almacenes': warehouse.pk})

        self.assertEqual(respuesta.status_code, 200)
        self.assertContains(respuesta, 'Falta el tipo de movimiento')
        self.assertContains(respuesta, 'Falta el tipo de documento')
        self.assertEqual(Movement.objects.count(), 0)
        self.assertEqual(MovementDetail.objects.count(), 0)


class TotalDeMovimientoTest(TestCase):
    """Suma la columna `amount`, asi que el agregado es exacto y ademas se memoriza."""

    def test_se_calcula_una_sola_vez(self):
        movement = baker.make(Movement)

        with self.assertNumQueries(1):
            movement.total

        with self.assertNumQueries(0):
            movement.total


class UltimosPorProductoTest(TestCase):
    """Las vistas de stock resolvian el ultimo Kardex con un `latest()` por
    product: una consulta por fila y MultipleObjectsReturned si dos movimientos
    compartian date."""

    def setUp(self):
        self.warehouse = baker.make(Warehouse)
        self.productos = [baker.make(Product) for _ in range(3)]
        for product in self.productos:
            baker.make(Kardex, warehouse=self.warehouse, product=product,
                       operation_date=timezone.make_aware(datetime(2024, 1, 10, 9, 0)))

    def test_una_consulta_para_todo_el_lote(self):
        with self.assertNumQueries(1):
            ultimos = Kardex.ultimos_por_producto(self.productos, warehouse=self.warehouse)

        self.assertEqual(len(ultimos), 3)

    def test_el_producto_viene_cargado(self):
        """El `select_related` es lo que evita una consulta por fila al leer
        `kardex.product.description` en los bucles."""
        ultimos = Kardex.ultimos_por_producto(self.productos, warehouse=self.warehouse)

        with self.assertNumQueries(0):
            for kardex in ultimos.values():
                kardex.product.code
                kardex.product.unit_of_measure

    def test_desempata_por_pk(self):
        product = self.productos[0]
        primero = Kardex.objects.get(product=product)
        segundo = baker.make(Kardex, warehouse=self.warehouse, product=product,
                             operation_date=primero.operation_date)

        ultimos = Kardex.ultimos_por_producto([product], warehouse=self.warehouse)

        self.assertEqual(ultimos[product.pk].pk, segundo.pk)


class ReporteKardexConsolidadoTest(TestCase):
    """Ejecuta las dos tablas consolidadas del kardex, donde el saldo inicial de
    cada producto se resolvia con un `latest()` dentro del bucle. `manage.py
    check` no ejecuta cuerpos de funcion, asi que sin esto un nombre roto dentro
    de esas tablas solo se descubriria al pedir el PDF."""

    def setUp(self):
        from contabilidad.models import Account
        from productos.models import ProductGroup

        self.warehouse = baker.make(Warehouse)
        self.grupo = baker.make(ProductGroup, code='000001',
                                account=baker.make(Account), contains_products=True)
        self.productos = [baker.make(Product, code='', product_group=self.grupo)
                          for number in range(3)]

    def reporte(self):
        from almacen.reports import KardexPdfReport
        from productos.models import ProductGroup
        return KardexPdfReport('A4', date(2024, 1, 1), date(2024, 1, 31),
                                self.warehouse, ProductGroup.objects.all())

    def test_tabla_consolidada_de_productos(self):
        tabla = self.reporte().tabla_detalle_consolidado_productos(Product.objects.all())

        filas = tabla._cellvalues
        self.assertEqual(len(filas), 3 + len(self.productos))
        self.assertIn(self.productos[0].code, filas[2])

    def test_tabla_consolidada_de_grupos(self):
        from productos.models import ProductGroup

        tabla = self.reporte().tabla_detalle_consolidado_grupo(ProductGroup.objects.all())

        self.assertEqual(len(tabla._cellvalues), 3 + 1)


class ReporteKardexExcelTest(TestCase):
    """Los consolidados del kardex en Excel resolvian el saldo inicial con un
    `latest()` por producto. El test fija la semantica -el ultimo kardex
    *anterior* al periodo, no el ultimo a secas- porque en estos informes el
    numero de consultas igual crece con el catalogo: cada fila llama ademas a
    `obtener_kardex()`."""

    def setUp(self):
        from contabilidad.models import Account, StockType
        from productos.models import ProductGroup

        self.warehouse = baker.make(Warehouse)
        self.grupo = baker.make(ProductGroup, code='000001',
                                account=baker.make(Account))
        self.unidad = baker.make(UnitOfMeasure)
        self.stock_type = baker.make(StockType)
        self.document_type = baker.make(DocumentType, sunat_code='PEC')
        self.movement_type = baker.make(MovementType, code='I01', sunat_code='01')
        self.product = baker.make(Product, code='', product_group=self.grupo,
                                   unit_of_measure=self.unidad,
                                   stock_type=self.stock_type)
        self.desde = date(2024, 1, 1)
        self.hasta = date(2024, 1, 31)
        baker.make(Kardex, warehouse=self.warehouse, product=self.product,
                   operation_date=timezone.make_aware(datetime(2023, 12, 31, 9, 0)),
                   total_quantity=Decimal('7'), total_amount=Decimal('21'))

    def test_el_formato_sunat_no_crece_con_el_catalogo(self):
        """Era 4 consultas por producto: dos `select_related`, el saldo inicial y
        el `obtener_kardex()` del periodo. Ahora el lote se resuelve de una vez."""
        from django.db import connection
        from django.test.utils import CaptureQueriesContext
        from almacen.reports import KardexExcelReport

        reporte = KardexExcelReport()
        reporte.obtener_formato_sunat_unidades_fisicas_todos(self.desde, self.hasta, self.warehouse)
        with CaptureQueriesContext(connection) as con_uno:
            reporte.obtener_formato_sunat_unidades_fisicas_todos(self.desde, self.hasta, self.warehouse)

        for number in range(9):
            product = baker.make(Product, code='', product_group=self.grupo,
                                  unit_of_measure=self.unidad,
                                  stock_type=self.stock_type)
            baker.make(Kardex, warehouse=self.warehouse, product=product,
                       movement=baker.make(Movement, document_type=self.document_type,
                                             movement_type=self.movement_type),
                       operation_date=timezone.make_aware(datetime(2024, 1, 10, 9, 0)),
                       total_quantity=Decimal('5'), total_amount=Decimal('10'))

        with CaptureQueriesContext(connection) as con_diez:
            libro = reporte.obtener_formato_sunat_unidades_fisicas_todos(
                self.desde, self.hasta, self.warehouse)

        self.assertLessEqual(len(con_diez), len(con_uno))
        self.assertLess(len(con_diez), 20)
        self.assertEqual(len(libro.sheetnames) - 1, 10)

    def test_el_consolidado_usa_el_kardex_anterior_al_periodo(self):
        from almacen.reports import KardexExcelReport

        baker.make(Kardex, warehouse=self.warehouse, product=self.product,
                   operation_date=timezone.make_aware(datetime(2024, 6, 30, 9, 0)),
                   total_quantity=Decimal('99'), total_amount=Decimal('99'))

        libro = KardexExcelReport().obtener_consolidado_productos(
            self.desde, self.hasta, self.warehouse)

        hoja = libro.active
        self.assertEqual(hoja.cell(row=4, column=4).value, Decimal('7'))
        self.assertEqual(hoja.cell(row=4, column=5).value, Decimal('21'))

    def test_el_formato_normal_se_genera(self):
        from almacen.reports import KardexExcelReport

        libro = KardexExcelReport().obtener_formato_normal_todos(
            self.desde, self.hasta, self.warehouse)

        hoja = libro.active
        self.assertEqual(hoja.cell(row=5, column=8).value, 'SALDO INICIAL:')


class ReporteKardexPorProductoTest(TestCase):
    """Los informes de kardex por producto resolvian el saldo inicial con un
    `latest()` por fila. `kardex_inicial_de()` lee el lote que el report
    precargo, y si el informe exporta un solo producto consulta ese producto:
    los dos caminos se ejercitan aqui, porque `manage.py check` no ejecuta
    cuerpos de funcion."""

    def setUp(self):
        from contabilidad.models import Account, StockType
        from productos.models import ProductGroup

        self.warehouse = baker.make(Warehouse)
        self.grupo = baker.make(ProductGroup, code='000001',
                                account=baker.make(Account))
        self.product = baker.make(Product, code='', product_group=self.grupo,
                                   stock_type=baker.make(StockType))
        self.desde = date(2024, 1, 1)
        self.hasta = date(2024, 1, 31)
        baker.make(Kardex, warehouse=self.warehouse, product=self.product,
                   operation_date=timezone.make_aware(datetime(2023, 12, 31, 9, 0)),
                   total_quantity=Decimal('7'), total_amount=Decimal('21'),
                   total_price=Decimal('3'))

    def test_las_tablas_del_pdf_usan_el_kardex_anterior(self):
        from almacen.reports import KardexPdfReport
        from productos.models import ProductGroup

        reporte = KardexPdfReport('A4', self.desde, self.hasta, self.warehouse,
                                   ProductGroup.objects.all())

        unidades = reporte.tabla_detalle_unidades_fisicas(
            self.product, self.desde, self.hasta, self.warehouse)
        self.assertEqual(unidades._cellvalues[2][7], '7.00')

        valorizado = reporte.tabla_detalle_valorizado(
            self.product, self.desde, self.hasta, self.warehouse)
        self.assertTrue(valorizado._cellvalues)

    def test_los_todos_precargan_el_lote(self):
        from almacen.reports import KardexExcelReport

        reporte = KardexExcelReport()
        libro = reporte.obtener_formato_sunat_unidades_fisicas_todos(
            self.desde, self.hasta, self.warehouse)

        self.assertTrue(libro.sheetnames)
        self.assertIn(self.product.pk, reporte.kardex_iniciales)

    def test_los_todos_valorizados_precargan_el_lote(self):
        from almacen.reports import KardexExcelReport

        reporte = KardexExcelReport()
        libro = reporte.obtener_formato_sunat_valorizado_todos(
            self.desde, self.hasta, self.warehouse)

        self.assertTrue(libro.sheetnames)
        self.assertIn(self.product.pk, reporte.kardex_iniciales)

    def test_los_formatos_de_un_solo_producto(self):
        from almacen.reports import KardexExcelReport

        reporte = KardexExcelReport()
        for metodo in ('obtener_formato_sunat_unidades_fisicas_producto',
                       'obtener_formato_sunat_valorizado_producto',
                       'obtener_formato_normal_producto'):
            with self.subTest(metodo=metodo):
                libro = getattr(reporte, metodo)(self.product, self.desde,
                                                 self.hasta, self.warehouse)
                self.assertTrue(libro.sheetnames)


class StockAjaxTest(TestCase):
    """Los endpoints de autocompletado resolvian el ultimo Kardex uno por uno.
    Esto fija el JSON que devuelven, que es lo que consume el JavaScript."""

    def setUp(self):
        self.client.force_login(User.objects.create_superuser('buscador', 'b@example.com', 'clave-segura'))
        self.warehouse = baker.make(Warehouse)
        self.product = baker.make(Product, description='ACERO INOXIDABLE',
                                   unit_of_measure=baker.make(UnitOfMeasure))
        self.unidad = self.product.unit_of_measure
        baker.make(Kardex, warehouse=self.warehouse, product=self.product,
                   operation_date=timezone.make_aware(datetime(2024, 1, 10, 9, 0)),
                   total_quantity=Decimal('7'), total_amount=Decimal('21'), total_price=Decimal('3'))

    def obtener(self, url):
        return self.client.get(url, {'description': 'ACERO', 'warehouse': self.warehouse.pk},
                               HTTP_X_REQUESTED_WITH='XMLHttpRequest')

    def test_listado_stock_producto(self):
        respuesta = self.obtener('/almacen/listado_stock_producto/')

        self.assertEqual(respuesta.status_code, 200)
        datos = respuesta.json()
        self.assertEqual(len(datos), 1)
        self.assertEqual(datos[0]['code'], self.product.code)
        self.assertEqual(datos[0]['label'], 'ACERO INOXIDABLE')
        self.assertEqual(datos[0]['unidad'], self.unidad.code)
        self.assertAlmostEqual(datos[0]['stock'], 7)

    def test_busqueda_productos_almacen(self):
        respuesta = self.obtener('/almacen/busqueda_productos_almacen/')

        self.assertEqual(respuesta.status_code, 200)
        datos = respuesta.json()
        self.assertEqual(len(datos), 1)
        self.assertEqual(datos[0]['code'], self.product.code)
        self.assertEqual(datos[0]['unidad'], self.unidad.description)
        self.assertEqual(Decimal(datos[0]['price']), Decimal('3'))
