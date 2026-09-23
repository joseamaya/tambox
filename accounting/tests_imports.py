"""Importadores CSV de contabilidad.

Comparten `CsvImportMixin`, que guarda el archivo y delega cada fila en
`process_row()`; lo que cambia por importador son las columnas que lee.
"""
import tempfile

from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.urls import reverse

from accounting.models import Account, DocumentType, StockType


class AccountingImportTest(TestCase):

    def setUp(self):
        self.client.force_login(User.objects.create_superuser(
            'cargador', 'c@example.com', 'key-segura'))

    def upload(self, name, filename, content):
        file = SimpleUploadedFile(filename, content.encode('utf8'), content_type='text/csv')
        with tempfile.TemporaryDirectory() as media, self.settings(MEDIA_ROOT=media):
            return self.client.post(reverse(name), {'file': file})

    def test_import_accounts(self):
        response = self.upload('accounting:account_import', 'accounts.csv', 'CTA01,CUENTA UNO\n')

        self.assertEqual(302, response.status_code)
        self.assertEqual('CUENTA UNO', Account.objects.get(account_number='CTA01').description)

    def test_import_stock_types(self):
        response = self.upload('accounting:stock_type_import', 'stock.csv', '01,EXISTENCIA UNO\n')

        self.assertEqual(302, response.status_code)
        self.assertEqual('EXISTENCIA UNO', StockType.objects.get(sunat_code='01').description)

    def test_import_document_types(self):
        response = self.upload('accounting:document_type_import', 'documents.csv', 'PEC,PECOSA\n')

        self.assertEqual(302, response.status_code)
        self.assertTrue(DocumentType.objects.filter(sunat_code='PEC', name='PECOSA').exists())
