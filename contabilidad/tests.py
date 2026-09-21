from model_bakery import baker
from django.test import TestCase
from contabilidad.models import Account, PaymentMethod, DocumentType, Type, \
    Tax, Company, StockType


# Create your tests here.
class TestCuentaContable(TestCase):

    def setUp(self):
        self.c1 = baker.make(Account)
        self.c2 = baker.make(Account)
        self.c3 = baker.make(Account)

    def test_creacion_cuenta_contable(self):
        self.assertTrue(isinstance(self.c1, Account))
        self.assertEqual(self.c1.__str__(), self.c1.account_number)

    def test_siguiente_profesion(self):
        self.assertEqual(self.c2.pk, self.c1.next())
        self.assertEqual(self.c3.pk, self.c2.next())

    def test_anterior_profesion(self):
        self.assertEqual(self.c1.pk, self.c2.previous())
        self.assertEqual(self.c2.pk, self.c3.previous())

    def test_primera_profesion(self):
        self.assertEqual(self.c1.pk, self.c3.next())

    def test_ultima_profesion(self):
        self.assertEqual(self.c3.pk, self.c1.previous())


class TestFormaPago(TestCase):

    def setUp(self):
        self.fp1 = baker.make(PaymentMethod)
        self.fp2 = baker.make(PaymentMethod)
        self.fp3 = baker.make(PaymentMethod)

    def test_creacion_forma_pago(self):
        self.assertTrue(isinstance(self.fp1, PaymentMethod))
        self.assertEqual(self.fp1.__str__(), self.fp1.description)

    def test_siguiente_forma_pago(self):
        self.assertEqual(self.fp2.pk, self.fp1.next())
        self.assertEqual(self.fp3.pk, self.fp2.next())

    def test_anterior_forma_pago(self):
        self.assertEqual(self.fp1.pk, self.fp2.previous())
        self.assertEqual(self.fp2.pk, self.fp3.previous())

    def test_primera_forma_pago(self):
        self.assertEqual(self.fp1.pk, self.fp3.next())

    def test_ultima_forma_pago(self):
        self.assertEqual(self.fp3.pk, self.fp1.previous())


class TestTipoDocumento(TestCase):

    def setUp(self):
        self.td1 = baker.make(DocumentType)
        self.td2 = baker.make(DocumentType)
        self.td3 = baker.make(DocumentType)

    def test_creacion_tipo_documento(self):
        self.assertTrue(isinstance(self.td1, DocumentType))
        self.assertEqual(self.td1.__str__(), self.td1.name)

    def test_siguiente_tipo_documento(self):
        self.assertEqual(self.td2.pk, self.td1.next())
        self.assertEqual(self.td3.pk, self.td2.next())

    def test_anterior_tipo_documento(self):
        self.assertEqual(self.td1.pk, self.td2.previous())
        self.assertEqual(self.td2.pk, self.td3.previous())

    def test_primera_tipo_documento(self):
        self.assertEqual(self.td1.pk, self.td3.next())

    def test_ultima_tipo_documento(self):
        self.assertEqual(self.td3.pk, self.td1.previous())


class TestTipo(TestCase):

    def setUp(self):
        self.t1 = baker.make(Type)

    def test_creacion_tipo_documento(self):
        self.assertTrue(isinstance(self.t1, Type))
        self.assertEqual(self.t1.__str__(), self.t1.value_description)


class TestImpuesto(TestCase):

    def setUp(self):
        self.imp1 = baker.make(Tax)
        self.imp2 = baker.make(Tax)
        self.imp3 = baker.make(Tax)

    def test_creacion_impuesto(self):
        self.assertTrue(isinstance(self.imp1, Tax))
        self.assertEqual(self.imp1.__str__(), self.imp1.description)

    def test_siguiente_impuesto(self):
        self.assertEqual(self.imp2.pk, self.imp1.next())
        self.assertEqual(self.imp3.pk, self.imp2.next())

    def test_anterior_impuesto(self):
        self.assertEqual(self.imp1.pk, self.imp2.previous())
        self.assertEqual(self.imp2.pk, self.imp3.previous())

    def test_primer_impuesto(self):
        self.assertEqual(self.imp1.pk, self.imp3.next())

    def test_ultimo_impuesto(self):
        self.assertEqual(self.imp3.pk, self.imp1.previous())


class TestEmpresa(TestCase):

    def setUp(self):
        self.emp1 = baker.make(Company)
        self.emp2 = baker.make(Company)

    def test_creacion_empresa(self):
        self.assertTrue(isinstance(self.emp1, Company))
        self.assertEqual(self.emp1.__str__(), self.emp1.business_name)

    def test_patron_singleton(self):
        self.assertEqual(self.emp1, self.emp2)

    def test_direccion_empresa(self):
        address = self.emp1.place + ' ' + self.emp1.street + ' ' + self.emp1.district
        self.assertEqual(address, self.emp1.address())


class TestTipoExistencia(TestCase):

    def setUp(self):
        self.te1 = baker.make(StockType)

    def test_creacion_tipo_existencia(self):
        self.assertEqual(self.te1.__str__(), self.te1.description)
