from django.test import TestCase
from model_bakery import baker
from administracion.models import ApprovalLevel, Office, Position, Worker
from requerimientos.models import Requirement, RequirementDetail, \
    RequirementApproval
from tambox.statuses import classify, COMPLETE, PARTIAL, EMPTY


def crear_requerimiento(**kwargs):
    """Un requerimiento necesita que su solicitante tenga puesto asignado:
    `save()` lanza ValidationError si no lo tiene, porque de ahi sale la oficina
    y la cadena de aprobaciones. Los tests viejos no armaban ese grafo."""
    ApprovalLevel.objects.get_or_create(description='USUARIO')
    office = baker.make(Office)
    worker = baker.make(Worker)
    baker.make(Position, office=office, worker=worker, end_date=None)
    return baker.make(Requirement, requester=worker, office=office, **kwargs)


# Create your tests here.
class RequerimientoTest(TestCase):
    def setUp(self):
        self.r1 = crear_requerimiento(code='')
        self.r2 = crear_requerimiento(code='')
        self.r3 = crear_requerimiento(code='')

    def test_creacion_requerimiento(self):
        self.assertTrue(isinstance(self.r1, Requirement))
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
        quantity = Requirement.objects.count()

        self.r1.save()

        self.assertEqual(code, Requirement.objects.get(pk=self.r1.pk).code)
        self.assertEqual(quantity, Requirement.objects.count())


class DetalleRequerimientoTest(TestCase):
    def setUp(self):
        self.r1 = crear_requerimiento(code='')

    def test_creacion_detalle_requerimiento(self):
        dr1 = baker.make(RequirementDetail, requirement=self.r1)
        self.assertTrue(isinstance(dr1, RequirementDetail))
        self.assertEqual(dr1.__str__(), self.r1.code + ' ' + str(dr1.line_number))

    def test_estado_atendido(self):
        dr1 = baker.make(RequirementDetail, requirement=self.r1, quantity=5, served_quantity=5)
        dr1.establecer_estado_atendido()
        self.assertEqual(dr1.status, RequirementDetail.STATUS.ATEN)
        dr2 = baker.make(RequirementDetail, requirement=self.r1, quantity=8, served_quantity=5)
        dr2.establecer_estado_atendido()
        self.assertEqual(dr2.status, RequirementDetail.STATUS.ATEN_PARC)
        dr3 = baker.make(RequirementDetail, requirement=self.r1, quantity=8, served_quantity=10)
        dr3.establecer_estado_atendido()
        self.assertEqual(dr3.status, RequirementDetail.STATUS.ATEN)


class AprobacionRequerimientoTest(TestCase):
    def setUp(self):
        self.r1 = crear_requerimiento(code='')
        self.apr1 = baker.make(RequirementApproval, requirement=self.r1)

    def test_creacion_aprobacion_requerimiento(self):
        self.assertTrue(isinstance(self.apr1, RequirementApproval))
        self.assertEqual(self.apr1.requirement, self.r1)


class ClasificarTest(TestCase):
    """La regla detras de la maquina de estados."""

    def test_sin_avance(self):
        self.assertEqual(classify(0, 10), EMPTY)

    def test_avance_parcial(self):
        self.assertEqual(classify(4, 10), PARTIAL)

    def test_avance_completo(self):
        self.assertEqual(classify(10, 10), COMPLETE)

    def test_avance_por_encima_del_total(self):
        self.assertEqual(classify(12, 10), COMPLETE)


