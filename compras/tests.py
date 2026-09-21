from django.test import TestCase
from model_bakery import baker
from compras.models import Supplier, LegalRepresentative, Quotation, \
    QuotationDetail, PurchaseOrderDetail, ServiceOrderDetail, PurchaseOrder
from datetime import date


# Create your tests here.
class ProveedorTest(TestCase):

    def setUp(self):
        self.p1 = baker.make(Supplier)
        self.p2 = baker.make(Supplier)
        self.p3 = baker.make(Supplier)

    def test_creation_supplier(self):
        self.assertTrue(isinstance(self.p1, Supplier))
        self.assertEqual(self.p1.__str__(), self.p1.business_name)

    def test_next_supplier(self):
        self.assertEqual(self.p2.pk, self.p1.next())
        self.assertEqual(self.p3.pk, self.p2.next())

    def test_previous_supplier(self):
        self.assertEqual(self.p1.pk, self.p2.previous())
        self.assertEqual(self.p2.pk, self.p3.previous())

    def test_first_supplier(self):
        self.assertEqual(self.p1.pk, self.p3.next())

    def test_last_supplier(self):
        self.assertEqual(self.p3.pk, self.p1.previous())


class RepresentanteLegalTest(TestCase):

    def setUp(self):
        self.rl1 = baker.make(LegalRepresentative)

    def test_creation_representative_legal(self):
        self.assertTrue(isinstance(self.rl1, LegalRepresentative))
        self.assertEqual(self.rl1.__str__(), self.rl1.name)


class CotizacionTest(TestCase):

    def setUp(self):
        self.current_date = date.today()
        self.c1 = baker.make(Quotation, code='', date=self.current_date)
        self.c2 = baker.make(Quotation, code='', date=self.current_date)
        self.c3 = baker.make(Quotation, code='', date=self.current_date)

    def test_creation_supplier_1(self):
        self.assertTrue(isinstance(self.c1, Quotation))
        self.assertEqual(self.c1.__str__(), self.c1.code)

    def test_next_quotation(self):
        self.assertEqual(self.c2.pk, self.c1.next())
        self.assertEqual(self.c3.pk, self.c2.next())

    def test_previous_quotation(self):
        self.assertEqual(self.c1.pk, self.c2.previous())
        self.assertEqual(self.c2.pk, self.c3.previous())

    def test_first_quotation(self):
        self.assertEqual(self.c1.pk, self.c3.next())

    def test_last_quotation(self):
        self.assertEqual(self.c3.pk, self.c1.previous())

    def test_status(self):
        """Una cotizacion refleja cuanto de lo cotizado se compro. Antes este
        test clasificaba por el estado de los detalles con `set_status`,
        que un refactor posterior reemplazo por `set_status_purchased`."""
        baker.make(QuotationDetail, quotation=self.c1, requirement_detail=None,
                   quantity=10, purchased_quantity=4)
        self.assertEqual(self.c1.set_status_purchased(), Quotation.STATUS.ELEG_PARC)

        baker.make(QuotationDetail, quotation=self.c2, requirement_detail=None,
                   quantity=10, purchased_quantity=10)
        self.assertEqual(self.c2.set_status_purchased(), Quotation.STATUS.ELEG)

        baker.make(QuotationDetail, quotation=self.c3, requirement_detail=None,
                   quantity=10, purchased_quantity=0)
        self.assertEqual(self.c3.set_status_purchased(), Quotation.STATUS.DESC)

    def test_delete_reference(self):
        pass


class ReporteXLSOrdenCompraTest(TestCase):
    """Ejecuta el armado del libro de Excel. `manage.py check` no ejecuta
    cuerpos de funcion, asi que sin esto un nombre sin importar en la funcion
    solo se descubriria al descargar el reporte."""

    def test_generates_book(self):
        from compras.models import PurchaseOrder
        from compras.reports import purchase_order_xls_report

        supplier = baker.make(Supplier)
        order = baker.make(PurchaseOrder, supplier=supplier)

        libro = purchase_order_xls_report(order)

        self.assertIsNotNone(libro.active)


