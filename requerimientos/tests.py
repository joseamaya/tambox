from django.test import TestCase
from model_bakery import baker
from administracion.models import NivelAprobacion, Oficina, Puesto, Trabajador
from requerimientos.models import Requerimiento, DetalleRequerimiento, \
    AprobacionRequerimiento
from tambox.estados import clasificar, COMPLETO, PARCIAL, VACIO


# Create your tests here.
class RequerimientoTest(TestCase):
    def setUp(self):
        self.r1 = baker.make(Requerimiento, codigo='')
        self.r2 = baker.make(Requerimiento, codigo='')
        self.r3 = baker.make(Requerimiento, codigo='')

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
        r5 = baker.make(Requerimiento, codigo=self.r1.pk)
        self.assertEqual(r5.pk, self.r1.pk)

    def test_estado_cotizado(self):
        dr1 = baker.make(DetalleRequerimiento, requerimiento=self.r1, estado=DetalleRequerimiento.STATUS.COTIZ_PARC)
        dr2 = baker.make(DetalleRequerimiento, requerimiento=self.r1, estado=DetalleRequerimiento.STATUS.COTIZ_PARC)
        dr3 = baker.make(DetalleRequerimiento, requerimiento=self.r1, estado=DetalleRequerimiento.STATUS.PEND)
        self.r1.establecer_estado_cotizado()
        self.assertEqual(self.r1.estado, Requerimiento.STATUS.COTIZ_PARC)
        dr4 = baker.make(DetalleRequerimiento, requerimiento=self.r2, estado=DetalleRequerimiento.STATUS.COTIZ)
        dr5 = baker.make(DetalleRequerimiento, requerimiento=self.r2, estado=DetalleRequerimiento.STATUS.COTIZ)
        dr6 = baker.make(DetalleRequerimiento, requerimiento=self.r2, estado=DetalleRequerimiento.STATUS.COTIZ)
        self.r2.establecer_estado_cotizado()
        self.assertEqual(self.r2.estado, Requerimiento.STATUS.COTIZ)
        dr7 = baker.make(DetalleRequerimiento, requerimiento=self.r3, estado=DetalleRequerimiento.STATUS.COTIZ_PARC)
        dr8 = baker.make(DetalleRequerimiento, requerimiento=self.r3, estado=DetalleRequerimiento.STATUS.COTIZ_PARC)
        dr9 = baker.make(DetalleRequerimiento, requerimiento=self.r3, estado=DetalleRequerimiento.STATUS.COTIZ_PARC)
        self.r3.establecer_estado_cotizado()
        self.assertEqual(self.r3.estado, Requerimiento.STATUS.COTIZ_PARC)

    def test_estado_comprado(self):
        dr1 = baker.make(DetalleRequerimiento, requerimiento=self.r1, estado=DetalleRequerimiento.STATUS.PED_PARC)
        dr2 = baker.make(DetalleRequerimiento, requerimiento=self.r1, estado=DetalleRequerimiento.STATUS.COTIZ)
        dr3 = baker.make(DetalleRequerimiento, requerimiento=self.r1, estado=DetalleRequerimiento.STATUS.PED_PARC)
        self.r1.establecer_estado()
        self.assertEqual(self.r1.estado, Requerimiento.STATUS.PED_PARC)
        dr4 = baker.make(DetalleRequerimiento, requerimiento=self.r2, estado=DetalleRequerimiento.STATUS.PED)
        dr5 = baker.make(DetalleRequerimiento, requerimiento=self.r2, estado=DetalleRequerimiento.STATUS.PED)
        dr6 = baker.make(DetalleRequerimiento, requerimiento=self.r2, estado=DetalleRequerimiento.STATUS.PED)
        self.r2.establecer_estado()
        self.assertEqual(self.r2.estado, Requerimiento.STATUS.PED)
        dr7 = baker.make(DetalleRequerimiento, requerimiento=self.r3, estado=DetalleRequerimiento.STATUS.PED_PARC)
        dr8 = baker.make(DetalleRequerimiento, requerimiento=self.r3, estado=DetalleRequerimiento.STATUS.PED_PARC)
        dr9 = baker.make(DetalleRequerimiento, requerimiento=self.r3, estado=DetalleRequerimiento.STATUS.PED_PARC)
        self.r3.establecer_estado()
        self.assertEqual(self.r3.estado, Requerimiento.STATUS.PED_PARC)

    def test_estado_atendido(self):
        dr1 = baker.make(DetalleRequerimiento, requerimiento=self.r1, estado=DetalleRequerimiento.STATUS.ATEN_PARC)
        dr2 = baker.make(DetalleRequerimiento, requerimiento=self.r1, estado=DetalleRequerimiento.STATUS.ATEN_PARC)
        dr3 = baker.make(DetalleRequerimiento, requerimiento=self.r1, estado=DetalleRequerimiento.STATUS.PED)
        self.r1.establecer_estado_atendido()
        self.assertEqual(self.r1.estado, Requerimiento.STATUS.ATEN_PARC)
        dr4 = baker.make(DetalleRequerimiento, requerimiento=self.r2, estado=DetalleRequerimiento.STATUS.ATEN)
        dr5 = baker.make(DetalleRequerimiento, requerimiento=self.r2, estado=DetalleRequerimiento.STATUS.ATEN)
        dr6 = baker.make(DetalleRequerimiento, requerimiento=self.r2, estado=DetalleRequerimiento.STATUS.ATEN)
        self.r2.establecer_estado_atendido()
        self.assertEqual(self.r2.estado, Requerimiento.STATUS.ATEN)
        dr7 = baker.make(DetalleRequerimiento, requerimiento=self.r3, estado=DetalleRequerimiento.STATUS.ATEN_PARC)
        dr8 = baker.make(DetalleRequerimiento, requerimiento=self.r3, estado=DetalleRequerimiento.STATUS.ATEN_PARC)
        dr9 = baker.make(DetalleRequerimiento, requerimiento=self.r3, estado=DetalleRequerimiento.STATUS.ATEN_PARC)
        self.r3.establecer_estado_atendido()
        self.assertEqual(self.r3.estado, Requerimiento.STATUS.ATEN_PARC)


