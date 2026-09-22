"""CRUD de almacen: tipos de movimiento y almacenes."""
from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from model_bakery import baker

from warehouse.models import Movement, MovementType, Order, OrderDetail, Warehouse


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

    def test_movement_excel_report(self):
        movement_type = baker.make(MovementType, code='I01', increases=True)
        warehouse = baker.make(Warehouse)
        baker.make(Movement, movement_id='', movement_type=movement_type,
                   warehouse=warehouse, operation_date=timezone.now())
        base = {'start_date': '01/01/2024', 'end_date': '31/01/2024', 'month': '01',
                'year': '2024', 'movement_types': movement_type.code,
                'warehouses': warehouse.code}

        for search_type in ('F', 'M', 'A'):
            with self.subTest(search_type=search_type):
                data = dict(base, search_type=search_type)
                response = self.client.post(reverse('warehouse:movement_report'), data)
                self.assertEqual(200, response.status_code)

    def test_movement_excel_report_by_date(self):
        movement_type = baker.make(MovementType, code='I01', increases=True)
        warehouse = baker.make(Warehouse)
        baker.make(Movement, movement_id='', movement_type=movement_type,
                   warehouse=warehouse, operation_date=timezone.now())
        url = reverse('warehouse:movement_excel_report_by_date',
                      args=['01/01/2024', '31/01/2024', warehouse.code,
                            movement_type.code])

        response = self.client.get(url)

        self.assertEqual(200, response.status_code)

    def test_movement_and_order_lists(self):
        movement_type = baker.make(MovementType, code='I01', increases=True)
        baker.make('warehouse.Movement', movement_id='', movement_type=movement_type,
                   warehouse=baker.make(Warehouse))

        for name in ('warehouse:movement_list', 'warehouse:inbound_list',
                     'warehouse:outbound_list', 'warehouse:order_list'):
            with self.subTest(name=name):
                response = self.client.get(reverse(name))
                self.assertIn(response.status_code, (200, 302))

    def _approval_graph(self, signature='firmas/firma.png', leadership=True):
        from datetime import date

        from administration.models import Office, Position, Worker
        from tambox.config import clear_cache

        movement_type = baker.make(MovementType, code='S01', increases=False)
        warehouse = baker.make(Warehouse)
        worker = baker.make(Worker, user=self.user, signature=signature)
        logistics = baker.make(Office)
        baker.make(Position, office=logistics, worker=worker, is_leadership=leadership,
                   is_active=True, start_date=date(2020, 1, 1), end_date=None)
        baker.make('accounting.Configuration', logistics=logistics)
        clear_cache()
        self.addCleanup(clear_cache)
        order = baker.make(Order, requester=baker.make(Worker), office=baker.make(Office))
        product = baker.make('products.Product')
        order_detail = baker.make(OrderDetail, order=order, product=product,
                                  line_number=1, quantity=5,
                                  status=OrderDetail.STATUS.PEND)
        return movement_type, warehouse, order, product, order_detail

    def test_order_approve_get(self):
        _, _, order, _, _ = self._approval_graph()

        response = self.client.get(reverse('warehouse:order_approve', args=[order.code]))

        self.assertEqual(200, response.status_code)

    def test_order_approve_get_requires_signature(self):
        _, _, order, _, _ = self._approval_graph(signature='')
        worker = self.user.worker

        response = self.client.get(reverse('warehouse:order_approve', args=[order.code]))

        self.assertEqual(302, response.status_code)
        self.assertEqual(reverse('administration:worker_update', args=[worker.pk]), response.url)

    def test_order_approve_get_requires_worker(self):
        order = baker.make(Order, requester=baker.make('administration.Worker'))

        response = self.client.get(reverse('warehouse:order_approve', args=[order.code]))

        self.assertEqual(302, response.status_code)
        self.assertEqual(reverse('administration:worker_create'), response.url)

    def test_order_approve_get_denied_without_logistics(self):
        _, _, order, _, _ = self._approval_graph(leadership=False)

        response = self.client.get(reverse('warehouse:order_approve', args=[order.code]))

        self.assertEqual(302, response.status_code)
        self.assertEqual(reverse('security:permission_denied'), response.url)

    def test_order_approve_post(self):
        movement_type, warehouse, order, product, order_detail = self._approval_graph()
        data = {'order_code': order.code, 'date': '01/01/2024', 'time': '10:00:00',
                'total': '10.00000', 'warehouse': warehouse.pk, 'notes': '',
                'form-TOTAL_FORMS': '1', 'form-INITIAL_FORMS': '0',
                'form-MIN_NUM_FORMS': '0', 'form-MAX_NUM_FORMS': '1000',
                'form-0-order': order_detail.pk, 'form-0-code': product.pk,
                'form-0-name': product.description, 'form-0-unit': 'UND01',
                'form-0-quantity': '1', 'form-0-price': '10', 'form-0-amount': '10'}

        response = self.client.post(reverse('warehouse:order_approve', args=[order.code]), data)

        self.assertEqual(302, response.status_code)
        movement = Movement.objects.get(movement_type=movement_type)
        self.assertEqual(1, movement.details.count())
        order_detail.refresh_from_db()
        self.assertEqual(OrderDetail.STATUS.ATEN_PARC, order_detail.status)

    def test_order_approve_post_invalid(self):
        _, _, order, product, order_detail = self._approval_graph()
        data = {'order_code': order.code, 'date': '01/01/2024', 'time': '10:00:00',
                'total': '10.00000', 'warehouse': '', 'notes': '',
                'form-TOTAL_FORMS': '1', 'form-INITIAL_FORMS': '0',
                'form-MIN_NUM_FORMS': '0', 'form-MAX_NUM_FORMS': '1000',
                'form-0-order': order_detail.pk, 'form-0-code': product.pk,
                'form-0-name': product.description, 'form-0-unit': 'UND01',
                'form-0-quantity': '1', 'form-0-price': '10', 'form-0-amount': '10'}

        response = self.client.post(reverse('warehouse:order_approve', args=[order.code]), data)

        self.assertEqual(200, response.status_code)


