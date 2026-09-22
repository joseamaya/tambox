"""CRUD de almacen: tipos de movimiento y almacenes."""
from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from model_bakery import baker

from warehouse.models import MovementType, Warehouse


class WarehouseViewsTest(TestCase):

    def setUp(self):
        self.client.force_login(User.objects.create_superuser('a', 'a@example.com', 'clave'))

    def test_movement_type_crud(self):
        response = self.client.post(reverse('warehouse:movement_type_create'),
                                    {'description': 'INGRESO', 'sunat_code': '01',
                                     'increases': 'on', 'is_purchase': 'on'})
        self.assertEqual(302, response.status_code)
        movement_type = MovementType.objects.get(description='INGRESO')

        self.assertEqual(200, self.client.get(
            reverse('warehouse:movement_type_detail', args=[movement_type.pk])).status_code)

    def test_warehouse_crud_and_delete(self):
        response = self.client.post(reverse('warehouse:warehouse_create'),
                                    {'code': 'AL01', 'description': 'ALMACEN UNO'})
        self.assertEqual(302, response.status_code)
        warehouse = Warehouse.objects.get(code='AL01')

        self.assertEqual(200, self.client.get(
            reverse('warehouse:warehouse_detail', args=[warehouse.pk])).status_code)
        response = self.client.post(reverse('warehouse:warehouse_update', args=[warehouse.pk]),
                                    {'code': 'AL01', 'description': 'ALMACEN EDITADO'})
        self.assertEqual(302, response.status_code)

        response = self.client.post(reverse('warehouse:warehouse_delete'),
                                    {'code': warehouse.pk},
                                    HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(200, response.status_code)
        warehouse.refresh_from_db()
        self.assertFalse(warehouse.is_active)

    def test_dashboard_and_excel_reports(self):
        self.assertEqual(200, self.client.get(reverse('warehouse:dashboard')).status_code)

        for name in ('warehouse:warehouse_excel_report',
                     'warehouse:movement_type_excel_report'):
            with self.subTest(name=name):
                self.assertEqual(200, self.client.get(reverse(name)).status_code)

    def test_movement_and_order_lists(self):
        movement_type = baker.make(MovementType, code='I01', increases=True)
        baker.make('warehouse.Movement', movement_id='', movement_type=movement_type,
                   warehouse=baker.make(Warehouse))

        for name in ('warehouse:movement_list', 'warehouse:inbound_list',
                     'warehouse:outbound_list', 'warehouse:order_list'):
            with self.subTest(name=name):
                response = self.client.get(reverse(name))
                self.assertIn(response.status_code, (200, 302))
