from django.test import TestCase
from model_bakery import baker
from compras.models import Proveedor, RepresentanteLegal, Cotizacion, \
    DetalleCotizacion
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
        self.c1 = baker.make(Cotizacion, codigo='', fecha=self.fecha_actual)
        self.c2 = baker.make(Cotizacion, codigo='', fecha=self.fecha_actual)
        self.c3 = baker.make(Cotizacion, codigo='', fecha=self.fecha_actual)

    def test_creacion_proveedor(self):
        self.assertTrue(isinstance(self.c1, Cotizacion))
        self.assertEqual(self.c1.__str__(), self.c1.codigo)

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
        dc1 = baker.make(DetalleCotizacion, cotizacion=self.c1, estado=DetalleCotizacion.STATUS.ELEG_PARC)
        dc2 = baker.make(DetalleCotizacion, cotizacion=self.c1, estado=DetalleCotizacion.STATUS.ELEG)
        dc3 = baker.make(DetalleCotizacion, cotizacion=self.c1, estado=DetalleCotizacion.STATUS.ELEG)
        self.c1.establecer_estado()
        self.assertEqual(self.c1.estado, Cotizacion.STATUS.ELEG_PARC)
        dc4 = baker.make(DetalleCotizacion, cotizacion=self.c2, estado=DetalleCotizacion.STATUS.ELEG)
        dc5 = baker.make(DetalleCotizacion, cotizacion=self.c2, estado=DetalleCotizacion.STATUS.ELEG)
        dc6 = baker.make(DetalleCotizacion, cotizacion=self.c2, estado=DetalleCotizacion.STATUS.ELEG)
        self.c2.establecer_estado()
        self.assertEqual(self.c2.estado, Cotizacion.STATUS.ELEG)
        dc7 = baker.make(DetalleCotizacion, cotizacion=self.c3, estado=DetalleCotizacion.STATUS.DESC)
        dc8 = baker.make(DetalleCotizacion, cotizacion=self.c3, estado=DetalleCotizacion.STATUS.DESC)
        dc9 = baker.make(DetalleCotizacion, cotizacion=self.c3, estado=DetalleCotizacion.STATUS.DESC)
        self.c3.establecer_estado()
        self.assertEqual(self.c3.estado, Cotizacion.STATUS.DESC)

    def test_eliminar_referencia(self):
        pass
