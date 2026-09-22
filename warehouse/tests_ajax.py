"""Endpoints AJAX de almacen."""
from decimal import Decimal

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from model_bakery import baker

from products.models import Product, UnitOfMeasure
from warehouse.models import Kardex, Movement, MovementType, Order, OrderDetail, Warehouse


class WarehouseAjaxTest(TestCase):

    def setUp(self):
        self.client.force_login(User.objects.create_superuser('a', 'a@example.com', 'clave'))
        self.warehouse = baker.make(Warehouse, code='AL01', description='ALMACEN UNO')
        self.unit = baker.make(UnitOfMeasure, code='UND01', description='UNIDAD')
        self.product = baker.make(Product, code='P000000001', description='ACERO',
                                  unit_of_measure=self.unit, price=3)

    def get(self, name, params=None):
        return self.client.get(reverse(name), params or {},
                               HTTP_X_REQUESTED_WITH='XMLHttpRequest')

    def make_kardex(self):
        movement_type = baker.make(MovementType, code='I01', increases=True)
        movement = baker.make(Movement, movement_id='', operation_date=timezone.now(),
                              movement_type=movement_type, warehouse=self.warehouse)
        return baker.make(Kardex, movement=movement, movement_line_number=1,
                          product=self.product, operation_date=timezone.now(),
                          warehouse=self.warehouse, total_quantity=Decimal('7'),
                          total_amount=Decimal('21'), total_price=Decimal('3'))

    def test_product_warehouse_search(self):
        self.make_kardex()

        response = self.get('warehouse:product_warehouse_search',
                            {'description': 'ACERO', 'warehouse': self.warehouse.pk})

        self.assertEqual(200, response.status_code)
        self.assertEqual('P000000001', response.json()[0]['code'])

    def test_stock_query(self):
        self.make_kardex()

        response = self.get('warehouse:stock_query',
                            {'warehouse': self.warehouse.pk, 'code': self.product.code})

        self.assertEqual(200, response.status_code)
        self.assertEqual(7, response.json()['stock'])

    def test_detail_row_endpoints(self):
        for name in ('warehouse:outbound_detail_row', 'warehouse:order_detail_row',
                     'warehouse:inbound_detail_row'):
            with self.subTest(name=name):
                response = self.client.get(reverse(name), {'index': '2'})
                self.assertEqual(200, response.status_code)
                self.assertContains(response, 'name="form-2-code"')

    def test_verify_reference(self):
        movement_type = baker.make(MovementType, code='I02', increases=True,
                                   requires_reference=True)

        response = self.get('warehouse:verify_reference_required', {'type': movement_type.pk})

        self.assertTrue(response.json()['requires_reference'])

    def test_order_approve_detail_rows(self):
        order = baker.make(Order, code='P000000001')
        baker.make(OrderDetail, order=order, product=self.product, quantity=2,
                   served_quantity=0)

        response = self.get('warehouse:order_approve_detail_rows',
                            {'warehouse': self.warehouse.code, 'order': order.code})

        self.assertEqual(200, response.status_code)
        self.assertContains(response, 'name="form-TOTAL_FORMS"')
