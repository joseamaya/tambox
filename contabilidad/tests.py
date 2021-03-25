from model_mommy import mommy
from django.test import TestCase
from contabilidad.models import CuentaContable, FormaPago, TipoDocumento, Tipo, \
    Impuesto, Empresa, TipoExistencia


# Create your tests here.
class TestCuentaContable(TestCase):

    def setUp(self):
        self.c1 = mommy.make(CuentaContable)
        self.c2 = mommy.make(CuentaContable)
        self.c3 = mommy.make(CuentaContable)

    def test_creacion_cuenta_contable(self):
        self.assertTrue(isinstance(self.c1, CuentaContable))
        self.assertEqual(self.c1.__str__(), self.c1.cuenta)

    def test_siguiente_profesion(self):
        self.assertEqual(self.c2.pk, self.c1.siguiente())
        self.assertEqual(self.c3.pk, self.c2.siguiente())

    def test_anterior_profesion(self):
        self.assertEqual(self.c1.pk, self.c2.anterior())
        self.assertEqual(self.c2.pk, self.c3.anterior())

    def test_primera_profesion(self):
        self.assertEqual(self.c1.pk, self.c3.siguiente())

    def test_ultima_profesion(self):
        self.assertEqual(self.c3.pk, self.c1.anterior())


class TestFormaPago(TestCase):

    def setUp(self):
        self.fp1 = mommy.make(FormaPago)
        self.fp2 = mommy.make(FormaPago)
        self.fp3 = mommy.make(FormaPago)

    def test_creacion_forma_pago(self):
        self.assertTrue(isinstance(self.fp1, FormaPago))
        self.assertEqual(self.fp1.__str__(), self.fp1.descripcion)

    def test_siguiente_forma_pago(self):
        self.assertEqual(self.fp2.pk, self.fp1.siguiente())
        self.assertEqual(self.fp3.pk, self.fp2.siguiente())

    def test_anterior_forma_pago(self):
        self.assertEqual(self.fp1.pk, self.fp2.anterior())
        self.assertEqual(self.fp2.pk, self.fp3.anterior())

    def test_primera_forma_pago(self):
        self.assertEqual(self.fp1.pk, self.fp3.siguiente())

    def test_ultima_forma_pago(self):
        self.assertEqual(self.fp3.pk, self.fp1.anterior())


class TestTipoDocumento(TestCase):

    def setUp(self):
        self.td1 = mommy.make(TipoDocumento)
        self.td2 = mommy.make(TipoDocumento)
        self.td3 = mommy.make(TipoDocumento)

    def test_creacion_tipo_documento(self):
        self.assertTrue(isinstance(self.td1, TipoDocumento))
        self.assertEqual(self.td1.__str__(), self.td1.nombre)

    def test_siguiente_tipo_documento(self):
        self.assertEqual(self.td2.pk, self.td1.siguiente())
        self.assertEqual(self.td3.pk, self.td2.siguiente())

    def test_anterior_tipo_documento(self):
        self.assertEqual(self.td1.pk, self.td2.anterior())
        self.assertEqual(self.td2.pk, self.td3.anterior())

    def test_primera_tipo_documento(self):
        self.assertEqual(self.td1.pk, self.td3.siguiente())

    def test_ultima_tipo_documento(self):
        self.assertEqual(self.td3.pk, self.td1.anterior())


class TestTipo(TestCase):

    def setUp(self):
        self.t1 = mommy.make(Tipo)

    def test_creacion_tipo_documento(self):
        self.assertTrue(isinstance(self.t1, Tipo))
        self.assertEqual(self.t1.__str__(), self.t1.descripcion_valor)


class TestImpuesto(TestCase):

    def setUp(self):
        self.imp1 = mommy.make(Impuesto)
        self.imp2 = mommy.make(Impuesto)
        self.imp3 = mommy.make(Impuesto)

    def test_creacion_impuesto(self):
        self.assertTrue(isinstance(self.imp1, Impuesto))
        self.assertEqual(self.imp1.__str__(), self.imp1.descripcion)

    def test_siguiente_impuesto(self):
        self.assertEqual(self.imp2.pk, self.imp1.siguiente())
        self.assertEqual(self.imp3.pk, self.imp2.siguiente())

    def test_anterior_impuesto(self):
        self.assertEqual(self.imp1.pk, self.imp2.anterior())
        self.assertEqual(self.imp2.pk, self.imp3.anterior())

    def test_primer_impuesto(self):
        self.assertEqual(self.imp1.pk, self.imp3.siguiente())

    def test_ultimo_impuesto(self):
        self.assertEqual(self.imp3.pk, self.imp1.anterior())


class TestEmpresa(TestCase):

    def setUp(self):
        self.emp1 = mommy.make(Empresa)
        self.emp2 = mommy.make(Empresa)

    def test_creacion_empresa(self):
        self.assertTrue(isinstance(self.emp1, Empresa))
        self.assertEqual(self.emp1.__str__(), self.emp1.razon_social)

    def test_patron_singleton(self):
        self.assertEqual(self.emp1, self.emp2)

    def test_direccion_empresa(self):
        direccion = self.emp1.lugar + ' ' + self.emp1.calle + ' ' + self.emp1.distrito
        self.assertEqual(direccion, self.emp1.direccion())


class TestTipoExistencia(TestCase):

    def setUp(self):
        self.te1 = mommy.make(TipoExistencia)

    def test_creacion_tipo_existencia(self):
        self.assertEqual(self.te1.__str__(), self.te1.descripcion)