class EstadosDeRequerimientoTest(TestCase):

    def _requirement(self, quantity, cotizada=0, comprada=0, atendida=0):
        requirement = crear_requerimiento(code='')
        baker.make(RequirementDetail, requirement=requirement, line_number=1,
                   quantity=quantity, quoted_quantity=cotizada,
                   purchased_quantity=comprada, served_quantity=atendida)
        return requirement

    def test_comprado_parcial_no_marca_como_comprado(self):
        requirement = self._requirement(quantity=10, comprada=4)

        self.assertEqual(requirement.establecer_estado_comprado(), Requirement.STATUS.COMP_PARC)

    def test_crear_requerimiento_crea_su_aprobacion_inicial(self):
        """Antes fallaba siempre: la aprobacion se creaba antes de que el
        requerimiento tuviera pk."""
        requirement = self._requirement(quantity=10)

        self.assertTrue(RequirementApproval.objects.filter(requirement=requirement).exists())

    def test_comprado_completo(self):
        requirement = self._requirement(quantity=10, comprada=10)

        self.assertEqual(requirement.establecer_estado_comprado(), Requirement.STATUS.COMP)

    def test_comprado_por_encima_del_total(self):
        requirement = self._requirement(quantity=10, comprada=12)

        self.assertEqual(requirement.establecer_estado_comprado(), Requirement.STATUS.COMP)

    def test_cotizado_parcial(self):
        requirement = self._requirement(quantity=10, cotizada=4)

        self.assertEqual(requirement.establecer_estado_cotizado(), Requirement.STATUS.COTIZ_PARC)

    def test_cotizado_completo(self):
        requirement = self._requirement(quantity=10, cotizada=10)

        self.assertEqual(requirement.establecer_estado_cotizado(), Requirement.STATUS.COTIZ)

    def test_atendido_parcial(self):
        requirement = self._requirement(quantity=10, atendida=4)

        self.assertEqual(requirement.establecer_estado_atendido(), Requirement.STATUS.ATEN_PARC)

    def test_atendido_completo(self):
        requirement = self._requirement(quantity=10, atendida=10)

        self.assertEqual(requirement.establecer_estado_atendido(), Requirement.STATUS.ATEN)

    def test_los_totales_se_calculan_una_sola_vez(self):
        """Suma columnas, asi que el agregado es exacto; la maquina de estados los
        invoca varias veces en la misma operacion."""
        requirement = self._requirement(quantity=10)

        with self.assertNumQueries(1):
            self.assertEqual(requirement.total, 10)

        with self.assertNumQueries(1):
            requirement.total_cotizado

        with self.assertNumQueries(1):
            requirement.total_comprado

        with self.assertNumQueries(0):
            requirement.total
            requirement.total_cotizado
            requirement.total_comprado

    def test_el_prefetch_evita_una_consulta_por_requerimiento(self):
        """Los totales recorren el manager inverso y no un .filter(), que siempre
        lanza su propia consulta. Eso es lo que hace que prefetch_related sirva
        en los bucles que cargan muchos requerimientos."""
        for quantity in (10, 20, 30):
            self._requirement(quantity=quantity)

        requerimientos = list(Requirement.objects.prefetch_related('details'))

        with self.assertNumQueries(0):
            for requirement in requerimientos:
                requirement.total
                requirement.total_cotizado
                requirement.total_comprado


class EstadosDeDetalleRequerimientoTest(TestCase):
    """Estos metodos solo leen los campos de la instancia, asi que no hace falta
    tocar la base de datos."""

    def _detalle(self, quantity, cotizada=0, comprada=0, atendida=0):
        return RequirementDetail(quantity=quantity, quoted_quantity=cotizada,
                                    purchased_quantity=comprada, served_quantity=atendida)

    def test_cotizado(self):
        self.assertEqual(self._detalle(10).establecer_estado_cotizado(), RequirementDetail.STATUS.PEND)
        self.assertEqual(self._detalle(10, cotizada=4).establecer_estado_cotizado(),
                         RequirementDetail.STATUS.COTIZ_PARC)
        self.assertEqual(self._detalle(10, cotizada=10).establecer_estado_cotizado(),
                         RequirementDetail.STATUS.COTIZ)

    def test_comprado(self):
        self.assertEqual(self._detalle(10, comprada=4).establecer_estado_comprado(),
                         RequirementDetail.STATUS.COMP_PARC)
        self.assertEqual(self._detalle(10, comprada=10).establecer_estado_comprado(),
                         RequirementDetail.STATUS.COMP)

    def test_atendido(self):
        self.assertEqual(self._detalle(10, atendida=4).establecer_estado_atendido(),
                         RequirementDetail.STATUS.ATEN_PARC)
        self.assertEqual(self._detalle(10, atendida=10).establecer_estado_atendido(),
                         RequirementDetail.STATUS.ATEN)
