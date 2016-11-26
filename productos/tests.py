from django.test import TestCase
from django.contrib.auth.models import User
from model_mommy import mommy
from productos.models import UnidadMedida, GrupoProductos, Producto

# Create your tests here.
"""class NewUnidadMedidaTestCase(TestCase):
    fixtures = ['usuarios.json','unidadesmedida.json']
    
    def test_index(self):
        resp = self.client.get("/")
        self.assertEqual(resp.status_code,200)
        
    def test_new_unidad_medida_view(self):
        self.client.login(username='test',password='test')
        resp = self.client.get('/productos/crear_unidad_medida/')
        self.assertEqual(200,resp.status_code)"""


class UnidadMedidaTest(TestCase):
    def setUp(self):
        self.um1 = mommy.make(UnidadMedida)
        self.um2 = mommy.make(UnidadMedida)
        self.um3 = mommy.make(UnidadMedida)

    def test_creacion_unidad_medida(self):
        self.assertTrue(isinstance(self.um1, UnidadMedida))
        self.assertEqual(self.um1.__str__(), self.um1.descripcion)

    def test_siguiente_unidad_medida(self):
        self.assertEqual(self.um3.pk, self.um2.siguiente())

    def test_anterior_unidad_medida(self):
        self.assertEqual(self.um2.pk, self.um3.anterior())

    def test_primera_unidad_medida(self):
        self.assertEqual(self.um1.pk, self.um3.siguiente())

    def test_ultima_unidad_medida(self):
        self.assertEqual(self.um3.pk, self.um1.anterior())


class GrupoProductosTest(TestCase):
    def setUp(self):
        self.gp1 = mommy.make(GrupoProductos, codigo='')
        self.gp2 = mommy.make(GrupoProductos, codigo='')
        self.gp3 = mommy.make(GrupoProductos, codigo='')

    def test_creacion_grupo_productos(self):
        self.assertTrue(isinstance(self.gp1, GrupoProductos))
        self.assertEqual("1".zfill(6), self.gp1.codigo)
        self.assertEqual(self.gp1.__str__(), self.gp1.descripcion)

    def test_siguiente_grupo_productos(self):
        self.assertEqual(self.gp2.pk, self.gp1.siguiente())
        self.assertEqual(self.gp3.pk, self.gp2.siguiente())

    def test_anterior_grupo_productos(self):
        self.assertEqual(self.gp1.pk, self.gp2.anterior())
        self.assertEqual(self.gp2.pk, self.gp3.anterior())

    def test_primer_grupo_productos(self):
        self.assertEqual(self.gp1.pk, self.gp3.siguiente())

    def test_ultimo_grupo_productos(self):
        self.assertEqual(self.gp3.pk, self.gp1.anterior())


class ProductoTest(TestCase):
    def setUp(self):
        self.gp1 = mommy.make(GrupoProductos, codigo='')
        self.gp2 = mommy.make(GrupoProductos, codigo='')
        self.p1 = mommy.make(Producto, codigo='', grupo_productos=self.gp1)
        self.p2 = mommy.make(Producto, codigo='', grupo_productos=self.gp1)
        self.p3 = mommy.make(Producto, codigo='', grupo_productos=self.gp2, es_servicio=True)

    def test_creacion_producto(self):
        self.assertTrue(isinstance(self.p1, Producto))
        self.assertEqual(self.gp1.codigo + "1".zfill(4), self.p1.codigo)
        self.assertEqual(self.gp1.codigo + "2".zfill(4), self.p2.codigo)
        self.assertEqual(self.p1.__str__(), self.p1.descripcion)

    def test_siguiente_producto(self):
        self.assertEqual(self.p2.pk, self.p1.siguiente())
        self.assertEqual(self.p3.pk, self.p2.siguiente())

    def test_anterior_producto(self):
        self.assertEqual(self.p1.pk, self.p2.anterior())
        self.assertEqual(self.p2.pk, self.p3.anterior())

    def test_primer_producto(self):
        self.assertEqual(self.p1.pk, self.p3.siguiente())

    def test_ultimo_producto(self):
        self.assertEqual(self.p3.pk, self.p1.anterior())

    def test_creacion_servicio(self):
        self.assertEqual(self.p3.unidad_medida.codigo, 'SERV')
