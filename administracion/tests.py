from django.test import TestCase
from administracion.models import Profesion, Trabajador, Oficina, Puesto
from django.core.urlresolvers import reverse
from administracion.forms import ProfesionForm
from model_mommy import mommy
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
        data = {'abreviatura': p.abreviatura, 'descripcion': p.descripcion}
        form = ProfesionForm(data = data)
        self.assertTrue(form.is_valid())
        
    def test_invalid_form(self):
        p = self.crear_profesion('Dr.','')
        data = {'abreviatura': p.abreviatura, 'descripcion': p.descripcion}
        form = ProfesionForm(data = data)
        self.assertFalse(form.is_valid())"""


# Create your tests here.
class ProfesionTest(TestCase):
    def setUp(self):
        self.p1 = mommy.make(Profesion)
        self.p2 = mommy.make(Profesion)
        self.p3 = mommy.make(Profesion)

    def test_creacion_profesion_mommy(self):
        self.assertTrue(isinstance(self.p1, Profesion))
        self.assertEqual(self.p1.__str__(), self.p1.descripcion)

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
        self.t1 = mommy.make(Trabajador)
        self.t2 = mommy.make(Trabajador)
        self.t3 = mommy.make(Trabajador)

    def test_creacion_trabajador_mommy(self):
        self.assertTrue(isinstance(self.t1, Trabajador))
        self.assertEqual(self.t3.__str__(),
                         self.t3.apellido_paterno + ' ' + self.t3.apellido_materno + ' ' + self.t3.nombres)

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
                         self.t3.nombres + ' ' + self.t3.apellido_paterno + ' ' + self.t3.apellido_materno)
        p = mommy.make(Profesion)
        t = mommy.make(Trabajador, profesion=p)
        self.assertEqual(t.nombre_completo(),
                         t.profesion.abreviatura + ' ' + t.nombres + ' ' + t.apellido_paterno + ' ' + t.apellido_materno)


class OficinaTest(TestCase):
    def setUp(self):
        self.o1 = mommy.make(Oficina)
        self.o2 = mommy.make(Oficina)
        self.o3 = mommy.make(Oficina)

    def test_creacion_oficina_mommy(self):
        self.assertTrue(isinstance(self.o1, Oficina))
        self.assertEqual(self.o1.__str__(), self.o1.nombre)

    def test_siguiente_oficina(self):
        self.assertEqual(self.o3.pk, self.o2.siguiente())

    def test_anterior_oficina(self):
        self.assertEqual(self.o2.pk, self.o3.anterior())

    def test_primera_oficina(self):
        self.assertEqual(self.o1.pk, self.o3.siguiente())

    def test_ultima_oficina(self):
        self.assertEqual(self.o3.pk, self.o1.anterior())


class PuestoTest(TestCase):
    def setUp(self):
        self.p1 = mommy.make(Puesto)
        self.p2 = mommy.make(Puesto)
        self.p3 = mommy.make(Puesto)

    def test_creacion_profesion_mommy(self):
        self.assertTrue(isinstance(self.p1, Puesto))
        # self.assertEqual(self.p1.__str__(), self.p1.descripcion)

    def test_siguiente_puesto(self):
        self.assertEqual(self.p3.pk, self.p2.siguiente())

    def test_anterior_puesto(self):
        self.assertEqual(self.p2.pk, self.p3.anterior())

    def test_primer_puesto(self):
        self.assertEqual(self.p1.pk, self.p3.siguiente())

    def test_ultimo_puesto(self):
        self.assertEqual(self.p3.pk, self.p1.anterior())

    def test_estado_puesto(self):
        p = mommy.make(Puesto, fecha_fin=date.today())
        self.assertTrue(self.p1.estado)
        self.assertFalse(p.estado)
