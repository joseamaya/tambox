from django.test import TestCase
from model_bakery import baker
from compras.models import Proveedor, RepresentanteLegal, Cotizacion, \
    DetalleCotizacion, DetalleOrdenCompra, DetalleOrdenServicios, OrdenCompra
from datetime import date


# Create your tests here.
class ProveedorTest(TestCase):

    def setUp(self):
        self.p1 = baker.make(Proveedor)
        self.p2 = baker.make(Proveedor)
        self.p3 = baker.make(Proveedor)

    def test_creacion_proveedor(self):
        self.assertTrue(isinstance(self.p1, Proveedor))
        self.assertEqual(self.p1.__str__(), self.p1.razon_social)

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
        self.rl1 = baker.make(RepresentanteLegal)

    def test_creacion_representante_legal(self):
        self.assertTrue(isinstance(self.rl1, RepresentanteLegal))
        self.assertEqual(self.rl1.__str__(), self.rl1.nombre)


class CotizacionTest(TestCase):

    def setUp(self):
        self.fecha_actual = date.today()
        self.c1 = baker.make(Cotizacion, code='', date=self.fecha_actual)
        self.c2 = baker.make(Cotizacion, code='', date=self.fecha_actual)
        self.c3 = baker.make(Cotizacion, code='', date=self.fecha_actual)

    def test_creacion_proveedor(self):
        self.assertTrue(isinstance(self.c1, Cotizacion))
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
        baker.make(DetalleCotizacion, cotizacion=self.c1, detalle_requerimiento=None,
                   cantidad=10, cantidad_comprada=4)
        self.assertEqual(self.c1.establecer_estado_comprado(), Cotizacion.STATUS.ELEG_PARC)

        baker.make(DetalleCotizacion, cotizacion=self.c2, detalle_requerimiento=None,
                   cantidad=10, cantidad_comprada=10)
        self.assertEqual(self.c2.establecer_estado_comprado(), Cotizacion.STATUS.ELEG)

        baker.make(DetalleCotizacion, cotizacion=self.c3, detalle_requerimiento=None,
                   cantidad=10, cantidad_comprada=0)
        self.assertEqual(self.c3.establecer_estado_comprado(), Cotizacion.STATUS.DESC)

    def test_eliminar_referencia(self):
        pass


class ReporteXLSOrdenCompraTest(TestCase):
    """Ejecuta el armado del libro de Excel. `manage.py check` no ejecuta
    cuerpos de funcion, asi que sin esto un nombre sin importar en la funcion
    solo se descubriria al descargar el reporte."""

    def test_genera_el_libro(self):
        from compras.models import OrdenCompra
        from compras.reports import reporte_xls_orden_compra

        proveedor = baker.make(Proveedor)
        orden = baker.make(OrdenCompra, proveedor=proveedor)

        libro = reporte_xls_orden_compra(orden)

        self.assertIsNotNone(libro.active)


class ReportesPDFTest(TestCase):
    """Genera cada PDF de verdad. Los metodos de dibujado se movieron fuera de
    las vistas sin cambios, y ninguna comprobacion estatica garantiza que las
    llamadas encadenadas sigan funcionando: hay que ejecutarlas."""

    def test_orden_compra(self):
        from compras.models import OrdenCompra
        from compras.reports import PDFOrdenCompra

        orden = baker.make(OrdenCompra, proveedor=baker.make(Proveedor))

        contenido = PDFOrdenCompra().imprimir(orden)

        self.assertTrue(contenido.startswith(b'%PDF'))

    def test_orden_servicios(self):
        from compras.models import OrdenServicios
        from compras.reports import PDFOrdenServicios

        orden = baker.make(OrdenServicios, proveedor=baker.make(Proveedor))

        contenido = PDFOrdenServicios().imprimir(orden)

        self.assertTrue(contenido.startswith(b'%PDF'))

    def test_solicitud_cotizacion_sin_logo(self):
        from compras.reports import PDFSolicitudCotizacion

        cotizacion = baker.make(Cotizacion, proveedor=baker.make(Proveedor))

        contenido = PDFSolicitudCotizacion().imprimir(cotizacion)

        self.assertTrue(contenido.startswith(b'%PDF'))


class EstadosDeDetalleTest(TestCase):
    """Estos metodos solo leen campos de la instancia, asi que no hace falta
    tocar la base de datos, y fijan la regla compartida de clasificar()."""

    def test_detalle_cotizacion(self):
        self.assertEqual(DetalleCotizacion(cantidad=10, cantidad_comprada=0).establecer_estado_comprado(),
                         DetalleCotizacion.STATUS.PEND)
        self.assertEqual(DetalleCotizacion(cantidad=10, cantidad_comprada=4).establecer_estado_comprado(),
                         DetalleCotizacion.STATUS.ELEG_PARC)
        self.assertEqual(DetalleCotizacion(cantidad=10, cantidad_comprada=10).establecer_estado_comprado(),
                         DetalleCotizacion.STATUS.ELEG)
        self.assertEqual(DetalleCotizacion(cantidad=10, cantidad_comprada=12).establecer_estado_comprado(),
                         DetalleCotizacion.STATUS.ELEG)

    def test_detalle_orden_compra(self):
        self.assertEqual(DetalleOrdenCompra(cantidad=10, cantidad_ingresada=0).establecer_estado(),
                         DetalleOrdenCompra.STATUS.PEND)
        self.assertEqual(DetalleOrdenCompra(cantidad=10, cantidad_ingresada=4).establecer_estado(),
                         DetalleOrdenCompra.STATUS.ING_PARC)
        self.assertEqual(DetalleOrdenCompra(cantidad=10, cantidad_ingresada=10).establecer_estado(),
                         DetalleOrdenCompra.STATUS.ING)

    def test_detalle_orden_servicios(self):
        self.assertEqual(DetalleOrdenServicios(cantidad=10, cantidad_conforme=0).establecer_estado_atendido(),
                         DetalleOrdenServicios.STATUS.PEND)
        self.assertEqual(DetalleOrdenServicios(cantidad=10, cantidad_conforme=4).establecer_estado_atendido(),
                         DetalleOrdenServicios.STATUS.CONF_PARC)
        self.assertEqual(DetalleOrdenServicios(cantidad=10, cantidad_conforme=10).establecer_estado_atendido(),
                         DetalleOrdenServicios.STATUS.CONF)


class TotalesDeOrdenCompraTest(TestCase):
    """`total` y `total_letras` encadenan `subtotal` e `impuesto`, y las
    plantillas las invocan mas de una vez: sin memorizar se repiten las
    consultas. No se convierten en agregados SQL porque redondean fila a fila."""

    def test_subtotal_e_impuesto_se_calculan_una_sola_vez(self):
        orden = baker.make(OrdenCompra, proveedor=baker.make(Proveedor))

        with self.assertNumQueries(1):
            orden.subtotal

        with self.assertNumQueries(1):
            orden.impuesto

        with self.assertNumQueries(0):
            orden.subtotal
            orden.impuesto
            orden.total

    def test_los_detalles_usan_la_cache_del_prefetch(self):
        """`subtotal` recorre detalleordencompra_set y no un .filter(): solo asi
        prefetch_related evita una consulta por orden en los reportes."""
        baker.make(OrdenCompra, proveedor=baker.make(Proveedor))

        ordenes = list(OrdenCompra.objects.prefetch_related('detalleordencompra_set'))

        with self.assertNumQueries(0):
            for orden in ordenes:
                orden.subtotal
                orden.impuesto
