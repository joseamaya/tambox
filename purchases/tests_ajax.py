"""Endpoints AJAX de compras."""
from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from model_bakery import baker

from purchases.models import Quotation, Supplier


class PurchasesAjaxTest(TestCase):

    def setUp(self):
        self.client.force_login(User.objects.create_superuser('a', 'a@example.com', 'clave'))

    def get(self, name, params=None):
        return self.client.get(reverse(name), params or {},
                               HTTP_X_REQUESTED_WITH='XMLHttpRequest')

    def test_quotation_search(self):
        supplier = baker.make(Supplier, tax_id='12345678901', business_name='PROVEEDOR UNO')
        quotation = baker.make(Quotation, supplier=supplier)

        response = self.get('purchases:quotation_search', {'code': quotation.code})

        self.assertEqual(200, response.status_code)
        self.assertEqual('12345678901', response.json()['tax_id'])
