from django.test import TestCase
from model_mommy import mommy
from requerimientos.models import Requerimiento, DetalleRequerimiento, \
    AprobacionRequerimiento


# Create your tests here.
class RequerimientoTest(TestCase):
    def setUp(self):
        self.r1 = mommy.make(Requerimiento, codigo='')
        self.r2 = mommy.make(Requerimiento, codigo='')
        self.r3 = mommy.make(Requerimiento, codigo='')

    def test_creacion_requerimiento(self):
        self.assertTrue(isinstance(self.r1, Requerimiento))
        self.assertEqual(self.r1.__str__(), self.r1.codigo)

    def test_siguiente_requerimiento(self):
        self.assertEqual(self.r2.pk, self.r1.siguiente())
        self.assertEqual(self.r3.pk, self.r2.siguiente())

    def test_anterior_requerimiento(self):
        self.assertEqual(self.r1.pk, self.r2.anterior())
        self.assertEqual(self.r2.pk, self.r3.anterior())

    def test_primer_requerimiento(self):
        self.assertEqual(self.r1.pk, self.r3.siguiente())

    def test_ultimo_requerimiento(self):
        self.assertEqual(self.r3.pk, self.r1.anterior())

    def test_actualizacion_requerimiento(self):
        r5 = mommy.make(Requerimiento, codigo=self.r1.pk)
        self.assertEqual(r5.pk, self.r1.pk)

    def test_estado_cotizado(self):
        dr1 = mommy.make(DetalleRequerimiento, requerimiento=self.r1, estado=DetalleRequerimiento.STATUS.COTIZ_PARC)
        dr2 = mommy.make(DetalleRequerimiento, requerimiento=self.r1, estado=DetalleRequerimiento.STATUS.COTIZ_PARC)
        dr3 = mommy.make(DetalleRequerimiento, requerimiento=self.r1, estado=DetalleRequerimiento.STATUS.PEND)
        self.r1.establecer_estado_cotizado()
        self.assertEqual(self.r1.estado, Requerimiento.STATUS.COTIZ_PARC)
        dr4 = mommy.make(DetalleRequerimiento, requerimiento=self.r2, estado=DetalleRequerimiento.STATUS.COTIZ)
        dr5 = mommy.make(DetalleRequerimiento, requerimiento=self.r2, estado=DetalleRequerimiento.STATUS.COTIZ)
        dr6 = mommy.make(DetalleRequerimiento, requerimiento=self.r2, estado=DetalleRequerimiento.STATUS.COTIZ)
        self.r2.establecer_estado_cotizado()
        self.assertEqual(self.r2.estado, Requerimiento.STATUS.COTIZ)
        dr7 = mommy.make(DetalleRequerimiento, requerimiento=self.r3, estado=DetalleRequerimiento.STATUS.COTIZ_PARC)
        dr8 = mommy.make(DetalleRequerimiento, requerimiento=self.r3, estado=DetalleRequerimiento.STATUS.COTIZ_PARC)
        dr9 = mommy.make(DetalleRequerimiento, requerimiento=self.r3, estado=DetalleRequerimiento.STATUS.COTIZ_PARC)
        self.r3.establecer_estado_cotizado()
        self.assertEqual(self.r3.estado, Requerimiento.STATUS.COTIZ_PARC)

    def test_estado_comprado(self):
        dr1 = mommy.make(DetalleRequerimiento, requerimiento=self.r1, estado=DetalleRequerimiento.STATUS.PED_PARC)
        dr2 = mommy.make(DetalleRequerimiento, requerimiento=self.r1, estado=DetalleRequerimiento.STATUS.COTIZ)
        dr3 = mommy.make(DetalleRequerimiento, requerimiento=self.r1, estado=DetalleRequerimiento.STATUS.PED_PARC)
        self.r1.establecer_estado()
        self.assertEqual(self.r1.estado, Requerimiento.STATUS.PED_PARC)
        dr4 = mommy.make(DetalleRequerimiento, requerimiento=self.r2, estado=DetalleRequerimiento.STATUS.PED)
        dr5 = mommy.make(DetalleRequerimiento, requerimiento=self.r2, estado=DetalleRequerimiento.STATUS.PED)
        dr6 = mommy.make(DetalleRequerimiento, requerimiento=self.r2, estado=DetalleRequerimiento.STATUS.PED)
        self.r2.establecer_estado()
        self.assertEqual(self.r2.estado, Requerimiento.STATUS.PED)
        dr7 = mommy.make(DetalleRequerimiento, requerimiento=self.r3, estado=DetalleRequerimiento.STATUS.PED_PARC)
        dr8 = mommy.make(DetalleRequerimiento, requerimiento=self.r3, estado=DetalleRequerimiento.STATUS.PED_PARC)
        dr9 = mommy.make(DetalleRequerimiento, requerimiento=self.r3, estado=DetalleRequerimiento.STATUS.PED_PARC)
        self.r3.establecer_estado()
        self.assertEqual(self.r3.estado, Requerimiento.STATUS.PED_PARC)

    def test_estado_atendido(self):
        dr1 = mommy.make(DetalleRequerimiento, requerimiento=self.r1, estado=DetalleRequerimiento.STATUS.ATEN_PARC)
        dr2 = mommy.make(DetalleRequerimiento, requerimiento=self.r1, estado=DetalleRequerimiento.STATUS.ATEN_PARC)
        dr3 = mommy.make(DetalleRequerimiento, requerimiento=self.r1, estado=DetalleRequerimiento.STATUS.PED)
        self.r1.establecer_estado_atendido()
        self.assertEqual(self.r1.estado, Requerimiento.STATUS.ATEN_PARC)
        dr4 = mommy.make(DetalleRequerimiento, requerimiento=self.r2, estado=DetalleRequerimiento.STATUS.ATEN)
        dr5 = mommy.make(DetalleRequerimiento, requerimiento=self.r2, estado=DetalleRequerimiento.STATUS.ATEN)
        dr6 = mommy.make(DetalleRequerimiento, requerimiento=self.r2, estado=DetalleRequerimiento.STATUS.ATEN)
        self.r2.establecer_estado_atendido()
        self.assertEqual(self.r2.estado, Requerimiento.STATUS.ATEN)
        dr7 = mommy.make(DetalleRequerimiento, requerimiento=self.r3, estado=DetalleRequerimiento.STATUS.ATEN_PARC)
        dr8 = mommy.make(DetalleRequerimiento, requerimiento=self.r3, estado=DetalleRequerimiento.STATUS.ATEN_PARC)
        dr9 = mommy.make(DetalleRequerimiento, requerimiento=self.r3, estado=DetalleRequerimiento.STATUS.ATEN_PARC)
        self.r3.establecer_estado_atendido()
        self.assertEqual(self.r3.estado, Requerimiento.STATUS.ATEN_PARC)


