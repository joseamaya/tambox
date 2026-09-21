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

    def test_creacion_proveedor(self):
        self.assertTrue(isinstance(self.p1, Supplier))
        self.assertEqual(self.p1.__str__(), self.p1.business_name)

    def test_siguiente_proveedor(self):
        self.assertEqual(self.p2.pk, self.p1.siguiente())
        self.assertEqual(self.p3.pk, self.p2.siguiente())

    def test_anterior_proveedor(self):
        self.assertEqual(self.p1.pk, self.p2.anterior())
        self.assertEqual(self.p2.pk, self.p3.anterior())

    def test_primer_proveedor(self):
        self.assertEqual(self.p1.pk, self.p3.siguiente())

    def test_ultimo_proveedor(self):
        self.assertEqual(self.p3.pk, self.p1.anterior())


class RepresentanteLegalTest(TestCase):

    def setUp(self):
        self.rl1 = baker.make(LegalRepresentative)

    def test_creacion_representante_legal(self):
        self.assertTrue(isinstance(self.rl1, LegalRepresentative))
        self.assertEqual(self.rl1.__str__(), self.rl1.name)


class CotizacionTest(TestCase):

    def setUp(self):
        self.fecha_actual = date.today()
        self.c1 = baker.make(Quotation, code='', date=self.fecha_actual)
        self.c2 = baker.make(Quotation, code='', date=self.fecha_actual)
        self.c3 = baker.make(Quotation, code='', date=self.fecha_actual)

    def test_creacion_proveedor(self):
        self.assertTrue(isinstance(self.c1, Quotation))
        self.assertEqual(self.c1.__str__(), self.c1.code)

    def test_siguiente_cotizacion(self):
        self.assertEqual(self.c2.pk, self.c1.siguiente())
        self.assertEqual(self.c3.pk, self.c2.siguiente())

    def test_anterior_cotizacion(self):
        self.assertEqual(self.c1.pk, self.c2.anterior())
        self.assertEqual(self.c2.pk, self.c3.anterior())

    def test_primera_cotizacion(self):
        self.assertEqual(self.c1.pk, self.c3.siguiente())

    def test_ultima_cotizacion(self):
        self.assertEqual(self.c3.pk, self.c1.anterior())

    def test_estado(self):
        """Una cotizacion refleja cuanto de lo cotizado se compro. Antes este
        test clasificaba por el estado de los detalles con `establecer_estado`,
        que un refactor posterior reemplazo por `establecer_estado_comprado`."""
        baker.make(QuotationDetail, quotation=self.c1, requirement_detail=None,
                   quantity=10, purchased_quantity=4)
        self.assertEqual(self.c1.establecer_estado_comprado(), Quotation.STATUS.ELEG_PARC)

        baker.make(QuotationDetail, quotation=self.c2, requirement_detail=None,
                   quantity=10, purchased_quantity=10)
        self.assertEqual(self.c2.establecer_estado_comprado(), Quotation.STATUS.ELEG)

        baker.make(QuotationDetail, quotation=self.c3, requirement_detail=None,
                   quantity=10, purchased_quantity=0)
        self.assertEqual(self.c3.establecer_estado_comprado(), Quotation.STATUS.DESC)

    def test_eliminar_referencia(self):
        pass


class ReporteXLSOrdenCompraTest(TestCase):
    """Ejecuta el armado del libro de Excel. `manage.py check` no ejecuta
    cuerpos de funcion, asi que sin esto un nombre sin importar en la funcion
    solo se descubriria al descargar el reporte."""

    def test_genera_el_libro(self):
        from compras.models import PurchaseOrder
        from compras.reports import reporte_xls_orden_compra

        supplier = baker.make(Supplier)
        order = baker.make(PurchaseOrder, supplier=supplier)

        libro = reporte_xls_orden_compra(order)

        self.assertIsNotNone(libro.active)