class DetalleRequerimientoTest(TestCase):
    def setUp(self):
        self.r1 = baker.make(Requerimiento, codigo='')

    def test_creacion_detalle_requerimiento(self):
        dr1 = baker.make(DetalleRequerimiento, requerimiento=self.r1)
        self.assertTrue(isinstance(dr1, DetalleRequerimiento))
        self.assertEqual(dr1.__str__(), self.r1.codigo + ' ' + str(dr1.nro_detalle))

    def test_estado_comprado(self):
        dr1 = baker.make(DetalleRequerimiento, requerimiento=self.r1, cantidad=5, cantidad_comprada=5)
        dr1.establecer_estado()
        self.assertEqual(dr1.estado, DetalleRequerimiento.STATUS.PED)
        dr2 = baker.make(DetalleRequerimiento, requerimiento=self.r1, cantidad=8, cantidad_comprada=5)
        dr2.establecer_estado()
        self.assertEqual(dr2.estado, DetalleRequerimiento.STATUS.PED_PARC)
        dr3 = baker.make(DetalleRequerimiento, requerimiento=self.r1, cantidad=8, cantidad_comprada=10)
        dr3.establecer_estado()
        self.assertEqual(dr3.estado, DetalleRequerimiento.STATUS.PED)

    def test_estado_atendido(self):
        dr1 = baker.make(DetalleRequerimiento, requerimiento=self.r1, cantidad=5, cantidad_atendida=5)
        dr1.establecer_estado_atendido()
        self.assertEqual(dr1.estado, DetalleRequerimiento.STATUS.ATEN)
        dr2 = baker.make(DetalleRequerimiento, requerimiento=self.r1, cantidad=8, cantidad_atendida=5)
        dr2.establecer_estado_atendido()
        self.assertEqual(dr2.estado, DetalleRequerimiento.STATUS.ATEN_PARC)
        dr3 = baker.make(DetalleRequerimiento, requerimiento=self.r1, cantidad=8, cantidad_atendida=10)
        dr3.establecer_estado_atendido()
        self.assertEqual(dr3.estado, DetalleRequerimiento.STATUS.ATEN)


class AprobacionRequerimientoTest(TestCase):
    def setUp(self):
        self.r1 = baker.make(Requerimiento, codigo='')
        self.apr1 = baker.make(AprobacionRequerimiento, requerimiento=self.r1)

    def test_creacion_detalle_requerimiento(self):
        self.assertTrue(isinstance(self.apr1, AprobacionRequerimiento))
        self.assertEqual(self.apr1.__str__(), self.r1.codigo)


class ClasificarTest(TestCase):
    """La regla detras de la maquina de estados."""

    def test_sin_avance(self):
        self.assertEqual(clasificar(0, 10), VACIO)

    def test_avance_parcial(self):
        self.assertEqual(clasificar(4, 10), PARCIAL)

    def test_avance_completo(self):
        self.assertEqual(clasificar(10, 10), COMPLETO)

    def test_avance_por_encima_del_total(self):
        self.assertEqual(clasificar(12, 10), COMPLETO)


