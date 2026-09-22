"""Importador CSV de proveedores."""
import tempfile

from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.urls import reverse

from purchases.models import Supplier


class PurchasesImportTest(TestCase):

    def setUp(self):
        self.client.force_login(User.objects.create_superuser(
            'cargador', 'c@example.com', 'key-segura'))

    def test_import_suppliers(self):
        content = '12345678901,PROVEEDOR UNO,DIRECCION UNO\n'
        file = SimpleUploadedFile('suppliers.csv', content.encode('utf8'),
                                  content_type='text/csv')

        with tempfile.TemporaryDirectory() as media, self.settings(MEDIA_ROOT=media):
            response = self.client.post(reverse('purchases:supplier_import'), {'file': file})

        self.assertEqual(302, response.status_code)
        supplier = Supplier.objects.get(tax_id='12345678901')
        self.assertEqual('PROVEEDOR UNO', supplier.business_name)
        self.assertEqual('ACTIVO', supplier.sunat_status)
