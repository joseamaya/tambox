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

    def test_creation_profession_baker(self):
        self.assertTrue(isinstance(self.a1, Warehouse))
        self.assertEqual(self.a1.__str__(), self.a1.description)

    def test_next_warehouse(self):
        self.assertEqual(self.a3.pk, self.a2.next())

    def test_previous_warehouse(self):
        self.assertEqual(self.a2.pk, self.a3.previous())

    def test_first_warehouse(self):
        self.assertEqual(self.a1.pk, self.a3.next())

    def test_last_warehouse(self):
        self.assertEqual(self.a3.pk, self.a1.previous())


class TipoMovimientoTest(TestCase):

    def setUp(self):
        self.tm1 = baker.make(MovementType, code='')
        self.tm2 = baker.make(MovementType, code='')
        self.tm3 = baker.make(MovementType, code='')

    def test_creation_type_movement_baker(self):
        self.assertTrue(isinstance(self.tm1, MovementType))
        self.assertEqual(self.tm1.__str__(), self.tm1.description)

    def test_next_type_movement(self):
        self.assertEqual(self.tm3.pk, self.tm2.next())

    def test_previous_type_movement(self):
        self.assertEqual(self.tm2.pk, self.tm3.previous())

    def test_first_type_movement(self):
        self.assertEqual(self.tm1.pk, self.tm3.next())

    def test_last_type_movement(self):
        self.assertEqual(self.tm3.pk, self.tm1.previous())

    def test_type_movement_inbound(self):
        tm1 = baker.make(MovementType, code='', increases=True)
        self.assertEqual("I", tm1.code[0])


class PedidoTest(TestCase):

    def setUp(self):
        self.current_date = date.today()
        self.next_date = date(2017, 1, 1)
        self.pe1 = baker.make(Order, code='', date=self.current_date)
        self.pe2 = baker.make(Order, code='', date=self.current_date)
        self.pe3 = baker.make(Order, code='', date=self.current_date)
        self.pe4 = baker.make(Order, code='', date=self.next_date)

    def test_creation_order_baker(self):
        self.assertTrue(isinstance(self.pe1, Order))
        self.assertEqual(self.pe1.__str__(), self.pe1.code)
        self.assertEqual("PE" + str(self.pe1.date.year) + "000001", self.pe1.code)
        self.assertEqual("PE" + str(self.pe2.date.year) + "000002", self.pe2.code)
        self.assertEqual("PE" + str(self.pe4.date.year) + "000001", self.pe4.code)

    def test_update_order(self):
        """`Order.save()` solo genera el code cuando esta vacio, asi que
        guardar un pedido existente no lo duplica ni le cambia el code."""
        code = self.pe1.code
        quantity = Order.objects.count()

        self.pe1.save()

        self.assertEqual(code, Order.objects.get(pk=self.pe1.pk).code)
        self.assertEqual(quantity, Order.objects.count())

    def test_next_order(self):
        self.assertEqual(self.pe3.pk, self.pe2.next())

    def test_previous_order(self):
        self.assertEqual(self.pe2.pk, self.pe3.previous())

    def test_first_order(self):
        self.assertEqual(self.pe1.pk, self.pe4.next())

    def test_last_order(self):
        self.assertEqual(self.pe4.pk, self.pe1.previous())


class DetallePedidoTest(TestCase):

    def setUp(self):
        self.current_date = date.today()
        self.pe1 = baker.make(Order, code='', date=self.current_date)
        self.dpe1 = baker.make(OrderDetail, order=self.pe1)

    def test_creation_detail_order(self):
        self.assertTrue(isinstance(self.dpe1, OrderDetail))
        self.assertEqual(self.dpe1.__str__(), self.dpe1.order.code + ' ' + str(self.dpe1.line_number))

    def test_cantidad_by_serve(self):
        resultado = self.dpe1.quantity - self.dpe1.served_quantity
        self.assertEqual(resultado, self.dpe1.quantity_to_serve())


