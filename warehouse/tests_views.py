"""CRUD de almacen: tipos de movimiento y almacenes."""
from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from model_bakery import baker

from warehouse.models import Movement, MovementType, Order, Warehouse


class WarehouseViewsTest(TestCase):

    def setUp(self):
        self.user = User.objects.create_superuser('a', 'a@example.com', 'clave')
        self.client.force_login(self.user)

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

    def test_order_create(self):
        from datetime import date

        from tambox.config import clear_cache

        worker = baker.make('administration.Worker', user=self.user,
                            signature='firmas/firma.png')
        office = baker.make('administration.Office')
        baker.make('administration.Position', office=office, worker=worker,
                   is_leadership=True, end_date=None)
        logistics = baker.make('administration.Office')
        boss = baker.make('administration.Worker',
                          user=baker.make('auth.User', email='jefe@example.com'))
        baker.make('administration.Position', office=logistics, worker=boss,
                   is_leadership=True, is_active=True, start_date=date(2020, 1, 1),
                   end_date=None)
        baker.make('accounting.Configuration', logistics=logistics)
        clear_cache()
        self.addCleanup(clear_cache)
        product = baker.make('products.Product')
        data = {'code': '', 'date': '01/01/2024', 'notes': '',
                'form-TOTAL_FORMS': '1', 'form-INITIAL_FORMS': '0',
                'form-MIN_NUM_FORMS': '0', 'form-MAX_NUM_FORMS': '1000',
                'form-0-code': product.pk, 'form-0-name': 'PRODUCTO',
                'form-0-unit': 'UND01', 'form-0-quantity': '5'}

        response = self.client.post(reverse('warehouse:order_create'), data)

        self.assertEqual(302, response.status_code)
        order = Order.objects.get(requester=worker)
        self.assertEqual(1, order.details.count())

    def test_inbound_create(self):
        movement_type = baker.make(MovementType, code='I01', increases=True)
        warehouse = baker.make(Warehouse)
        product = baker.make('products.Product')
        data = {'movement_id': '', 'movement_type': movement_type.pk,
                'document_type': '', 'series': '', 'number': '',
                'warehouse': warehouse.pk, 'office': '', 'notes': '',
                'date': '01/01/2024', 'time': '08:30:00', 'reference_document': '',
                'receiver_dni': '', 'receiver': '', 'details_count': '0', 'total': '0',
                'form-TOTAL_FORMS': '1', 'form-INITIAL_FORMS': '0',
                'form-MIN_NUM_FORMS': '0', 'form-MAX_NUM_FORMS': '1000',
                'form-0-purchase_order': '999999', 'form-0-code': product.pk,
                'form-0-name': 'PRODUCTO', 'form-0-unit': 'UND01',
                'form-0-quantity': '5', 'form-0-price': '3', 'form-0-amount': '15'}

        response = self.client.post(reverse('warehouse:inbound_create'), data)

        self.assertEqual(302, response.status_code)
        movement = Movement.objects.get(movement_type=movement_type)
        self.assertEqual(1, movement.details.count())

    def test_outbound_create(self):
        movement_type = baker.make(MovementType, code='S01', increases=False)
        warehouse = baker.make(Warehouse)
        product = baker.make('products.Product')
        data = {'movement_id': '', 'movement_type': movement_type.pk,
                'document_type': '', 'series': '', 'number': '',
                'warehouse': warehouse.pk, 'office': '', 'notes': '',
                'date': '01/01/2024', 'time': '08:30:00', 'reference_document': '',
                'receiver_dni': '', 'receiver': '', 'details_count': '0', 'total': '0',
                'form-TOTAL_FORMS': '1', 'form-INITIAL_FORMS': '0',
                'form-MIN_NUM_FORMS': '0', 'form-MAX_NUM_FORMS': '1000',
                'form-0-order': '', 'form-0-code': product.pk,
                'form-0-name': 'PRODUCTO', 'form-0-unit': 'UND01',
                'form-0-quantity': '5', 'form-0-price': '3', 'form-0-amount': '15'}

        response = self.client.post(reverse('warehouse:outbound_create'), data)

        self.assertEqual(302, response.status_code)
        movement = Movement.objects.get(movement_type=movement_type)
        self.assertEqual(1, movement.details.count())

    def test_order_update(self):
        from datetime import date

        from administration.models import Office, Position, Worker
        from tambox.config import clear_cache

        worker = baker.make(Worker, user=self.user, signature='firmas/firma.png')
        office = baker.make(Office)
        baker.make(Position, office=office, worker=worker, is_leadership=True,
                   end_date=None)
        logistics = baker.make(Office)
        boss = baker.make(Worker, user=baker.make('auth.User', email='jefe@example.com'))
        baker.make(Position, office=logistics, worker=boss, is_leadership=True,
                   is_active=True, start_date=date(2020, 1, 1), end_date=None)
        baker.make('accounting.Configuration', logistics=logistics)
        clear_cache()
        self.addCleanup(clear_cache)
        order = baker.make(Order, requester=worker, office=office,
                           status=Order.STATUS.PEND)
        product = baker.make('products.Product')
        data = {'code': '', 'date': '01/01/2024', 'notes': '',
                'form-TOTAL_FORMS': '1', 'form-INITIAL_FORMS': '0',
                'form-MIN_NUM_FORMS': '0', 'form-MAX_NUM_FORMS': '1000',
                'form-0-code': product.pk, 'form-0-name': 'PRODUCTO',
                'form-0-unit': 'UND01', 'form-0-quantity': '5'}

        response = self.client.post(reverse('warehouse:order_update', args=[order.pk]),
                                    data)

        self.assertEqual(302, response.status_code)
        order.refresh_from_db()
        self.assertEqual(1, order.details.count())

    def test_inbound_update(self):
        movement_type = baker.make(MovementType, code='I01', increases=True)
        warehouse = baker.make(Warehouse)
        movement = baker.make(Movement, movement_id='', movement_type=movement_type,
                              warehouse=warehouse, operation_date=timezone.now())
        product = baker.make('products.Product')
        data = {'movement_id': movement.movement_id, 'movement_type': movement_type.pk,
                'document_type': '', 'series': '', 'number': '',
                'warehouse': warehouse.pk, 'office': '', 'notes': '',
                'date': '01/01/2024', 'time': '08:30:00', 'reference_document': '',
                'receiver_dni': '', 'receiver': '', 'details_count': '0', 'total': '0',
                'form-TOTAL_FORMS': '1', 'form-INITIAL_FORMS': '0',
                'form-MIN_NUM_FORMS': '0', 'form-MAX_NUM_FORMS': '1000',
                'form-0-purchase_order': '999999', 'form-0-code': product.pk,
                'form-0-name': 'PRODUCTO', 'form-0-unit': 'UND01',
                'form-0-quantity': '5', 'form-0-price': '3', 'form-0-amount': '15'}

        response = self.client.post(reverse('warehouse:inbound_update', args=[movement.pk]),
                                    data)

        self.assertEqual(302, response.status_code)
        movement.refresh_from_db()
        self.assertEqual(1, movement.details.count())

    def test_outbound_update(self):
        movement_type = baker.make(MovementType, code='S01', increases=False)
        warehouse = baker.make(Warehouse)
        movement = baker.make(Movement, movement_id='', movement_type=movement_type,
                              warehouse=warehouse, operation_date=timezone.now())
        product = baker.make('products.Product')
        data = {'movement_id': movement.movement_id, 'movement_type': movement_type.pk,
                'document_type': '', 'series': '', 'number': '',
                'warehouse': warehouse.pk, 'office': '', 'notes': '',
                'date': '01/01/2024', 'time': '08:30:00', 'reference_document': '',
                'receiver_dni': '', 'receiver': '', 'details_count': '0', 'total': '0',
                'form-TOTAL_FORMS': '1', 'form-INITIAL_FORMS': '0',
                'form-MIN_NUM_FORMS': '0', 'form-MAX_NUM_FORMS': '1000',
                'form-0-order': '999999', 'form-0-code': product.pk,
                'form-0-name': 'PRODUCTO', 'form-0-unit': 'UND01',
                'form-0-quantity': '5', 'form-0-price': '3', 'form-0-amount': '15'}

        response = self.client.post(reverse('warehouse:outbound_update', args=[movement.pk]),
                                    data)

        self.assertEqual(302, response.status_code)
        movement.refresh_from_db()
        self.assertEqual(1, movement.details.count())

    def test_movement_and_order_lists(self):
        movement_type = baker.make(MovementType, code='I01', increases=True)
        baker.make('warehouse.Movement', movement_id='', movement_type=movement_type,
                   warehouse=baker.make(Warehouse))

        for name in ('warehouse:movement_list', 'warehouse:inbound_list',
                     'warehouse:outbound_list', 'warehouse:order_list'):
            with self.subTest(name=name):
                response = self.client.get(reverse(name))
                self.assertIn(response.status_code, (200, 302))
