"""Buscadores AJAX de productos."""
from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from model_bakery import baker

from products.models import Product, UnitOfMeasure


class ProductSearchTest(TestCase):

    def setUp(self):
        self.client.force_login(User.objects.create_superuser('a', 'a@example.com', 'clave'))
        unit = baker.make(UnitOfMeasure, code='UND01', description='UNIDAD')
        self.product = baker.make(Product, code='P000000001', description='ACERO',
                                  unit_of_measure=unit, is_service=False, price=3)
        self.service = baker.make(Product, code='S000000001', description='SERVICIO ACERO',
                                  unit_of_measure=unit, is_service=True, price=5)

    def search(self, name, params):
        return self.client.get(reverse(name), params,
                               HTTP_X_REQUESTED_WITH='XMLHttpRequest')

    def test_description_search_all(self):
        response = self.search('products:product_description_search',
                               {'description': 'ACERO', 'search_type': 'TODOS'})

        self.assertEqual(200, response.status_code)
        self.assertEqual(2, len(response.json()))

    def test_description_search_products(self):
        response = self.search('products:product_description_search',
                               {'description': 'ACERO', 'search_type': 'PRODUCTOS'})

        self.assertEqual([self.product.code], [row['code'] for row in response.json()])

    def test_description_search_services(self):
        response = self.search('products:product_description_search',
                               {'description': 'ACERO', 'search_type': 'SERVICIOS'})

        self.assertEqual([self.service.code], [row['code'] for row in response.json()])

    def test_code_search(self):
        response = self.search('products:product_code_search', {'code': 'P000000001'})

        self.assertEqual(200, response.status_code)
        self.assertEqual('ACERO', response.json()[0]['description'])

    def test_stock_query(self):
        response = self.search('products:product_stock_query', {'code': self.product.code})

        self.assertEqual(200, response.status_code)
        self.assertEqual(0, response.json()['stock'])