class WarehouseReportViewsTest(TestCase):
    """Las vistas que envuelven a los reportes: el armado del file, las
    combinaciones de formato y las ramas de error."""

    def setUp(self):
        from datetime import datetime
        from decimal import Decimal

        from accounting.models import Account, DocumentType, StockType
        from products.models import Product, ProductGroup, UnitOfMeasure
        from warehouse.models import Kardex

        self.user = User.objects.create_superuser('r', 'r@example.com', 'clave')
        self.client.force_login(self.user)
        self.warehouse = baker.make(Warehouse)
        self.group = baker.make(ProductGroup, code='000001',
                                account=baker.make(Account))
        self.product = baker.make(Product, code='', product_group=self.group,
                                  unit_of_measure=baker.make(UnitOfMeasure),
                                  stock_type=baker.make(StockType))
        self.movement_type = baker.make(MovementType, code='I01', increases=True,
                                        sunat_code='01')
        baker.make(Kardex, warehouse=self.warehouse, product=self.product,
                   movement=baker.make(Movement, movement_type=self.movement_type,
                                       warehouse=self.warehouse,
                                       document_type=baker.make(DocumentType, sunat_code='PEC')),
                   operation_date=timezone.make_aware(datetime(2024, 1, 10, 9, 0)),
                   in_quantity=Decimal('5'), in_price=Decimal('3'),
                   in_amount=Decimal('15'), out_quantity=Decimal('0'),
                   out_price=Decimal('0'), out_amount=Decimal('0'),
                   total_quantity=Decimal('5'), total_price=Decimal('3'),
                   total_amount=Decimal('15'))

    def test_kardex_product_report(self):
        url = reverse('warehouse:kardex_product_report')
        base = {'warehouses': self.warehouse.pk, 'start_date': '01/01/2024',
                'end_date': '31/01/2024', 'product_code': self.product.code,
                'product_description': self.product.description}
        cases = [({'formats': 'XLS', 'sunat_format': ''}, 200),
                 ({'formats': 'XLS', 'sunat_format': 'S'}, 200),
                 ({'formats': 'XLS', 'sunat_format': 'V'}, 200),
                 ({'formats': 'PDF', 'sunat_format': 'S'}, 200),
                 ({'formats': 'PDF', 'sunat_format': 'V'}, 200),
                 ({'formats': 'PDF', 'sunat_format': ''}, 404)]

        for extra, status in cases:
            with self.subTest(**extra):
                response = self.client.post(url, dict(base, **extra))
                self.assertEqual(status, response.status_code)

    def test_kardex_report(self):
        url = reverse('warehouse:kardex_report')
        base = {'warehouses': self.warehouse.pk, 'start_date': '01/01/2024',
                'end_date': '31/01/2024', 'product_code': '',
                'product_description': ''}
        cases = [({'formats': 'XLS', 'consolidated': 'P', 'sunat_format': ''}, 200),
                 ({'formats': 'XLS', 'consolidated': 'G', 'sunat_format': ''}, 200),
                 ({'formats': 'XLS', 'consolidated': '', 'sunat_format': 'S'}, 200),
                 ({'formats': 'XLS', 'consolidated': '', 'sunat_format': 'V'}, 200),
                 ({'formats': 'XLS', 'consolidated': '', 'sunat_format': ''}, 200),
                 ({'formats': 'PDF', 'consolidated': 'P', 'sunat_format': ''}, 200),
                 ({'formats': 'PDF', 'consolidated': 'G', 'sunat_format': ''}, 200),
                 ({'formats': 'PDF', 'consolidated': '', 'sunat_format': 'S'}, 200),
                 ({'formats': 'PDF', 'consolidated': '', 'sunat_format': 'V'}, 200),
                 ({'formats': 'PDF', 'consolidated': '', 'sunat_format': ''}, 404)]

        for extra, status in cases:
            with self.subTest(**extra):
                response = self.client.post(url, dict(base, **extra))
                self.assertEqual(status, response.status_code)

    def test_inventory_report(self):
        response = self.client.post(reverse('warehouse:inventory'),
                                    {'warehouse': self.warehouse.pk,
                                     'start_date': '01/01/2024'})

        self.assertEqual(200, response.status_code)

    def test_movement_pdf_report(self):
        movement = baker.make(Movement, movement_type=self.movement_type,
                              warehouse=self.warehouse)

        response = self.client.get(reverse('warehouse:movement_pdf', args=[movement.pk]))

        self.assertEqual(200, response.status_code)
        self.assertTrue(response.content.startswith(b'%PDF'))

    def test_movement_list_by_product(self):
        response = self.client.post(reverse('warehouse:movement_list_by_product'),
                                    {'warehouse': self.warehouse.pk,
                                     'start_date': '01/01/2024',
                                     'end_date': '31/01/2024',
                                     'product': self.product.code,
                                     'description': self.product.description})

        self.assertEqual(200, response.status_code)

    def test_price_reprocess(self):
        base = {'warehouse': self.warehouse.pk, 'start_date': '01/01/2024',
                'product': self.product.code, 'description': self.product.description}

        for selection in ('T', 'P'):
            with self.subTest(selection=selection):
                response = self.client.post(reverse('warehouse:price_reprocess'),
                                            dict(base, selection=selection))
                self.assertEqual(302, response.status_code)

    def test_product_stock(self):
        response = self.client.post(reverse('warehouse:product_stock'),
                                    {'warehouse': self.warehouse.pk,
                                     'start_date': '01/01/2024',
                                     'product': self.product.code,
                                     'description': self.product.description})

        self.assertEqual(200, response.status_code)

    def test_product_stock_list(self):
        response = self.client.get(reverse('warehouse:product_stock_list'),
                                   {'description': self.product.description,
                                    'warehouse': self.warehouse.pk},
                                   HTTP_X_REQUESTED_WITH='XMLHttpRequest')

        self.assertEqual(200, response.status_code)

    def test_verify_reference_required(self):
        response = self.client.get(reverse('warehouse:verify_reference_required'),
                                   {'type': self.movement_type.pk},
                                   HTTP_X_REQUESTED_WITH='XMLHttpRequest')

        self.assertEqual(200, response.status_code)

    def test_verify_stock_for_order(self):
        order = baker.make(Order, requester=baker.make('administration.Worker'))
        baker.make(OrderDetail, order=order, product=self.product, line_number=1,
                   quantity=2, status=OrderDetail.STATUS.PEND)

        response = self.client.get(reverse('warehouse:verify_stock_for_order'),
                                   {'warehouse': self.warehouse.code, 'order': order.code},
                                   HTTP_X_REQUESTED_WITH='XMLHttpRequest')

        self.assertEqual(200, response.status_code)