class MovimientoTest(TestCase):

    def test_creation_movement(self):
        mov1 = baker.make(Movement, movement_id='', operation_date=timezone.now())
        self.assertTrue(isinstance(mov1, Movement))
        self.assertEqual(mov1.__str__(), mov1.movement_id)

    def test_creation_movement_inbound(self):
        movement_type = baker.make(MovementType, code='', increases=True)
        mov1 = baker.make(Movement, movement_id='', operation_date=timezone.now(), movement_type=movement_type)
        mov2 = baker.make(Movement, movement_id='', operation_date=timezone.now(), movement_type=movement_type)
        self.assertEqual("I" + str(mov1.operation_date.year) + str(1).zfill(7), mov1.movement_id)
        self.assertEqual("I" + str(mov2.operation_date.year) + str(2).zfill(7), mov2.movement_id)

    def test_creation_movement_outbound(self):
        movement_type = baker.make(MovementType, code='', increases=False)
        mov1 = baker.make(Movement, movement_id='', operation_date=timezone.now(), movement_type=movement_type)
        mov2 = baker.make(Movement, movement_id='', operation_date=timezone.now(), movement_type=movement_type)
        self.assertEqual("S" + str(mov1.operation_date.year) + str(1).zfill(7), mov1.movement_id)
        self.assertEqual("S" + str(mov2.operation_date.year) + str(2).zfill(7), mov2.movement_id)

    def test_next_movement(self):
        movement_type = baker.make(MovementType, code='', increases=True)
        mov1 = baker.make(Movement, movement_id='', operation_date=timezone.now(), movement_type=movement_type)
        mov2 = baker.make(Movement, movement_id='', operation_date=timezone.now(), movement_type=movement_type)
        mov3 = baker.make(Movement, movement_id='', operation_date=timezone.now(), movement_type=movement_type)
        self.assertEqual(mov2.pk, mov1.next())
        self.assertEqual(mov3.pk, mov2.next())

    def test_previous_movement(self):
        movement_type = baker.make(MovementType, code='', increases=False)
        mov1 = baker.make(Movement, movement_id='', operation_date=timezone.now(), movement_type=movement_type)
        mov2 = baker.make(Movement, movement_id='', operation_date=timezone.now(), movement_type=movement_type)
        mov3 = baker.make(Movement, movement_id='', operation_date=timezone.now(), movement_type=movement_type)
        self.assertEqual(mov1.pk, mov2.previous())
        self.assertEqual(mov2.pk, mov3.previous())

    def test_first_movement(self):
        movement_type = baker.make(MovementType, code='', increases=True)
        mov1 = baker.make(Movement, movement_id='', operation_date=timezone.now(), movement_type=movement_type)
        mov2 = baker.make(Movement, movement_id='', operation_date=timezone.now(), movement_type=movement_type)
        self.assertEqual(mov1.pk, mov2.next())

    def test_last_movement(self):
        movement_type = baker.make(MovementType, code='', increases=False)
        mov1 = baker.make(Movement, movement_id='', operation_date=timezone.now(), movement_type=movement_type)
        mov2 = baker.make(Movement, movement_id='', operation_date=timezone.now(), movement_type=movement_type)
        self.assertEqual(mov2.pk, mov1.previous())

    def test_delete_reference(self):
        """Devuelve la orden referenciada a su estado segun lo que queda
        ingresado. Un refactor anterior renombro el metodo a
        `delete_reference` y este test quedo apuntando al nombre viejo."""
        movement_type = baker.make(MovementType, code='', increases=True, requires_reference=True)
        reference = baker.make(PurchaseOrder, quotation=None)
        mov1 = baker.make(Movement, movement_id='', operation_date=timezone.now(), movement_type=movement_type,
                          reference=reference)

        mov1.delete_reference()

        self.assertEqual(mov1.reference.status, PurchaseOrder.STATUS.PEND)


