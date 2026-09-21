from django.test import TestCase
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from administracion.models import Profesion, Trabajador, Oficina, Puesto, NivelAprobacion
from model_bakery import baker
from datetime import date

"""
 class ProfesionTest(TestCase):
    fixtures = ['usuarios.json']

    def test_listado_profesiones_view(self):
        self.client.login(username='test',password='test')
        p = self.crear_profesion()
        url = reverse("administracion:maestro_profesiones")
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        
    def test_valid_form(self):
        p = self.crear_profesion()
        data = {'abbreviation': p.abbreviation, 'description': p.description}
        form = ProfesionForm(data = data)
        self.assertTrue(form.is_valid())
        
    def test_invalid_form(self):
        p = self.crear_profesion('Dr.','')
        data = {'abbreviation': p.abbreviation, 'description': p.description}
        form = ProfesionForm(data = data)
        self.assertFalse(form.is_valid())"""


# Create your tests here.
class ProfesionTest(TestCase):

    def setUp(self):
        self.p1 = baker.make(Profesion)
        self.p2 = baker.make(Profesion)
        self.p3 = baker.make(Profesion)

    def test_creacion_profesion_mommy(self):
        self.assertTrue(isinstance(self.p1, Profesion))
        self.assertEqual(self.p1.__str__(), self.p1.description)

    def test_siguiente_profesion(self):
        self.assertEqual(self.p3.pk, self.p2.siguiente())

    def test_anterior_profesion(self):
        self.assertEqual(self.p2.pk, self.p3.anterior())

    def test_primera_profesion(self):
        self.assertEqual(self.p1.pk, self.p3.siguiente())

    def test_ultima_profesion(self):
        self.assertEqual(self.p3.pk, self.p1.anterior())


class TrabajadorTest(TestCase):

    def setUp(self):
        self.t1 = baker.make(Trabajador)
        self.t2 = baker.make(Trabajador)
        self.t3 = baker.make(Trabajador)

    def test_creacion_trabajador_mommy(self):
        self.assertTrue(isinstance(self.t1, Trabajador))
        self.assertEqual(self.t3.__str__(),
                         self.t3.last_name + ' ' + self.t3.first_name)

    def test_siguiente_trabajador(self):
        self.assertEqual(self.t3.pk, self.t2.siguiente())

    def test_anterior_trabajador(self):
        self.assertEqual(self.t2.pk, self.t3.anterior())

    def test_primer_trabajador(self):
        self.assertEqual(self.t1.pk, self.t3.siguiente())

    def test_ultimo_trabajador(self):
        self.assertEqual(self.t3.pk, self.t1.anterior())

    def test_nombre_completo(self):
        self.assertEqual(self.t3.nombre_completo(),
                         self.t3.first_name + ' ' + self.t3.last_name)
        p = baker.make(Profesion)
        t = baker.make(Trabajador, profession=p)
        self.assertEqual(t.nombre_completo(),
                         t.profession.abbreviation + ' ' + t.first_name + ' ' + t.last_name)


class OficinaTest(TestCase):

    def setUp(self):
        self.o1 = baker.make(Oficina)
        self.o2 = baker.make(Oficina)
        self.o3 = baker.make(Oficina)

    def test_creacion_oficina_mommy(self):
        self.assertTrue(isinstance(self.o1, Oficina))
        self.assertEqual(self.o1.__str__(), self.o1.name)

    def test_siguiente_oficina(self):
        self.assertEqual(self.o3, self.o2.siguiente())

    def test_anterior_oficina(self):
        self.assertEqual(self.o2, self.o3.anterior())

    def test_primera_oficina(self):
        self.assertEqual(self.o1, self.o3.siguiente())

    def test_ultima_oficina(self):
        self.assertEqual(self.o3, self.o1.anterior())


class PuestoTest(TestCase):

    def setUp(self):
        self.p1 = baker.make(Puesto)
        self.p2 = baker.make(Puesto)
        self.p3 = baker.make(Puesto)

    def test_creacion_profesion_mommy(self):
        self.assertTrue(isinstance(self.p1, Puesto))
        # self.assertEqual(self.p1.__str__(), self.p1.description)

    def test_siguiente_puesto(self):
        self.assertEqual(self.p3.pk, self.p2.siguiente())

    def test_anterior_puesto(self):
        self.assertEqual(self.p2.pk, self.p3.anterior())

    def test_primer_puesto(self):
        self.assertEqual(self.p1.pk, self.p3.siguiente())

    def test_ultimo_puesto(self):
        self.assertEqual(self.p3.pk, self.p1.anterior())

    def test_estado_puesto(self):
        p = baker.make(Puesto, end_date=date.today())
        self.assertTrue(self.p1.is_active)
        self.assertFalse(p.is_active)


class EstablecerNivelTest(TestCase):
    """Sin los niveles semilla, registrar un requerimiento fallaba con un
    DoesNotExist sin contexto. Ahora dice cual falta."""

    def test_nivel_ausente_da_un_mensaje_claro(self):
        office = baker.make(Oficina)
        puesto = baker.make(Puesto, office=office, worker=baker.make(Trabajador), end_date=None)

        with self.assertRaisesMessage(ValidationError, 'Falta el nivel de aprobacion "USUARIO"'):
            puesto.establecer_nivel(office)

    def test_usa_el_nivel_existente(self):
        level = baker.make(NivelAprobacion, description='USUARIO')
        office = baker.make(Oficina)
        puesto = baker.make(Puesto, office=office, worker=baker.make(Trabajador), end_date=None)

        self.assertEqual(puesto.establecer_nivel(office), level)


class TableroAdministracionTest(TestCase):
    """Las semillas se creaban solo con la tabla vacia (`count() == 0`), asi que
    un estado a medias —LOGISTICA presente y USUARIO ausente— no se arreglaba
    nunca y `establecer_nivel()` fallaba para todos los requerimientos."""

    def setUp(self):
        self.client.force_login(User.objects.create_superuser('jefe', 'jefe@example.com', 'clave-segura'))

    def test_completa_los_niveles_que_faltan(self):
        NivelAprobacion.objects.create(description='LOGISTICA')

        respuesta = self.client.get('/administracion/tablero/')

        self.assertEqual(respuesta.status_code, 200)
        usuario = NivelAprobacion.objects.get(description='USUARIO')
        self.assertEqual(usuario.superior_level.description, 'LOGISTICA')

    def test_crea_la_oficina_de_gerencia(self):
        respuesta = self.client.get('/administracion/tablero/')

        self.assertEqual(respuesta.status_code, 200)
        self.assertTrue(Oficina.objects.filter(code='GGEN', is_management=True).exists())

    def test_no_duplica_lo_que_ya_existe(self):
        Oficina.objects.create(code='GGEN', name='GERENCIA GENERAL', is_management=True)
        NivelAprobacion.objects.create(description='LOGISTICA')

        self.client.get('/administracion/tablero/')
        self.client.get('/administracion/tablero/')

        self.assertEqual(Oficina.objects.filter(code='GGEN').count(), 1)
        self.assertEqual(NivelAprobacion.objects.filter(description='LOGISTICA').count(), 1)
        self.assertEqual(NivelAprobacion.objects.filter(description='USUARIO').count(), 1)