class DetalleRequerimientoTest(TestCase):
    def setUp(self):
        self.r1 = mommy.make(Requerimiento, codigo='')

    def test_creacion_detalle_requerimiento(self):
        dr1 = mommy.make(DetalleRequerimiento, requerimiento=self.r1)
        self.assertTrue(isinstance(dr1, DetalleRequerimiento))
        self.assertEqual(dr1.__str__(), self.r1.codigo + ' ' + str(dr1.nro_detalle))

    def test_estado_comprado(self):
        dr1 = mommy.make(DetalleRequerimiento, requerimiento=self.r1, cantidad=5, cantidad_comprada=5)
        dr1.establecer_estado()
        self.assertEqual(dr1.estado, DetalleRequerimiento.STATUS.PED)
        dr2 = mommy.make(DetalleRequerimiento, requerimiento=self.r1, cantidad=8, cantidad_comprada=5)
        dr2.establecer_estado()
        self.assertEqual(dr2.estado, DetalleRequerimiento.STATUS.PED_PARC)
        dr3 = mommy.make(DetalleRequerimiento, requerimiento=self.r1, cantidad=8, cantidad_comprada=10)
        dr3.establecer_estado()
        self.assertEqual(dr3.estado, DetalleRequerimiento.STATUS.PED)

    def test_estado_atendido(self):
        dr1 = mommy.make(DetalleRequerimiento, requerimiento=self.r1, cantidad=5, cantidad_atendida=5)
        dr1.establecer_estado_atendido()
        self.assertEqual(dr1.estado, DetalleRequerimiento.STATUS.ATEN)
        dr2 = mommy.make(DetalleRequerimiento, requerimiento=self.r1, cantidad=8, cantidad_atendida=5)
        dr2.establecer_estado_atendido()
        self.assertEqual(dr2.estado, DetalleRequerimiento.STATUS.ATEN_PARC)
        dr3 = mommy.make(DetalleRequerimiento, requerimiento=self.r1, cantidad=8, cantidad_atendida=10)
        dr3.establecer_estado_atendido()
        self.assertEqual(dr3.estado, DetalleRequerimiento.STATUS.ATEN)


class AprobacionRequerimientoTest(TestCase):
    def setUp(self):
        self.r1 = mommy.make(Requerimiento, codigo='')
        self.apr1 = mommy.make(AprobacionRequerimiento, requerimiento=self.r1)

    def test_creacion_detalle_requerimiento(self):
        self.assertTrue(isinstance(self.apr1, AprobacionRequerimiento))
        self.assertEqual(self.apr1.__str__(), self.r1.codigo)