class ReporteInventarioTest(TestCase):
    """Ejecuta el armado del libro de Excel. `manage.py check` no ejecuta
    cuerpos de funcion, asi que sin esto un nombre sin importar en la funcion
    solo se descubriria al pedir el reporte."""

    def test_generates_book(self):
        from almacen.reports import inventory_report

        libro = inventory_report(date.today())

        self.assertIsNotNone(libro.active)
        self.assertEqual(libro.active['A3'].value, 'CTA CONTABLE')

    def test_includes_row_by_product(self):
        from almacen.reports import inventory_report
        from contabilidad.models import Account, StockType
        from productos.models import ProductGroup, Product, UnitOfMeasure

        account_number = baker.make(Account)
        group = baker.make(ProductGroup, code='GR0001', description='GRUPO UNO',
                           account=account_number, contains_products=True)
        unit = baker.make(UnitOfMeasure, code='UND01')
        baker.make(Product, code='GR00010001', description='PRODUCTO UNO',
                   product_group=group, unit_of_measure=unit,
                   stock_type=baker.make(StockType))

        libro = inventory_report(date.today())
        codes = [celda.value for celda in libro.active['B']]

        self.assertIn('GR00010001', codes)

    def test_queries_not_grow_with_products(self):
        """El reporte resolvia el ultimo Kardex y la cuenta contable del grupo con
        una consulta por producto, y ademas un `count()` por grupo."""
        from almacen.reports import inventory_report
        from django.db import connection
        from django.test.utils import CaptureQueriesContext
        from contabilidad.models import Account, StockType
        from productos.models import ProductGroup, Product

        group = baker.make(ProductGroup, code='000001', account=baker.make(Account))
        unit = baker.make(UnitOfMeasure)
        stock_type = baker.make(StockType)
        campos = {'product_group': group, 'unit_of_measure': unit,
                  'stock_type': stock_type}
        baker.make(Product, code='', **campos)

        with CaptureQueriesContext(connection) as with_one_product:
            inventory_report(date.today())

        for number in range(9):
            baker.make(Product, code='', **campos)

        with CaptureQueriesContext(connection) as con_diez:
            inventory_report(date.today())

        self.assertEqual(len(with_one_product), len(con_diez))


class EstadoDeDetallePedidoTest(TestCase):
    """Solo lee campos de la instance, y fija la regla compartida de classify()."""

    def test_served(self):
        self.assertEqual(OrderDetail(quantity=10, served_quantity=0).set_status_served(),
                         OrderDetail.STATUS.PEND)
        self.assertEqual(OrderDetail(quantity=10, served_quantity=4).set_status_served(),
                         OrderDetail.STATUS.ATEN_PARC)
        self.assertEqual(OrderDetail(quantity=10, served_quantity=10).set_status_served(),
                         OrderDetail.STATUS.ATEN)
        self.assertEqual(OrderDetail(quantity=10, served_quantity=12).set_status_served(),
                         OrderDetail.STATUS.ATEN)


@override_settings(MEDIA_ROOT=tempfile.mkdtemp())
class CargarCsvTest(TestCase):
    """Ejercita de punta a punta el lector de CSV y el mixin compartido, que es
    lo unico que garantiza que el refactor de los importadores funcione."""

    def setUp(self):
        self.client.force_login(User.objects.create_superuser('cargador', 'c@example.com', 'key-segura'))

    def test_import_warehouses(self):
        contenido = 'AL01,ALMACEN UNO\nAL02,ALMACEN DOS\n'
        file = SimpleUploadedFile('warehouses.csv', contenido.encode('utf8'), content_type='text/csv')

        respuesta = self.client.post('/almacen/warehouse_import/', {'file': file})

        self.assertEqual(respuesta.status_code, 302)
        self.assertEqual(Warehouse.objects.filter(code__in=['AL01', 'AL02']).count(), 2)
        self.assertEqual(Warehouse.objects.get(code='AL01').description, 'ALMACEN UNO')

    def test_import_inventory_initial(self):
        movement_type = baker.make(MovementType, code='I00', increases=True)
        baker.make(DocumentType, sunat_code='PEC')
        warehouse = baker.make(Warehouse)
        product_one = baker.make(Product, description='PRODUCTO UNO')
        product_two = baker.make(Product, description='PRODUCTO DOS')
        contenido = 'PRODUCTO UNO,10,5.0,\nPRODUCTO DOS,2,3.5,7.0\n'
        file = SimpleUploadedFile('inventario.csv', contenido.encode('utf8'), content_type='text/csv')

        respuesta = self.client.post('/almacen/initial_inventory_import/',
                                     {'file': file,
                                      'date': '01/01/2024',
                                      'time': '08:30',
                                      'warehouses': warehouse.pk})

        self.assertEqual(respuesta.status_code, 302)
        movement = Movement.objects.get()
        self.assertEqual(movement.movement_type, movement_type)
        details = list(MovementDetail.objects.order_by('line_number'))
        self.assertEqual([detail.line_number for detail in details], [1, 2])
        self.assertEqual([detail.product for detail in details], [product_one, product_two])
        self.assertEqual([detail.quantity for detail in details], [Decimal('10'), Decimal('2')])
        self.assertEqual(details[0].amount, Decimal('50'))
        self.assertEqual(details[1].amount, Decimal('7'))

    def test_import_inventory_initial_without_data_basic_warns(self):
        """`I00` y `PEC` los crean los tableros de Warehouse y Contabilidad. Si el
        usuario no paso por ellos, antes salia un DoesNotExist y ahora la pagina
        dice que falta y donde crearlo."""
        warehouse = baker.make(Warehouse)
        contenido = 'PRODUCTO UNO,10,5.0,50.0\n'
        file = SimpleUploadedFile('inventario.csv', contenido.encode('utf8'), content_type='text/csv')

        respuesta = self.client.post('/almacen/initial_inventory_import/',
                                     {'file': file,
                                      'date': '01/01/2024',
                                      'time': '08:30',
                                      'warehouses': warehouse.pk})

        self.assertEqual(respuesta.status_code, 200)
        self.assertContains(respuesta, 'Falta el tipo de movimiento')
        self.assertContains(respuesta, 'Falta el tipo de documento')
        self.assertEqual(Movement.objects.count(), 0)
        self.assertEqual(MovementDetail.objects.count(), 0)


