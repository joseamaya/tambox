from django.test import TestCase
from model_bakery import baker
from administration.models import ApprovalLevel, Office, Position, Worker
from requirements.models import Requirement, RequirementDetail,\
    RequirementApproval
from tambox.statuses import classify, COMPLETE, PARTIAL, EMPTY


def create_requirement(**kwargs):
    """Un requerimiento necesita que su solicitante tenga puesto asignado:
    `save()` lanza ValidationError si no lo tiene, porque de ahi sale la oficina
    y la cadena de aprobaciones. Los tests viejos no armaban ese grafo."""
    ApprovalLevel.objects.get_or_create(description='USUARIO')
    office = baker.make(Office)
    worker = baker.make(Worker)
    baker.make(Position, office=office, worker=worker, end_date=None)
    return baker.make(Requirement, requester=worker, office=office, **kwargs)


# Create your tests here.
class RequirementTest(TestCase):
    def setUp(self):
        self.r1 = create_requirement(code='')
        self.r2 = create_requirement(code='')
        self.r3 = create_requirement(code='')

    def test_creation_requirement(self):
        self.assertTrue(isinstance(self.r1, Requirement))
        self.assertEqual(self.r1.__str__(), self.r1.code)

    def test_next_requirement(self):
        self.assertEqual(self.r2, self.r1.next())
        self.assertEqual(self.r3, self.r2.next())

    def test_previous_requirement(self):
        self.assertEqual(self.r1, self.r2.previous())
        self.assertEqual(self.r2, self.r3.previous())

    def test_first_requirement(self):
        self.assertEqual(self.r1, self.r3.next())

    def test_last_requirement(self):
        self.assertEqual(self.r3, self.r1.previous())

    def test_update_requirement(self):
        """`save()` solo genera el code cuando esta vacio, asi que guardar un
        requerimiento existente no lo duplica ni le cambia el code."""
        code = self.r1.code
        quantity = Requirement.objects.count()

        self.r1.save()

        self.assertEqual(code, Requirement.objects.get(pk=self.r1.pk).code)
        self.assertEqual(quantity, Requirement.objects.count())


class RequirementDetailTest(TestCase):
    def setUp(self):
        self.r1 = create_requirement(code='')

    def test_creation_detail_requirement(self):
        dr1 = baker.make(RequirementDetail, requirement=self.r1)
        self.assertTrue(isinstance(dr1, RequirementDetail))
        self.assertEqual(dr1.__str__(), self.r1.code + ' ' + str(dr1.line_number))

    def test_status_served(self):
        dr1 = baker.make(RequirementDetail, requirement=self.r1, quantity=5, served_quantity=5)
        dr1.set_status_served()
        self.assertEqual(dr1.status, RequirementDetail.STATUS.ATEN)
        dr2 = baker.make(RequirementDetail, requirement=self.r1, quantity=8, served_quantity=5)
        dr2.set_status_served()
        self.assertEqual(dr2.status, RequirementDetail.STATUS.ATEN_PARC)
        dr3 = baker.make(RequirementDetail, requirement=self.r1, quantity=8, served_quantity=10)
        dr3.set_status_served()
        self.assertEqual(dr3.status, RequirementDetail.STATUS.ATEN)


class RequirementApprovalTest(TestCase):
    def setUp(self):
        self.r1 = create_requirement(code='')
        self.apr1 = baker.make(RequirementApproval, requirement=self.r1)

    def test_creation_approval_requirement(self):
        self.assertTrue(isinstance(self.apr1, RequirementApproval))
        self.assertEqual(self.apr1.requirement, self.r1)


class ClassifyTest(TestCase):
    """La regla detras de la maquina de estados."""

    def test_without_progress(self):
        self.assertEqual(classify(0, 10), EMPTY)

    def test_progress_partial(self):
        self.assertEqual(classify(4, 10), PARTIAL)

    def test_progress_complete(self):
        self.assertEqual(classify(10, 10), COMPLETE)

    def test_progress_by_above_total(self):
        self.assertEqual(classify(12, 10), COMPLETE)