class ReportesPDFTest(TestCase):
    """Genera cada PDF de verdad. Los metodos de dibujado se movieron fuera de
    las vistas sin cambios, y ninguna comprobacion estatica garantiza que las
    llamadas encadenadas sigan funcionando: hay que ejecutarlas."""

    def test_orden_compra(self):
        from compras.models import PurchaseOrder
        from compras.reports import PDFOrdenCompra

        order = baker.make(PurchaseOrder, supplier=baker.make(Supplier))

        contenido = PDFOrdenCompra().imprimir(order)

        self.assertTrue(contenido.startswith(b'%PDF'))

    def test_orden_servicios(self):
        from compras.models import ServiceOrder
        from compras.reports import PDFOrdenServicios

        order = baker.make(ServiceOrder, supplier=baker.make(Supplier))

        contenido = PDFOrdenServicios().imprimir(order)

        self.assertTrue(contenido.startswith(b'%PDF'))

    def test_solicitud_cotizacion_sin_logo(self):
        from compras.reports import PDFSolicitudCotizacion

        quotation = baker.make(Quotation, supplier=baker.make(Supplier))

        contenido = PDFSolicitudCotizacion().imprimir(quotation)

        self.assertTrue(contenido.startswith(b'%PDF'))


class EstadosDeDetalleTest(TestCase):
    """Estos metodos solo leen campos de la instancia, asi que no hace falta
    tocar la base de datos, y fijan la regla compartida de clasificar()."""

    def test_detalle_cotizacion(self):
        self.assertEqual(QuotationDetail(quantity=10, purchased_quantity=0).establecer_estado_comprado(),
                         QuotationDetail.STATUS.PEND)
        self.assertEqual(QuotationDetail(quantity=10, purchased_quantity=4).establecer_estado_comprado(),
                         QuotationDetail.STATUS.ELEG_PARC)
        self.assertEqual(QuotationDetail(quantity=10, purchased_quantity=10).establecer_estado_comprado(),
                         QuotationDetail.STATUS.ELEG)
        self.assertEqual(QuotationDetail(quantity=10, purchased_quantity=12).establecer_estado_comprado(),
                         QuotationDetail.STATUS.ELEG)

    def test_detalle_orden_compra(self):
        self.assertEqual(PurchaseOrderDetail(quantity=10, received_quantity=0).establecer_estado(),
                         PurchaseOrderDetail.STATUS.PEND)
        self.assertEqual(PurchaseOrderDetail(quantity=10, received_quantity=4).establecer_estado(),
                         PurchaseOrderDetail.STATUS.ING_PARC)
        self.assertEqual(PurchaseOrderDetail(quantity=10, received_quantity=10).establecer_estado(),
                         PurchaseOrderDetail.STATUS.ING)

    def test_detalle_orden_servicios(self):
        self.assertEqual(ServiceOrderDetail(quantity=10, conformed_quantity=0).establecer_estado_atendido(),
                         ServiceOrderDetail.STATUS.PEND)
        self.assertEqual(ServiceOrderDetail(quantity=10, conformed_quantity=4).establecer_estado_atendido(),
                         ServiceOrderDetail.STATUS.CONF_PARC)
        self.assertEqual(ServiceOrderDetail(quantity=10, conformed_quantity=10).establecer_estado_atendido(),
                         ServiceOrderDetail.STATUS.CONF)


class TotalesDeOrdenCompraTest(TestCase):
    """`total` y `total_in_words` encadenan `subtotal` e `impuesto`, y las
    plantillas las invocan mas de una vez: sin memorizar se repiten las
    consultas. No se convierten en agregados SQL porque redondean fila a fila."""

    def test_subtotal_e_impuesto_se_calculan_una_sola_vez(self):
        order = baker.make(PurchaseOrder, supplier=baker.make(Supplier))

        with self.assertNumQueries(1):
            order.subtotal

        with self.assertNumQueries(1):
            order.impuesto

        with self.assertNumQueries(0):
            order.subtotal
            order.impuesto
            order.total

    def test_los_detalles_usan_la_cache_del_prefetch(self):
        """`subtotal` recorre details y no un .filter(): solo asi
        prefetch_related evita una consulta por orden en los reportes."""
        baker.make(PurchaseOrder, supplier=baker.make(Supplier))

        ordenes = list(PurchaseOrder.objects.prefetch_related('details'))

        with self.assertNumQueries(0):
            for order in ordenes:
                order.subtotal
                order.impuesto
