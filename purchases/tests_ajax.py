"""Endpoints AJAX de compras."""
from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from model_bakery import baker

from purchases.models import PurchaseOrder, Quotation, ServiceOrder, Supplier


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

    def test_service_order_detail_create(self):
        response = self.get('purchases:service_order_detail_create')

        self.assertEqual(200, response.status_code)
        self.assertEqual(1, len(response.json()))

    def test_quotation_detail_fetch(self):
        quotation = baker.make(Quotation, supplier=baker.make(Supplier))

        response = self.get('purchases:quotation_detail_fetch',
                            {'quotation': quotation.code, 'search_type': 'PRODUCTOS'})

        self.assertEqual(200, response.status_code)
        self.assertEqual([], response.json())

    def test_purchase_order_detail_fetch(self):
        order = baker.make(PurchaseOrder, supplier=baker.make(Supplier), in_dollars=False)

        response = self.get('purchases:purchase_order_detail_fetch',
                            {'purchase_order': order.code, 'date': '15/01/2024'})

        self.assertEqual(200, response.status_code)
        self.assertEqual([], response.json())

    def test_service_order_detail_fetch(self):
        order = baker.make(ServiceOrder, supplier=baker.make(Supplier))

        response = self.get('purchases:service_order_detail_fetch',
                            {'service_order': order.code})

        self.assertEqual(200, response.status_code)
        self.assertEqual([], response.json())
