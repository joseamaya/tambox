"""Importadores CSV de productos.

El grupo necesita una cuenta contable; el producto y el servicio necesitan un
grupo, y el producto ademas la unidad de medida y el tipo de existencia.
"""
import tempfile

from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.urls import reverse
from model_bakery import baker

from accounting.models import Account, StockType
from products.models import Product, ProductGroup


class ProductsImportTest(TestCase):

    def setUp(self):
        self.client.force_login(User.objects.create_superuser(
            'cargador', 'c@example.com', 'key-segura'))
        self.account = baker.make(Account, account_number='CTA01')

    def upload(self, name, filename, content):
        file = SimpleUploadedFile(filename, content.encode('utf8'), content_type='text/csv')
        with tempfile.TemporaryDirectory() as media, self.settings(MEDIA_ROOT=media):
            return self.client.post(reverse(name), {'file': file})

    def test_import_product_groups(self):
        response = self.upload('products:product_group_import', 'groups.csv', 'CTA01,GRUPO UNO\n')

        self.assertEqual(302, response.status_code)
        group = ProductGroup.objects.get(description='GRUPO UNO')
        self.assertEqual(self.account, group.account)

    def test_import_services(self):
        group = baker.make(ProductGroup, code='000001', account=self.account)

        response = self.upload('products:service_import', 'services.csv',
                               '%s,SERVICIO UNO\n' % group.code)

        self.assertEqual(302, response.status_code)
        service = Product.objects.get(description='SERVICIO UNO')
        self.assertTrue(service.is_service)
        self.assertEqual('SERV', service.unit_of_measure.code)

    def test_import_products(self):
        group = baker.make(ProductGroup, code='000001', account=self.account)
        baker.make(StockType, sunat_code='01')

        response = self.upload('products:product_import', 'products.csv',
                               '%s,PRODUCTO UNO,UND01,10.5,01\n' % group.code)

        self.assertEqual(302, response.status_code)
        product = Product.objects.get(description='PRODUCTO UNO')
        self.assertEqual(group, product.product_group)
        self.assertEqual('UND01', product.unit_of_measure.code)
        self.assertEqual('01', product.stock_type.sunat_code)
