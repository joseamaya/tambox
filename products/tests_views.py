"""CRUD de productos.

El codigo de `Product` y `ProductGroup` lo genera `save()`, asi que se lee del
objeto creado; el borrado de estos modelos es un POST AJAX que desactiva la
fila.
"""
from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from model_bakery import baker

from accounting.models import Account, StockType
from products.models import Product, ProductGroup, UnitOfMeasure


class ProductsViewsTest(TestCase):

    def setUp(self):
        self.client.force_login(User.objects.create_superuser('a', 'a@example.com', 'clave'))
        self.account = baker.make(Account)
        self.stock_type = baker.make(StockType)

    def post(self, name, data):
        return self.client.post(reverse(name), data)

    def test_unit_of_measure_crud_and_delete(self):
        response = self.post('products:unit_of_measure_create',
                             {'code': 'UND01', 'sunat_code': '01', 'description': 'UNIDAD'})
        self.assertEqual(302, response.status_code)
        unit = UnitOfMeasure.objects.get(code='UND01')

        self.assertEqual(200, self.client.get(
            reverse('products:unit_of_measure_detail', args=[unit.pk])).status_code)
        response = self.client.post(reverse('products:unit_of_measure_update', args=[unit.pk]),
                                    {'code': 'UND01', 'sunat_code': '01',
                                     'description': 'UNIDAD EDITADA'})
        self.assertEqual(302, response.status_code)

        response = self.client.post(reverse('products:unit_of_measure_delete'),
                                    {'id': unit.pk}, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(200, response.status_code)
        unit.refresh_from_db()
        self.assertFalse(unit.is_active)

    def test_product_group_crud(self):
        response = self.post('products:product_group_create',
                             {'description': 'GRUPO UNO', 'account': self.account.pk,
                              'contains_products': 'on'})
        self.assertEqual(302, response.status_code)
        group = ProductGroup.objects.get(description='GRUPO UNO')

        self.assertEqual(200, self.client.get(
            reverse('products:product_group_detail', args=[group.pk])).status_code)
        response = self.client.post(reverse('products:product_group_update', args=[group.pk]),
                                    {'description': 'GRUPO EDITADO', 'account': self.account.pk,
                                     'contains_products': 'on'})
        self.assertEqual(302, response.status_code)

        response = self.client.post(reverse('products:product_group_delete'),
                                    {'code': group.pk}, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(200, response.status_code)
        group.refresh_from_db()
        self.assertFalse(group.is_active)

    def test_product_crud(self):
        group = baker.make(ProductGroup, account=self.account)
        unit = baker.make(UnitOfMeasure)

        response = self.post('products:product_create',
                             {'description': 'PRODUCTO UNO', 'product_group': group.pk,
                              'unit_of_measure': unit.pk, 'price': '10.5',
                              'stock_type': self.stock_type.pk})
        self.assertEqual(302, response.status_code)
        product = Product.objects.get(description='PRODUCTO UNO')

        self.assertEqual(200, self.client.get(
            reverse('products:product_detail', args=[product.pk])).status_code)
        response = self.client.post(reverse('products:product_update', args=[product.pk]),
                                    {'description': 'PRODUCTO EDITADO',
                                     'product_group': group.pk, 'unit_of_measure': unit.pk,
                                     'price': '11', 'stock_type': self.stock_type.pk})
        self.assertEqual(302, response.status_code)

        self.assertEqual(200, self.client.get(
            reverse('products:product_list_by_group', args=[group.pk])).status_code)

        response = self.client.post(reverse('products:product_delete'),
                                    {'code': product.pk}, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(200, response.status_code)
        product.refresh_from_db()
        self.assertFalse(product.is_active)

    def test_service_crud(self):
        group = baker.make(ProductGroup, account=self.account)

        response = self.post('products:service_create',
                             {'description': 'SERVICIO UNO', 'product_group': group.pk,
                              'price': '20'})
        self.assertEqual(302, response.status_code)
        service = Product.objects.get(description='SERVICIO UNO')
        self.assertTrue(service.is_service)

        self.assertEqual(200, self.client.get(
            reverse('products:service_detail', args=[service.pk])).status_code)

        response = self.client.post(reverse('products:service_delete'),
                                    {'code': service.pk}, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(200, response.status_code)
        service.refresh_from_db()
        self.assertFalse(service.is_active)

    def test_lists_return_htmx_fragment_and_search(self):
        group = baker.make(ProductGroup, code='000001', description='GRUPO UNICO',
                           account=self.account)
        baker.make(Product, code='', product_group=group, description='BIEN UNICO')
        baker.make(Product, code='', product_group=group, description='SERVICIO UNICO',
                   is_service=True)
        cases = [
            ('products:product_list', 'BIEN UNICO'),
            ('products:product_group_list', 'GRUPO UNICO'),
            ('products:service_list', 'SERVICIO UNICO'),
        ]

        for name, expected in cases:
            with self.subTest(name=name):
                fragment = self.client.get(reverse(name), {'q': expected},
                                           HTTP_HX_REQUEST='true')
                self.assertEqual(200, fragment.status_code)
                self.assertNotContains(fragment, '<html')
                self.assertContains(fragment, expected)

    def test_dashboard_and_reports(self):
        self.assertEqual(200, self.client.get(reverse('products:dashboard')).status_code)

        for name in ('products:product_excel_report',
                     'products:product_group_excel_report',
                     'products:unit_of_measure_excel_report',
                     'products:service_excel_report'):
            with self.subTest(name=name):
                self.assertEqual(200, self.client.get(reverse(name)).status_code)