class RequirementStatusesTest(TestCase):

    def _requirement(self, quantity, quoted=0, purchased=0, served=0):
        requirement = create_requirement(code='')
        baker.make(RequirementDetail, requirement=requirement, line_number=1,
                   quantity=quantity, quoted_quantity=quoted,
                   purchased_quantity=purchased, served_quantity=served)
        return requirement

    def test_purchased_partial_not_marks_as_purchased(self):
        requirement = self._requirement(quantity=10, purchased=4)

        self.assertEqual(requirement.set_status_purchased(), Requirement.STATUS.COMP_PARC)

    def test_create_requirement_creates_approval_initial(self):
        """Antes fallaba siempre: la aprobacion se creaba antes de que el
        requerimiento tuviera pk."""
        requirement = self._requirement(quantity=10)

        self.assertTrue(RequirementApproval.objects.filter(requirement=requirement).exists())

    def test_purchased_complete(self):
        requirement = self._requirement(quantity=10, purchased=10)

        self.assertEqual(requirement.set_status_purchased(), Requirement.STATUS.COMP)

    def test_purchased_by_above_total(self):
        requirement = self._requirement(quantity=10, purchased=12)

        self.assertEqual(requirement.set_status_purchased(), Requirement.STATUS.COMP)

    def test_quoted_partial(self):
        requirement = self._requirement(quantity=10, quoted=4)

        self.assertEqual(requirement.set_status_quoted(), Requirement.STATUS.COTIZ_PARC)

    def test_quoted_complete(self):
        requirement = self._requirement(quantity=10, quoted=10)

        self.assertEqual(requirement.set_status_quoted(), Requirement.STATUS.COTIZ)

    def test_served_partial(self):
        requirement = self._requirement(quantity=10, served=4)

        self.assertEqual(requirement.set_status_served(), Requirement.STATUS.ATEN_PARC)

    def test_served_complete(self):
        requirement = self._requirement(quantity=10, served=10)

        self.assertEqual(requirement.set_status_served(), Requirement.STATUS.ATEN)

    def test_totals_calculate_only_time(self):
        """Suma columnas, asi que el agregado es exacto; la maquina de estados los
        invoca varias veces en la misma operacion."""
        requirement = self._requirement(quantity=10)

        with self.assertNumQueries(1):
            self.assertEqual(requirement.total, 10)

        with self.assertNumQueries(1):
            requirement.total_quoted

        with self.assertNumQueries(1):
            requirement.total_purchased

        with self.assertNumQueries(0):
            requirement.total
            requirement.total_quoted
            requirement.total_purchased

    def test_prefetch_avoids_query_by_requirement(self):
        """Los totales recorren el manager inverso y no un .filter(), que siempre
        lanza su propia consulta. Eso es lo que hace que prefetch_related sirva
        en los bucles que cargan muchos requerimientos."""
        for quantity in (10, 20, 30):
            self._requirement(quantity=quantity)

        requirements = list(Requirement.objects.prefetch_related('details'))

        with self.assertNumQueries(0):
            for requirement in requirements:
                requirement.total
                requirement.total_quoted
                requirement.total_purchased


class RequirementDetailStatusesTest(TestCase):
    """Estos metodos solo leen los campos de la instance, asi que no hace falta
    tocar la base de datos."""

    def _detail(self, quantity, quoted=0, purchased=0, served=0):
        return RequirementDetail(quantity=quantity, quoted_quantity=quoted,
                                    purchased_quantity=purchased, served_quantity=served)

    def test_quoted(self):
        self.assertEqual(self._detail(10).set_status_quoted(), RequirementDetail.STATUS.PEND)
        self.assertEqual(self._detail(10, quoted=4).set_status_quoted(),
                         RequirementDetail.STATUS.COTIZ_PARC)
        self.assertEqual(self._detail(10, quoted=10).set_status_quoted(),
                         RequirementDetail.STATUS.COTIZ)

    def test_purchased(self):
        self.assertEqual(self._detail(10, purchased=4).set_status_purchased(),
                         RequirementDetail.STATUS.COMP_PARC)
        self.assertEqual(self._detail(10, purchased=10).set_status_purchased(),
                         RequirementDetail.STATUS.COMP)

    def test_served(self):
        self.assertEqual(self._detail(10, served=4).set_status_served(),
                         RequirementDetail.STATUS.ATEN_PARC)
        self.assertEqual(self._detail(10, served=10).set_status_served(),
                         RequirementDetail.STATUS.ATEN)


class RequirementReportTest(TestCase):
    """Genera el PDF del requerimiento. Arma sus tablas recorriendo el grafo de
    detalles y firmas, y `manage.py check` no ejecuta esos cuerpos."""

    def setUp(self):
        from datetime import date

        from tambox.config import clear_cache

        logistics = baker.make(Office)
        baker.make('accounting.Configuration', administration=logistics,
                   logistics=logistics, budget=logistics)
        baker.make(Position, office=logistics, worker=baker.make(Worker),
                   is_leadership=True, start_date=date(2020, 1, 1), end_date=None)
        clear_cache()
        self.addCleanup(clear_cache)

    def test_generates_pdf(self):
        from requirements.reports import RequirementReport

        requirement = create_requirement(code='')
        baker.make(RequirementDetail, requirement=requirement,
                   product=baker.make('products.Product'), quantity=3,
                   use='USO GENERAL')

        contenido = RequirementReport('A4', requirement).render()

        self.assertTrue(contenido.startswith(b'%PDF'))
