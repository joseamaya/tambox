"""CRUD de contabilidad: crear, ver, editar y borrar cada entidad.

Los formularios son `ModelForm` planos, asi que un POST valido tiene que dejar
la fila creada/actualizada y redirigir; el detalle tiene que pintar el objeto.
"""
import datetime

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from model_bakery import baker

from accounting.models import Account, DocumentType, ExchangeRate, PaymentMethod, Tax


class AccountingViewsTest(TestCase):

    def setUp(self):
        self.client.force_login(User.objects.create_superuser('a', 'a@example.com', 'clave'))

    def test_account_crud(self):
        self.assertEqual(200, self.client.get(reverse('accounting:account_create')).status_code)

        response = self.client.post(reverse('accounting:account_create'),
                                    {'account_number': 'CTA01', 'description': 'CUENTA UNO',
                                     'depreciation': '0'})
        self.assertEqual(302, response.status_code)
        account = Account.objects.get(account_number='CTA01')

        self.assertEqual(200, self.client.get(
            reverse('accounting:account_detail', args=[account.pk])).status_code)
        self.assertEqual(200, self.client.get(
            reverse('accounting:account_update', args=[account.pk])).status_code)

        response = self.client.post(reverse('accounting:account_update', args=[account.pk]),
                                    {'account_number': 'CTA01', 'description': 'CUENTA EDITADA',
                                     'depreciation': '0'})
        self.assertEqual(302, response.status_code)
        account.refresh_from_db()
        self.assertEqual('CUENTA EDITADA', account.description)

    def test_tax_crud(self):
        self.assertEqual(200, self.client.get(reverse('accounting:tax_create')).status_code)

        response = self.client.post(reverse('accounting:tax_create'),
                                    {'abbreviation': 'IGV', 'description': 'IMPUESTO',
                                     'amount': '18', 'start_date': '01/01/2024'})
        self.assertEqual(302, response.status_code)
        tax = Tax.objects.get(abbreviation='IGV')

        self.assertEqual(200, self.client.get(
            reverse('accounting:tax_detail', args=[tax.pk])).status_code)
        response = self.client.post(reverse('accounting:tax_update', args=[tax.pk]),
                                    {'abbreviation': 'IGV', 'description': 'IMPUESTO GENERAL',
                                     'amount': '18', 'start_date': '01/01/2024'})
        self.assertEqual(302, response.status_code)
        tax.refresh_from_db()
        self.assertEqual('IMPUESTO GENERAL', tax.description)

    def test_document_type_crud(self):
        response = self.client.post(reverse('accounting:document_type_create'),
                                    {'sunat_code': 'PEC', 'name': 'PECOSA',
                                     'description': 'PECOSA'})
        self.assertEqual(302, response.status_code)
        document = DocumentType.objects.get(sunat_code='PEC')

        self.assertEqual(200, self.client.get(
            reverse('accounting:document_type_detail', args=[document.pk])).status_code)
        response = self.client.post(reverse('accounting:document_type_update',
                                            args=[document.pk]),
                                    {'sunat_code': 'PEC', 'name': 'PECOSA EDITADA',
                                     'description': 'PECOSA'})
        self.assertEqual(302, response.status_code)

        response = self.client.post(reverse('accounting:document_type_delete'),
                                    {'id': document.pk},
                                    HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(200, response.status_code)
        document.refresh_from_db()
        self.assertFalse(document.is_active)

    def test_payment_method_crud_and_report(self):
        response = self.client.post(reverse('accounting:payment_method_create'),
                                    {'code': 'EFE', 'description': 'EFECTIVO',
                                     'credit_days': '0'})
        self.assertEqual(302, response.status_code)
        method = PaymentMethod.objects.get(code='EFE')

        self.assertEqual(200, self.client.get(
            reverse('accounting:payment_method_detail', args=[method.pk])).status_code)
        response = self.client.post(reverse('accounting:payment_method_update',
                                            args=[method.pk]),
                                    {'code': 'EFE', 'description': 'EFECTIVO EDITADO',
                                     'credit_days': '0'})
        self.assertEqual(302, response.status_code)

        response = self.client.get(reverse('accounting:payment_method_excel_report'))
        self.assertEqual(200, response.status_code)

        response = self.client.post(reverse('accounting:payment_method_delete'),
                                    {'code': method.pk},
                                    HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(200, response.status_code)
        method.refresh_from_db()
        self.assertFalse(method.is_active)

    def test_exchange_rate_crud(self):
        response = self.client.post(reverse('accounting:exchange_rate_create'),
                                    {'amount': '3.75', 'date': '15/01/2024'})
        self.assertEqual(302, response.status_code)
        rate = ExchangeRate.objects.get(date=datetime.date(2024, 1, 15))

        self.assertEqual(200, self.client.get(
            reverse('accounting:exchange_rate_detail', args=[rate.pk])).status_code)
        response = self.client.post(reverse('accounting:exchange_rate_update',
                                            args=[rate.pk]),
                                    {'amount': '3.8', 'date': '15/01/2024'})
        self.assertEqual(302, response.status_code)
        rate.refresh_from_db()
        self.assertEqual(3.8, float(rate.amount))

    def test_configuration_crud(self):
        tax = baker.make(Tax)
        office = baker.make('administration.Office')

        self.assertEqual(200, self.client.get(reverse('accounting:configuration')).status_code)

        response = self.client.post(reverse('accounting:configuration'),
                                    {'purchase_tax': tax.pk, 'operations': office.pk,
                                     'administration': office.pk, 'budget': office.pk,
                                     'logistics': office.pk})
        self.assertEqual(302, response.status_code)

    def test_lists_return_htmx_fragment_and_search(self):
        baker.make(Tax, abbreviation='IGV', description='IMPUESTO GENERAL')
        baker.make(PaymentMethod, code='EFE', description='EFECTIVO')
        baker.make(DocumentType, sunat_code='01', name='FACTURA')
        baker.make('accounting.StockType', sunat_code='01', description='MERCADERIA')
        cases = [
            ('accounting:tax_list', {'q': 'GENERAL'}, 'IMPUESTO GENERAL'),
            ('accounting:payment_method_list', {'q': 'EFECTIVO'}, 'EFECTIVO'),
            ('accounting:document_type_list', {'q': 'FACTURA'}, 'FACTURA'),
            ('accounting:stock_type_list', {'q': 'MERCADERIA'}, 'MERCADERIA'),
        ]

        for name, params, expected in cases:
            with self.subTest(name=name):
                fragment = self.client.get(reverse(name), params,
                                           HTTP_HX_REQUEST='true')
                self.assertEqual(200, fragment.status_code)
                self.assertNotContains(fragment, '<html')
                self.assertContains(fragment, expected)

    def test_excel_reports(self):
        for name in ('accounting:account_excel_report',
                     'accounting:document_type_excel_report'):
            with self.subTest(name=name):
                self.assertEqual(200, self.client.get(reverse(name)).status_code)