class TotalDeMovimientoTest(TestCase):
    """Suma la columna `amount`, asi que el agregado es exacto y ademas se memoriza."""

    def test_calculates_only_time(self):
        movement = baker.make(Movement)

        with self.assertNumQueries(1):
            movement.total

        with self.assertNumQueries(0):
            movement.total


class UltimosPorProductoTest(TestCase):
    """Las vistas de stock resolvian el ultimo Kardex con un `latest()` por
    product: una consulta por fila y MultipleObjectsReturned si dos movements
    compartian date."""

    def setUp(self):
        self.warehouse = baker.make(Warehouse)
        self.productos = [baker.make(Product) for _ in range(3)]
        for product in self.productos:
            baker.make(Kardex, warehouse=self.warehouse, product=product,
                       operation_date=timezone.make_aware(datetime(2024, 1, 10, 9, 0)))

    def test_query_for_todo_batch(self):
        with self.assertNumQueries(1):
            last_records = Kardex.last_by_product(self.productos, warehouse=self.warehouse)

        self.assertEqual(len(last_records), 3)

    def test_product_viene_cargado(self):
        """El `select_related` es lo que evita una consulta por fila al leer
        `kardex.product.description` en los bucles."""
        last_records = Kardex.last_by_product(self.productos, warehouse=self.warehouse)

        with self.assertNumQueries(0):
            for kardex in last_records.values():
                kardex.product.code
                kardex.product.unit_of_measure

    def test_breaks_tie_by_pk(self):
        product = self.productos[0]
        primero = Kardex.objects.get(product=product)
        segundo = baker.make(Kardex, warehouse=self.warehouse, product=product,
                             operation_date=primero.operation_date)

        last_records = Kardex.last_by_product([product], warehouse=self.warehouse)

        self.assertEqual(last_records[product.pk].pk, segundo.pk)


class ReporteKardexConsolidadoTest(TestCase):
    """Ejecuta las dos tablas consolidadas del kardex, donde el saldo inicial de
    cada producto se resolvia con un `latest()` dentro del bucle. `manage.py
    check` no ejecuta cuerpos de funcion, asi que sin esto un nombre roto dentro
    de esas tablas solo se descubriria al pedir el PDF."""

    def setUp(self):
        from contabilidad.models import Account
        from productos.models import ProductGroup

        self.warehouse = baker.make(Warehouse)
        self.group = baker.make(ProductGroup, code='000001',
                                account=baker.make(Account), contains_products=True)
        self.productos = [baker.make(Product, code='', product_group=self.group)
                          for number in range(3)]

    def report(self):
        from almacen.reports import KardexPdfReport
        from productos.models import ProductGroup
        return KardexPdfReport('A4', date(2024, 1, 1), date(2024, 1, 31),
                                self.warehouse, ProductGroup.objects.all())

    def test_table_consolidated_products(self):
        table = self.report().consolidated_product_detail_table(Product.objects.all())

        rows = table._cellvalues
        self.assertEqual(len(rows), 3 + len(self.productos))
        self.assertIn(self.productos[0].code, rows[2])

    def test_table_consolidated_groups(self):
        from productos.models import ProductGroup

        table = self.report().consolidated_group_detail_table(ProductGroup.objects.all())

        self.assertEqual(len(table._cellvalues), 3 + 1)