class ReportesPDFTest(TestCase):
    """Genera cada PDF de verdad. Los metodos de dibujado se movieron fuera de
    las vistas sin cambios, y ninguna comprobacion estatica garantiza que las
    llamadas encadenadas sigan funcionando: hay que ejecutarlas."""

    def test_order_purchase(self):
        from compras.models import PurchaseOrder
        from compras.reports import PurchaseOrderPdf

        order = baker.make(PurchaseOrder, supplier=baker.make(Supplier))

        contenido = PurchaseOrderPdf().render(order)

        self.assertTrue(contenido.startswith(b'%PDF'))

    def test_order_services(self):
        from compras.models import ServiceOrder
        from compras.reports import ServiceOrderPdf

        order = baker.make(ServiceOrder, supplier=baker.make(Supplier))

        contenido = ServiceOrderPdf().render(order)

        self.assertTrue(contenido.startswith(b'%PDF'))

    def test_request_quotation_without_logo(self):
        from compras.reports import QuotationRequestPdf

        quotation = baker.make(Quotation, supplier=baker.make(Supplier))

        contenido = QuotationRequestPdf().render(quotation)

        self.assertTrue(contenido.startswith(b'%PDF'))


class EstadosDeDetalleTest(TestCase):
    """Estos metodos solo leen campos de la instance, asi que no hace falta
    tocar la base de datos, y fijan la regla compartida de classify()."""

    def test_detail_quotation(self):
        self.assertEqual(QuotationDetail(quantity=10, purchased_quantity=0).set_status_purchased(),
                         QuotationDetail.STATUS.PEND)
        self.assertEqual(QuotationDetail(quantity=10, purchased_quantity=4).set_status_purchased(),
                         QuotationDetail.STATUS.ELEG_PARC)
        self.assertEqual(QuotationDetail(quantity=10, purchased_quantity=10).set_status_purchased(),
                         QuotationDetail.STATUS.ELEG)
        self.assertEqual(QuotationDetail(quantity=10, purchased_quantity=12).set_status_purchased(),
                         QuotationDetail.STATUS.ELEG)

    def test_detail_order_purchase(self):
        self.assertEqual(PurchaseOrderDetail(quantity=10, received_quantity=0).set_status(),
                         PurchaseOrderDetail.STATUS.PEND)
        self.assertEqual(PurchaseOrderDetail(quantity=10, received_quantity=4).set_status(),
                         PurchaseOrderDetail.STATUS.ING_PARC)
        self.assertEqual(PurchaseOrderDetail(quantity=10, received_quantity=10).set_status(),
                         PurchaseOrderDetail.STATUS.ING)

    def test_detail_order_services(self):
        self.assertEqual(ServiceOrderDetail(quantity=10, conformed_quantity=0).set_status_served(),
                         ServiceOrderDetail.STATUS.PEND)
        self.assertEqual(ServiceOrderDetail(quantity=10, conformed_quantity=4).set_status_served(),
                         ServiceOrderDetail.STATUS.CONF_PARC)
        self.assertEqual(ServiceOrderDetail(quantity=10, conformed_quantity=10).set_status_served(),
                         ServiceOrderDetail.STATUS.CONF)


class TotalesDeOrdenCompraTest(TestCase):
    """`total` y `total_in_words` encadenan `subtotal` e `tax`, y las
    plantillas las invocan mas de una vez: sin memorizar se repiten las
    consultas. No se convierten en agregados SQL porque redondean fila a row."""

    def test_subtotal_tax_calculate_only_time(self):
        order = baker.make(PurchaseOrder, supplier=baker.make(Supplier))

        with self.assertNumQueries(1):
            order.subtotal

        with self.assertNumQueries(1):
            order.tax

        with self.assertNumQueries(0):
            order.subtotal
            order.tax
            order.total

    def test_details_use_cache_prefetch(self):
        """`subtotal` recorre details y no un .filter(): solo asi
        prefetch_related evita una consulta por orden en los reportes."""
        baker.make(PurchaseOrder, supplier=baker.make(Supplier))

        orders = list(PurchaseOrder.objects.prefetch_related('details'))

        with self.assertNumQueries(0):
            for order in orders:
                order.subtotal
                order.tax
