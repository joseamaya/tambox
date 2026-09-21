from django.test import TestCase
from model_bakery import baker
from administracion.models import NivelAprobacion, Oficina, Puesto, Trabajador
from requerimientos.models import Requerimiento, DetalleRequerimiento, \
    AprobacionRequerimiento
from tambox.estados import clasificar, COMPLETO, PARCIAL, VACIO


def crear_requerimiento(**kwargs):
    """Un requerimiento necesita que su solicitante tenga puesto asignado:
    `save()` lanza ValidationError si no lo tiene, porque de ahi sale la oficina
    y la cadena de aprobaciones. Los tests viejos no armaban ese grafo."""
    NivelAprobacion.objects.get_or_create(description='USUARIO')
    oficina = baker.make(Oficina)
    trabajador = baker.make(Trabajador)
    baker.make(Puesto, oficina=oficina, trabajador=trabajador, end_date=None)
    return baker.make(Requerimiento, solicitante=trabajador, oficina=oficina, **kwargs)


# Create your tests here.
class RequerimientoTest(TestCase):
    def setUp(self):
        self.r1 = crear_requerimiento(code='')
        self.r2 = crear_requerimiento(code='')
        self.r3 = crear_requerimiento(code='')

    def test_creacion_requerimiento(self):
        self.assertTrue(isinstance(self.r1, Requerimiento))
        self.assertEqual(self.r1.__str__(), self.r1.code)

    def test_siguiente_requerimiento(self):
        self.assertEqual(self.r2, self.r1.siguiente())
        self.assertEqual(self.r3, self.r2.siguiente())

    def test_anterior_requerimiento(self):
        self.assertEqual(self.r1, self.r2.anterior())
        self.assertEqual(self.r2, self.r3.anterior())

    def test_primer_requerimiento(self):
        self.assertEqual(self.r1, self.r3.siguiente())

    def test_ultimo_requerimiento(self):
        self.assertEqual(self.r3, self.r1.anterior())

    def test_actualizacion_requerimiento(self):
        """`save()` solo genera el code cuando esta vacio, asi que guardar un
        requerimiento existente no lo duplica ni le cambia el code."""
        code = self.r1.code
        quantity = Requerimiento.objects.count()

        self.r1.save()

        self.assertEqual(code, Requerimiento.objects.get(pk=self.r1.pk).code)
        self.assertEqual(quantity, Requerimiento.objects.count())


class DetalleRequerimientoTest(TestCase):
    def setUp(self):
        self.r1 = crear_requerimiento(code='')

    def test_creacion_detalle_requerimiento(self):
        dr1 = baker.make(DetalleRequerimiento, requerimiento=self.r1)
        self.assertTrue(isinstance(dr1, DetalleRequerimiento))
        self.assertEqual(dr1.__str__(), self.r1.code + ' ' + str(dr1.nro_detalle))

    def test_estado_atendido(self):
        dr1 = baker.make(DetalleRequerimiento, requerimiento=self.r1, quantity=5, served_quantity=5)
        dr1.establecer_estado_atendido()
        self.assertEqual(dr1.status, DetalleRequerimiento.STATUS.ATEN)
        dr2 = baker.make(DetalleRequerimiento, requerimiento=self.r1, quantity=8, served_quantity=5)
        dr2.establecer_estado_atendido()
        self.assertEqual(dr2.status, DetalleRequerimiento.STATUS.ATEN_PARC)
        dr3 = baker.make(DetalleRequerimiento, requerimiento=self.r1, quantity=8, served_quantity=10)
        dr3.establecer_estado_atendido()
        self.assertEqual(dr3.status, DetalleRequerimiento.STATUS.ATEN)


class AprobacionRequerimientoTest(TestCase):
    def setUp(self):
        self.r1 = crear_requerimiento(code='')
        self.apr1 = baker.make(AprobacionRequerimiento, requerimiento=self.r1)

    def test_creacion_aprobacion_requerimiento(self):
        self.assertTrue(isinstance(self.apr1, AprobacionRequerimiento))
        self.assertEqual(self.apr1.requerimiento, self.r1)


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

    def _requerimiento(self, quantity, cotizada=0, comprada=0, atendida=0):
        requerimiento = crear_requerimiento(code='')
        baker.make(DetalleRequerimiento, requerimiento=requerimiento, nro_detalle=1,
                   quantity=quantity, quoted_quantity=cotizada,
                   purchased_quantity=comprada, served_quantity=atendida)
        return requerimiento

    def test_comprado_parcial_no_marca_como_comprado(self):
        requerimiento = self._requerimiento(quantity=10, comprada=4)

        self.assertEqual(requerimiento.establecer_estado_comprado(), Requerimiento.STATUS.COMP_PARC)

    def test_crear_requerimiento_crea_su_aprobacion_inicial(self):
        """Antes fallaba siempre: la aprobacion se creaba antes de que el
        requerimiento tuviera pk."""
        requerimiento = self._requerimiento(quantity=10)

        self.assertTrue(AprobacionRequerimiento.objects.filter(requerimiento=requerimiento).exists())

    def test_comprado_completo(self):
        requerimiento = self._requerimiento(quantity=10, comprada=10)

        self.assertEqual(requerimiento.establecer_estado_comprado(), Requerimiento.STATUS.COMP)

    def test_comprado_por_encima_del_total(self):
        requerimiento = self._requerimiento(quantity=10, comprada=12)

        self.assertEqual(requerimiento.establecer_estado_comprado(), Requerimiento.STATUS.COMP)

    def test_cotizado_parcial(self):
        requerimiento = self._requerimiento(quantity=10, cotizada=4)

        self.assertEqual(requerimiento.establecer_estado_cotizado(), Requerimiento.STATUS.COTIZ_PARC)

    def test_cotizado_completo(self):
        requerimiento = self._requerimiento(quantity=10, cotizada=10)

        self.assertEqual(requerimiento.establecer_estado_cotizado(), Requerimiento.STATUS.COTIZ)

    def test_atendido_parcial(self):
        requerimiento = self._requerimiento(quantity=10, atendida=4)

        self.assertEqual(requerimiento.establecer_estado_atendido(), Requerimiento.STATUS.ATEN_PARC)

    def test_atendido_completo(self):
        requerimiento = self._requerimiento(quantity=10, atendida=10)

        self.assertEqual(requerimiento.establecer_estado_atendido(), Requerimiento.STATUS.ATEN)

    def test_los_totales_se_calculan_una_sola_vez(self):
        """Suma columnas, asi que el agregado es exacto; la maquina de estados los
        invoca varias veces en la misma operacion."""
        requerimiento = self._requerimiento(quantity=10)

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

    def test_el_prefetch_evita_una_consulta_por_requerimiento(self):
        """Los totales recorren el manager inverso y no un .filter(), que siempre
        lanza su propia consulta. Eso es lo que hace que prefetch_related sirva
        en los bucles que cargan muchos requerimientos."""
        for quantity in (10, 20, 30):
            self._requerimiento(quantity=quantity)

        requerimientos = list(Requerimiento.objects.prefetch_related('details'))

        with self.assertNumQueries(0):
            for requerimiento in requerimientos:
                requerimiento.total
                requerimiento.total_cotizado
                requerimiento.total_comprado


class EstadosDeDetalleRequerimientoTest(TestCase):
    """Estos metodos solo leen los campos de la instancia, asi que no hace falta
    tocar la base de datos."""

    def _detalle(self, quantity, cotizada=0, comprada=0, atendida=0):
        return DetalleRequerimiento(quantity=quantity, quoted_quantity=cotizada,
                                    purchased_quantity=comprada, served_quantity=atendida)

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
