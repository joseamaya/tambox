from model_bakery import baker
from django.test import TestCase
from accounting.models import Account, PaymentMethod, DocumentType, Type, \
    Tax, Company, StockType


# Create your tests here.
class AccountTest(TestCase):

    def setUp(self):
        self.c1 = baker.make(Account)
        self.c2 = baker.make(Account)
        self.c3 = baker.make(Account)

    def test_creation_account(self):
        self.assertTrue(isinstance(self.c1, Account))
        self.assertEqual(self.c1.__str__(), self.c1.account_number)

    def test_next_profession(self):
        self.assertEqual(self.c2.pk, self.c1.next())
        self.assertEqual(self.c3.pk, self.c2.next())

    def test_previous_profession(self):
        self.assertEqual(self.c1.pk, self.c2.previous())
        self.assertEqual(self.c2.pk, self.c3.previous())

    def test_first_profession(self):
        self.assertEqual(self.c1.pk, self.c3.next())

    def test_last_profession(self):
        self.assertEqual(self.c3.pk, self.c1.previous())


class PaymentMethodTest(TestCase):

    def setUp(self):
        self.fp1 = baker.make(PaymentMethod)
        self.fp2 = baker.make(PaymentMethod)
        self.fp3 = baker.make(PaymentMethod)

    def test_creation_payment_method(self):
        self.assertTrue(isinstance(self.fp1, PaymentMethod))
        self.assertEqual(self.fp1.__str__(), self.fp1.description)

    def test_next_payment_method(self):
        self.assertEqual(self.fp2.pk, self.fp1.next())
        self.assertEqual(self.fp3.pk, self.fp2.next())

    def test_previous_payment_method(self):
        self.assertEqual(self.fp1.pk, self.fp2.previous())
        self.assertEqual(self.fp2.pk, self.fp3.previous())

    def test_first_payment_method(self):
        self.assertEqual(self.fp1.pk, self.fp3.next())

    def test_last_payment_method(self):
        self.assertEqual(self.fp3.pk, self.fp1.previous())


class DocumentTypeTest(TestCase):

    def setUp(self):
        self.td1 = baker.make(DocumentType)
        self.td2 = baker.make(DocumentType)
        self.td3 = baker.make(DocumentType)

    def test_creation_type_document(self):
        self.assertTrue(isinstance(self.td1, DocumentType))
        self.assertEqual(self.td1.__str__(), self.td1.name)

    def test_next_type_document(self):
        self.assertEqual(self.td2.pk, self.td1.next())
        self.assertEqual(self.td3.pk, self.td2.next())

    def test_previous_type_document(self):
        self.assertEqual(self.td1.pk, self.td2.previous())
        self.assertEqual(self.td2.pk, self.td3.previous())

    def test_first_type_document(self):
        self.assertEqual(self.td1.pk, self.td3.next())

    def test_last_type_document(self):
        self.assertEqual(self.td3.pk, self.td1.previous())


class TypeTest(TestCase):

    def setUp(self):
        self.t1 = baker.make(Type)

    def test_creation_type_document_1(self):
        self.assertTrue(isinstance(self.t1, Type))
        self.assertEqual(self.t1.__str__(), self.t1.value_description)


class TaxTest(TestCase):

    def setUp(self):
        self.imp1 = baker.make(Tax)
        self.imp2 = baker.make(Tax)
        self.imp3 = baker.make(Tax)

    def test_creation_tax(self):
        self.assertTrue(isinstance(self.imp1, Tax))
        self.assertEqual(self.imp1.__str__(), self.imp1.description)

    def test_next_tax(self):
        self.assertEqual(self.imp2.pk, self.imp1.next())
        self.assertEqual(self.imp3.pk, self.imp2.next())

    def test_previous_tax(self):
        self.assertEqual(self.imp1.pk, self.imp2.previous())
        self.assertEqual(self.imp2.pk, self.imp3.previous())

    def test_first_tax(self):
        self.assertEqual(self.imp1.pk, self.imp3.next())

    def test_last_tax(self):
        self.assertEqual(self.imp3.pk, self.imp1.previous())


class CompanyTest(TestCase):

    def setUp(self):
        self.emp1 = baker.make(Company)
        self.emp2 = baker.make(Company)

    def test_creation_company(self):
        self.assertTrue(isinstance(self.emp1, Company))
        self.assertEqual(self.emp1.__str__(), self.emp1.business_name)

    def test_pattern_singleton(self):
        self.assertEqual(self.emp1, self.emp2)

    def test_address_company(self):
        address = self.emp1.place + ' ' + self.emp1.street + ' ' + self.emp1.district
        self.assertEqual(address, self.emp1.address())


class StockTypeTest(TestCase):

    def setUp(self):
        self.te1 = baker.make(StockType)

    def test_creation_type_stock_type(self):
        self.assertEqual(self.te1.__str__(), self.te1.description)