class ReporteKardexExcelTest(TestCase):
    """Los consolidados del kardex en Excel resolvian el saldo inicial con un
    `latest()` por producto. El test fija la semantica -el ultimo kardex
    *anterior* al periodo, no el ultimo a secas- porque en estos informes el
    numero de consultas igual crece con el catalogo: cada fila llama ademas a
    `get_kardex()`."""

    def setUp(self):
        from contabilidad.models import Account, StockType
        from productos.models import ProductGroup

        self.warehouse = baker.make(Warehouse)
        self.group = baker.make(ProductGroup, code='000001',
                                account=baker.make(Account))
        self.unit = baker.make(UnitOfMeasure)
        self.stock_type = baker.make(StockType)
        self.document_type = baker.make(DocumentType, sunat_code='PEC')
        self.movement_type = baker.make(MovementType, code='I01', sunat_code='01')
        self.product = baker.make(Product, code='', product_group=self.group,
                                   unit_of_measure=self.unit,
                                   stock_type=self.stock_type)
        self.start_date = date(2024, 1, 1)
        self.end_date = date(2024, 1, 31)
        baker.make(Kardex, warehouse=self.warehouse, product=self.product,
                   operation_date=timezone.make_aware(datetime(2023, 12, 31, 9, 0)),
                   total_quantity=Decimal('7'), total_amount=Decimal('21'))

    def test_format_sunat_not_grows_with_catalogo(self):
        """Era 4 consultas por producto: dos `select_related`, el saldo inicial y
        el `get_kardex()` del periodo. Ahora el lote se resuelve de una vez."""
        from django.db import connection
        from django.test.utils import CaptureQueriesContext
        from almacen.reports import KardexExcelReport

        report = KardexExcelReport()
        report.get_sunat_physical_units_all(self.start_date, self.end_date, self.warehouse)
        with CaptureQueriesContext(connection) as con_uno:
            report.get_sunat_physical_units_all(self.start_date, self.end_date, self.warehouse)

        for number in range(9):
            product = baker.make(Product, code='', product_group=self.group,
                                  unit_of_measure=self.unit,
                                  stock_type=self.stock_type)
            baker.make(Kardex, warehouse=self.warehouse, product=product,
                       movement=baker.make(Movement, document_type=self.document_type,
                                             movement_type=self.movement_type),
                       operation_date=timezone.make_aware(datetime(2024, 1, 10, 9, 0)),
                       total_quantity=Decimal('5'), total_amount=Decimal('10'))

        with CaptureQueriesContext(connection) as con_diez:
            libro = report.get_sunat_physical_units_all(
                self.start_date, self.end_date, self.warehouse)

        self.assertLessEqual(len(con_diez), len(con_uno))
        self.assertLess(len(con_diez), 20)
        self.assertEqual(len(libro.sheetnames) - 1, 10)

    def test_consolidated_uses_kardex_previous_to_period(self):
        from almacen.reports import KardexExcelReport

        baker.make(Kardex, warehouse=self.warehouse, product=self.product,
                   operation_date=timezone.make_aware(datetime(2024, 6, 30, 9, 0)),
                   total_quantity=Decimal('99'), total_amount=Decimal('99'))

        libro = KardexExcelReport().get_consolidated_products(
            self.start_date, self.end_date, self.warehouse)

        sheet = libro.active
        self.assertEqual(sheet.cell(row=4, column=4).value, Decimal('7'))
        self.assertEqual(sheet.cell(row=4, column=5).value, Decimal('21'))

    def test_format_normal_generates(self):
        from almacen.reports import KardexExcelReport

        libro = KardexExcelReport().get_normal_format_all(
            self.start_date, self.end_date, self.warehouse)

        sheet = libro.active
        self.assertEqual(sheet.cell(row=5, column=8).value, 'SALDO INICIAL:')


