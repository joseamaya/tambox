from django.test import TestCase
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from administracion.models import Profession, Worker, Office, Position, ApprovalLevel
from model_bakery import baker
from datetime import date

"""
 class ProfesionTest(TestCase):
    fixtures = ['usuarios.json']

    def test_list_professions_view(self):
        self.client.login(username='test',password='test')
        p = self.crear_profesion()
        url = reverse("administracion:profession_list")
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        
    def test_form(self):
        p = self.crear_profesion()
        data = {'abbreviation': p.abbreviation, 'description': p.description}
        form = ProfessionForm(data = data)
        self.assertTrue(form.is_valid())
        
    def test_invalid_form(self):
        p = self.crear_profesion('Dr.','')
        data = {'abbreviation': p.abbreviation, 'description': p.description}
        form = ProfessionForm(data = data)
        self.assertFalse(form.is_valid())"""


# Create your tests here.
class ProfesionTest(TestCase):

    def setUp(self):
        self.p1 = baker.make(Profession)
        self.p2 = baker.make(Profession)
        self.p3 = baker.make(Profession)

    def test_creation_profession_baker(self):
        self.assertTrue(isinstance(self.p1, Profession))
        self.assertEqual(self.p1.__str__(), self.p1.description)

    def test_next_profession(self):
        self.assertEqual(self.p3.pk, self.p2.next())

    def test_previous_profession(self):
        self.assertEqual(self.p2.pk, self.p3.previous())

    def test_first_profession(self):
        self.assertEqual(self.p1.pk, self.p3.next())

    def test_last_profession(self):
        self.assertEqual(self.p3.pk, self.p1.previous())


class TrabajadorTest(TestCase):

    def setUp(self):
        self.t1 = baker.make(Worker)
        self.t2 = baker.make(Worker)
        self.t3 = baker.make(Worker)

    def test_creation_worker_baker(self):
        self.assertTrue(isinstance(self.t1, Worker))
        self.assertEqual(self.t3.__str__(),
                         self.t3.last_name + ' ' + self.t3.first_name)

    def test_next_worker(self):
        self.assertEqual(self.t3.pk, self.t2.next())

    def test_previous_worker(self):
        self.assertEqual(self.t2.pk, self.t3.previous())

    def test_first_worker(self):
        self.assertEqual(self.t1.pk, self.t3.next())

    def test_last_worker(self):
        self.assertEqual(self.t3.pk, self.t1.previous())

    def test_name_complete(self):
        self.assertEqual(self.t3.full_name(),
                         self.t3.first_name + ' ' + self.t3.last_name)
        p = baker.make(Profession)
        t = baker.make(Worker, profession=p)
        self.assertEqual(t.full_name(),
                         t.profession.abbreviation + ' ' + t.first_name + ' ' + t.last_name)


class OficinaTest(TestCase):

    def setUp(self):
        self.o1 = baker.make(Office)
        self.o2 = baker.make(Office)
        self.o3 = baker.make(Office)

    def test_creation_office_baker(self):
        self.assertTrue(isinstance(self.o1, Office))
        self.assertEqual(self.o1.__str__(), self.o1.name)

    def test_next_office(self):
        self.assertEqual(self.o3, self.o2.next())

    def test_previous_office(self):
        self.assertEqual(self.o2, self.o3.previous())

    def test_first_office(self):
        self.assertEqual(self.o1, self.o3.next())

    def test_last_office(self):
        self.assertEqual(self.o3, self.o1.previous())


class PuestoTest(TestCase):

    def setUp(self):
        self.p1 = baker.make(Position)
        self.p2 = baker.make(Position)
        self.p3 = baker.make(Position)

    def test_creation_profession_baker_1(self):
        self.assertTrue(isinstance(self.p1, Position))
        # self.assertEqual(self.p1.__str__(), self.p1.description)

    def test_next_position(self):
        self.assertEqual(self.p3.pk, self.p2.next())

    def test_previous_position(self):
        self.assertEqual(self.p2.pk, self.p3.previous())

    def test_first_position(self):
        self.assertEqual(self.p1.pk, self.p3.next())

    def test_last_position(self):
        self.assertEqual(self.p3.pk, self.p1.previous())

    def test_status_position(self):
        p = baker.make(Position, end_date=date.today())
        self.assertTrue(self.p1.is_active)
        self.assertFalse(p.is_active)


class EstablecerNivelTest(TestCase):
    """Sin los niveles semilla, registrar un requerimiento fallaba con un
    DoesNotExist sin contexto. Ahora dice cual falta."""

    def test_level_missing_gives_message_claro(self):
        office = baker.make(Office)
        position = baker.make(Position, office=office, worker=baker.make(Worker), end_date=None)

        with self.assertRaisesMessage(ValidationError, 'Falta el nivel de aprobacion "USUARIO"'):
            position.set_level(office)

    def test_uses_level_existing(self):
        level = baker.make(ApprovalLevel, description='USUARIO')
        office = baker.make(Office)
        position = baker.make(Position, office=office, worker=baker.make(Worker), end_date=None)

        self.assertEqual(position.set_level(office), level)


class TableroAdministracionTest(TestCase):
    """Las semillas se creaban solo con la tabla vacia (`count() == 0`), asi que
    un estado a medias —LOGISTICA presente y USUARIO ausente— no se arreglaba
    nunca y `set_level()` fallaba para todos los requerimientos."""

    def setUp(self):
        self.client.force_login(User.objects.create_superuser('boss', 'boss@example.com', 'key-segura'))

    def test_complete_levels_that_missing(self):
        ApprovalLevel.objects.create(description='LOGISTICA')

        respuesta = self.client.get('/administracion/dashboard/')

        self.assertEqual(respuesta.status_code, 200)
        usuario = ApprovalLevel.objects.get(description='USUARIO')
        self.assertEqual(usuario.superior_level.description, 'LOGISTICA')

    def test_creates_office_management(self):
        respuesta = self.client.get('/administracion/dashboard/')

        self.assertEqual(respuesta.status_code, 200)
        self.assertTrue(Office.objects.filter(code='GGEN', is_management=True).exists())

    def test_not_duplicates_that_exists(self):
        Office.objects.create(code='GGEN', name='GERENCIA GENERAL', is_management=True)
        ApprovalLevel.objects.create(description='LOGISTICA')

        self.client.get('/administracion/dashboard/')
        self.client.get('/administracion/dashboard/')

        self.assertEqual(Office.objects.filter(code='GGEN').count(), 1)
        self.assertEqual(ApprovalLevel.objects.filter(description='LOGISTICA').count(), 1)
        self.assertEqual(ApprovalLevel.objects.filter(description='USUARIO').count(), 1)
