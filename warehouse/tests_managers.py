"""Logica de negocio de `MovementDetailManager`.

`bulk_create` decide, segun la referencia, si hay que repartir la cantidad
recibida en el detalle de la orden de compra, en el detalle del pedido, o solo
guardar el movimiento.
"""
from decimal import Decimal

from django.test import TestCase
from django.utils import timezone
from model_bakery import baker

from purchases.models import PurchaseOrder, PurchaseOrderDetail
from warehouse.models import Movement, MovementDetail, MovementType, Order, OrderDetail, Warehouse


class MovementDetailManagerTest(TestCase):

    def setUp(self):
        self.product = baker.make('products.Product')
        self.warehouse = baker.make(Warehouse)
        self.movement_type = baker.make(MovementType, code='I01', increases=True)

    def movement(self):
        return baker.make(Movement, movement_id='', movement_type=self.movement_type,
                          warehouse=self.warehouse, operation_date=timezone.now())

    def test_without_reference_just_saves(self):
        detail = MovementDetail(line_number=1, movement=self.movement(),
                                product=self.product, quantity=Decimal('2'),
                                price=Decimal('3'), amount=Decimal('6'))

        MovementDetail.objects.bulk_create([detail], None, None)

        self.assertTrue(MovementDetail.objects.filter(pk=detail.pk).exists())

    def test_with_order_updates_the_order_detail(self):
        order = baker.make(Order)
        order_detail = baker.make(OrderDetail, order=order, product=self.product,
                                  quantity=Decimal('10'), served_quantity=Decimal('0'))
        detail = MovementDetail(line_number=1, movement=self.movement(),
                                order_detail=order_detail, product=self.product,
                                quantity=Decimal('4'), price=Decimal('3'),
                                amount=Decimal('12'))

        MovementDetail.objects.bulk_create([detail], None, order)

        order_detail.refresh_from_db()
        self.assertEqual(Decimal('4'), order_detail.served_quantity)

    def test_with_purchase_order_updates_the_received_quantity(self):
        purchase_order = baker.make(PurchaseOrder, quotation=None)
        purchase_order_detail = baker.make(PurchaseOrderDetail, order=purchase_order,
                                           quotation_detail=None, product=self.product,
                                           quantity=Decimal('10'),
                                           received_quantity=Decimal('0'))
        detail = MovementDetail(line_number=1, movement=self.movement(),
                                purchase_order_detail=purchase_order_detail,
                                product=self.product, quantity=Decimal('4'),
                                price=Decimal('3'), amount=Decimal('12'))

        MovementDetail.objects.bulk_create([detail], purchase_order, None)

        purchase_order_detail.refresh_from_db()
        self.assertEqual(Decimal('4'), purchase_order_detail.received_quantity)