class ReporteKardexPorProductoTest(TestCase):
    """Los informes de kardex por producto resolvian el saldo inicial con un
    `latest()` por fila. `initial_kardex_of()` lee el lote que el reporte
    precargo, y si el informe exporta un solo producto consulta ese producto:
    los dos caminos se ejercitan aqui, porque `manage.py check` no ejecuta
    cuerpos de funcion."""

    def setUp(self):
        from contabilidad.models import Account, StockType
        from productos.models import ProductGroup

        self.warehouse = baker.make(Warehouse)
        self.group = baker.make(ProductGroup, code='000001',
                                account=baker.make(Account))
        self.product = baker.make(Product, code='', product_group=self.group,
                                   stock_type=baker.make(StockType))
        self.start_date = date(2024, 1, 1)
        self.end_date = date(2024, 1, 31)
        baker.make(Kardex, warehouse=self.warehouse, product=self.product,
                   operation_date=timezone.make_aware(datetime(2023, 12, 31, 9, 0)),
                   total_quantity=Decimal('7'), total_amount=Decimal('21'),
                   total_price=Decimal('3'))

    def test_tables_pdf_use_kardex_previous(self):
        from almacen.reports import KardexPdfReport
        from productos.models import ProductGroup

        report = KardexPdfReport('A4', self.start_date, self.end_date, self.warehouse,
                                   ProductGroup.objects.all())

        units = report.physical_units_detail_table(
            self.product, self.start_date, self.end_date, self.warehouse)
        self.assertEqual(units._cellvalues[2][7], '7.00')

        valued = report.valued_detail_table(
            self.product, self.start_date, self.end_date, self.warehouse)
        self.assertTrue(valued._cellvalues)

    def test_all_preload_batch(self):
        from almacen.reports import KardexExcelReport

        report = KardexExcelReport()
        libro = report.get_sunat_physical_units_all(
            self.start_date, self.end_date, self.warehouse)

        self.assertTrue(libro.sheetnames)
        self.assertIn(self.product.pk, report.kardex_iniciales)

    def test_all_valued_preload_batch(self):
        from almacen.reports import KardexExcelReport

        report = KardexExcelReport()
        libro = report.get_sunat_valued_all(
            self.start_date, self.end_date, self.warehouse)

        self.assertTrue(libro.sheetnames)
        self.assertIn(self.product.pk, report.kardex_iniciales)

    def test_formats_solo_product(self):
        from almacen.reports import KardexExcelReport

        report = KardexExcelReport()
        for metodo in ('get_sunat_physical_units_product',
                       'get_sunat_valued_product',
                       'get_normal_format_product'):
            with self.subTest(metodo=metodo):
                libro = getattr(report, metodo)(self.product, self.start_date,
                                                 self.end_date, self.warehouse)
                self.assertTrue(libro.sheetnames)


class StockAjaxTest(TestCase):
    """Los endpoints de autocompletado resolvian el ultimo Kardex uno por uno.
    Esto fija el JSON que devuelven, que es lo que consume el JavaScript."""

    def setUp(self):
        self.client.force_login(User.objects.create_superuser('buscador', 'b@example.com', 'key-segura'))
        self.warehouse = baker.make(Warehouse)
        self.product = baker.make(Product, description='ACERO INOXIDABLE',
                                   unit_of_measure=baker.make(UnitOfMeasure))
        self.unit = self.product.unit_of_measure
        baker.make(Kardex, warehouse=self.warehouse, product=self.product,
                   operation_date=timezone.make_aware(datetime(2024, 1, 10, 9, 0)),
                   total_quantity=Decimal('7'), total_amount=Decimal('21'), total_price=Decimal('3'))

    def get(self, url):
        return self.client.get(url, {'description': 'ACERO', 'warehouse': self.warehouse.pk},
                               HTTP_X_REQUESTED_WITH='XMLHttpRequest')

    def test_list_stock_product(self):
        respuesta = self.get('/almacen/product_stock_list/')

        self.assertEqual(respuesta.status_code, 200)
        data = respuesta.json()
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]['code'], self.product.code)
        self.assertEqual(data[0]['label'], 'ACERO INOXIDABLE')
        self.assertEqual(data[0]['unit'], self.unit.code)
        self.assertAlmostEqual(data[0]['stock'], 7)

    def test_search_products_warehouse(self):
        respuesta = self.get('/almacen/product_warehouse_search/')

        self.assertEqual(respuesta.status_code, 200)
        data = respuesta.json()
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]['code'], self.product.code)
        self.assertEqual(data[0]['unit'], self.unit.description)
        self.assertEqual(Decimal(data[0]['price']), Decimal('3'))