class EstadosDeRequerimientoTest(TestCase):

    def _requerimiento(self, cantidad, cotizada=0, comprada=0, atendida=0):
        baker.make(NivelAprobacion, descripcion='USUARIO')
        oficina = baker.make(Oficina)
        trabajador = baker.make(Trabajador)
        baker.make(Puesto, oficina=oficina, trabajador=trabajador, fecha_fin=None)
        requerimiento = baker.make(Requerimiento, solicitante=trabajador, oficina=oficina, codigo='')
        baker.make(DetalleRequerimiento, requerimiento=requerimiento, nro_detalle=1,
                   cantidad=cantidad, cantidad_cotizada=cotizada,
                   cantidad_comprada=comprada, cantidad_atendida=atendida)
        return requerimiento

    def test_comprado_parcial_no_marca_como_comprado(self):
        requerimiento = self._requerimiento(cantidad=10, comprada=4)

        self.assertEqual(requerimiento.establecer_estado_comprado(), Requerimiento.STATUS.COMP_PARC)

    def test_crear_requerimiento_crea_su_aprobacion_inicial(self):
        """Antes fallaba siempre: la aprobacion se creaba antes de que el
        requerimiento tuviera pk."""
        requerimiento = self._requerimiento(cantidad=10)

        self.assertTrue(AprobacionRequerimiento.objects.filter(requerimiento=requerimiento).exists())

    def test_comprado_completo(self):
        requerimiento = self._requerimiento(cantidad=10, comprada=10)

        self.assertEqual(requerimiento.establecer_estado_comprado(), Requerimiento.STATUS.COMP)

    def test_comprado_por_encima_del_total(self):
        requerimiento = self._requerimiento(cantidad=10, comprada=12)

        self.assertEqual(requerimiento.establecer_estado_comprado(), Requerimiento.STATUS.COMP)

    def test_cotizado_parcial(self):
        requerimiento = self._requerimiento(cantidad=10, cotizada=4)

        self.assertEqual(requerimiento.establecer_estado_cotizado(), Requerimiento.STATUS.COTIZ_PARC)

    def test_cotizado_completo(self):
        requerimiento = self._requerimiento(cantidad=10, cotizada=10)

        self.assertEqual(requerimiento.establecer_estado_cotizado(), Requerimiento.STATUS.COTIZ)

    def test_atendido_parcial(self):
        requerimiento = self._requerimiento(cantidad=10, atendida=4)

        self.assertEqual(requerimiento.establecer_estado_atendido(), Requerimiento.STATUS.ATEN_PARC)

    def test_atendido_completo(self):
        requerimiento = self._requerimiento(cantidad=10, atendida=10)

        self.assertEqual(requerimiento.establecer_estado_atendido(), Requerimiento.STATUS.ATEN)

    def test_los_totales_se_calculan_una_sola_vez(self):
        """Suma columnas, asi que el agregado es exacto; la maquina de estados los
        invoca varias veces en la misma operacion."""
        requerimiento = self._requerimiento(cantidad=10)

        with self.assertNumQueries(1):
            self.assertEqual(requerimiento.total, 10)

        with self.assertNumQueries(1):
            requerimiento.total_cotizado

        with self.assertNumQueries(1):
            requerimiento.total_comprado

        with self.assertNumQueries(0):
            requerimiento.total
            requerimiento.total_cotizado
            requerimiento.total_comprado


class EstadosDeDetalleRequerimientoTest(TestCase):
    """Estos metodos solo leen los campos de la instancia, asi que no hace falta
    tocar la base de datos."""

    def _detalle(self, cantidad, cotizada=0, comprada=0, atendida=0):
        return DetalleRequerimiento(cantidad=cantidad, cantidad_cotizada=cotizada,
                                    cantidad_comprada=comprada, cantidad_atendida=atendida)

    def test_cotizado(self):
        self.assertEqual(self._detalle(10).establecer_estado_cotizado(), DetalleRequerimiento.STATUS.PEND)
        self.assertEqual(self._detalle(10, cotizada=4).establecer_estado_cotizado(),
                         DetalleRequerimiento.STATUS.COTIZ_PARC)
        self.assertEqual(self._detalle(10, cotizada=10).establecer_estado_cotizado(),
                         DetalleRequerimiento.STATUS.COTIZ)

    def test_comprado(self):
        self.assertEqual(self._detalle(10, comprada=4).establecer_estado_comprado(),
                         DetalleRequerimiento.STATUS.COMP_PARC)
        self.assertEqual(self._detalle(10, comprada=10).establecer_estado_comprado(),
                         DetalleRequerimiento.STATUS.COMP)

    def test_atendido(self):
        self.assertEqual(self._detalle(10, atendida=4).establecer_estado_atendido(),
                         DetalleRequerimiento.STATUS.ATEN_PARC)
        self.assertEqual(self._detalle(10, atendida=10).establecer_estado_atendido(),
                         DetalleRequerimiento.STATUS.ATEN)
