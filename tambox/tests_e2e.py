"""Smoke test del flujo de negocio de punta a punta.

Encadena las vistas reales de los modulos -requerimiento, cotizacion, orden de
compra/servicio e ingreso/conformidad- verificando el estado que cada paso deja
en el modulo siguiente, que es lo que los tests por modulo no ven.
"""
from datetime import date
from decimal import Decimal

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from model_bakery import baker

from accounting.models import Configuration, PaymentMethod, Tax
from administration.models import ApprovalLevel, Office, Position, Worker
from purchases.models import (PurchaseOrder, Quotation, ServiceConformity,
                              ServiceOrder, Supplier)
from requirements.models import Requirement
from tambox.config import clear_cache
from warehouse.models import Kardex, Movement, MovementType, Warehouse


class BusinessFlowTest(TestCase):
    """Un solo grafo de datos para los dos escenarios: bienes y servicios."""

    def setUp(self):
        usuario = ApprovalLevel.objects.get_or_create(description='USUARIO')[0]
        ApprovalLevel.objects.get_or_create(description='JEFATURA',
                                            superior_level=usuario)
        self.user = User.objects.create_superuser('e2e', 'e2e@example.com', 'clave')
        self.client.force_login(self.user)

        self.office = baker.make(Office)
        self.worker = baker.make(Worker, user=self.user, signature='firmas/firma.png')
        baker.make(Position, office=self.office, worker=self.worker,
                   is_leadership=True, end_date=None)

        logistics = baker.make(Office)
        baker.make(Configuration, purchase_tax=baker.make(Tax, amount=Decimal('0.18')),
                   administration=logistics, logistics=logistics, budget=logistics)
        baker.make(Position, office=logistics,
                   worker=baker.make(Worker, signature='firmas/firma.png'),
                   is_leadership=True, start_date=date(2020, 1, 1), end_date=None)
        clear_cache()
        self.addCleanup(clear_cache)

        self.supplier = baker.make(Supplier, tax_id='12345678901',
                                   business_name='PROVEEDOR E2E',
                                   address='DIRECCION E2E')
        self.payment_method = baker.make(PaymentMethod)
        self.warehouse = baker.make(Warehouse)
        self.inbound_type = baker.make(MovementType, code='I01', increases=True,
                                       sunat_code='02')
        self.outbound_type = baker.make(MovementType, code='S01', increases=False,
                                        sunat_code='10')

    def create_requirement(self, product):
        data = {'code': '', 'reason': 'COMPRA E2E', 'date': '01/01/2024', 'month': '1',
                'year': '2024', 'notes': '', 'direct_delivery_to_requester': 'on',
                'form-TOTAL_FORMS': '1', 'form-INITIAL_FORMS': '0',
                'form-MIN_NUM_FORMS': '0', 'form-MAX_NUM_FORMS': '1000',
                'form-0-code': product.code, 'form-0-product': product.description,
                'form-0-unit': 'UND01', 'form-0-quantity': '10', 'form-0-use': 'USO'}

        response = self.client.post(reverse('requirements:requirement_create'), data)

        self.assertEqual(302, response.status_code)
        return Requirement.objects.get(reason='COMPRA E2E')

    def approve_requirement(self, requirement):
        response = self.client.post(
            reverse('requirements:requirement_approve', args=[requirement.approval.pk]),
            {'is_active': 'on', 'rejection_reason': ''})

        self.assertEqual(302, response.status_code)

    def create_quotation(self, requirement, requirement_detail, quantity):
        data = {'tax_id': self.supplier.tax_id, 'business_name': self.supplier.business_name,
                'address': self.supplier.address, 'reference': requirement.pk,
                'order': '', 'code': '', 'date': '01/01/2024', 'notes': '',
                'form-TOTAL_FORMS': '1', 'form-INITIAL_FORMS': '0',
                'form-MIN_NUM_FORMS': '0', 'form-MAX_NUM_FORMS': '1000',
                'form-0-requirement': requirement_detail.pk,
                'form-0-code': requirement_detail.product.code,
                'form-0-name': requirement_detail.product.description,
                'form-0-unit': 'UND01', 'form-0-quantity': str(quantity)}

        response = self.client.post(reverse('purchases:quotation_create'), data)

        self.assertEqual(302, response.status_code)
        return Quotation.objects.get(requirement=requirement, supplier=self.supplier)

    def test_goods_flow(self):
        product = baker.make('products.Product')
        requirement = self.create_requirement(product)
        requirement_detail = requirement.details.get()
        self.approve_requirement(requirement)

        quotation = self.create_quotation(requirement, requirement_detail, 10)
        quotation_detail = quotation.details.get()
        requirement_detail.refresh_from_db()
        requirement.refresh_from_db()
        self.assertEqual(Decimal('10'), requirement_detail.quoted_quantity)
        self.assertEqual(Requirement.STATUS.COTIZ, requirement.status)

        data = {'tax_id': self.supplier.tax_id, 'business_name': self.supplier.business_name,
                'address': self.supplier.address, 'reference': quotation.code,
                'current_tax': '18', 'subtotal': '0', 'tax': '0', 'total': '0',
                'total_in_words': 'CERO', 'code': '', 'date': '01/01/2024',
                'notes': '', 'payment_method': self.payment_method.pk,
                'form-TOTAL_FORMS': '1', 'form-INITIAL_FORMS': '0',
                'form-MIN_NUM_FORMS': '0', 'form-MAX_NUM_FORMS': '1000',
                'form-0-quotation': quotation_detail.pk, 'form-0-code': product.pk,
                'form-0-name': product.description, 'form-0-unit': 'UND01',
                'form-0-quantity': '10', 'form-0-price': '3', 'form-0-tax': '1',
                'form-0-amount': '30'}

        response = self.client.post(reverse('purchases:purchase_order_create'), data)

        self.assertEqual(302, response.status_code)
        purchase_order = PurchaseOrder.objects.get(quotation=quotation)
        purchase_order_detail = purchase_order.details.get()
        quotation_detail.refresh_from_db()
        requirement_detail.refresh_from_db()
        requirement.refresh_from_db()
        self.assertEqual(Decimal('10'), quotation_detail.purchased_quantity)
        self.assertEqual(Decimal('10'), requirement_detail.purchased_quantity)
        self.assertEqual(Requirement.STATUS.COMP, requirement.status)

        data = {'movement_id': '', 'movement_type': self.inbound_type.pk,
                'document_type': '', 'series': '', 'number': '',
                'warehouse': self.warehouse.pk, 'office': '', 'notes': '',
                'date': '01/01/2024', 'time': '08:30:00',
                'reference_document': purchase_order.code,
                'receiver_dni': '', 'receiver': '', 'details_count': '0', 'total': '0',
                'form-TOTAL_FORMS': '1', 'form-INITIAL_FORMS': '0',
                'form-MIN_NUM_FORMS': '0', 'form-MAX_NUM_FORMS': '1000',
                'form-0-purchase_order': purchase_order_detail.pk, 'form-0-code': product.pk,
                'form-0-name': product.description, 'form-0-unit': 'UND01',
                'form-0-quantity': '10', 'form-0-price': '3', 'form-0-amount': '30'}

        response = self.client.post(reverse('warehouse:inbound_create'), data)

        self.assertEqual(302, response.status_code)
        purchase_order.refresh_from_db()
        purchase_order_detail.refresh_from_db()
        requirement_detail.refresh_from_db()
        requirement.refresh_from_db()
        self.assertEqual(Decimal('10'), purchase_order_detail.received_quantity)
        self.assertEqual(Decimal('10'), requirement_detail.served_quantity)
        self.assertEqual(PurchaseOrder.STATUS.ING, purchase_order.status)
        self.assertEqual(Requirement.STATUS.ATEN, requirement.status)
        movement = Movement.objects.get(reference=purchase_order)
        self.assertEqual(1, Kardex.objects.filter(movement=movement).count())

    def test_service_flow(self):
        service = baker.make('products.Product', is_service=True)
        requirement = self.create_requirement(service)
        requirement_detail = requirement.details.get()
        self.approve_requirement(requirement)

        quotation = self.create_quotation(requirement, requirement_detail, 10)
        quotation_detail = quotation.details.get()

        data = {'tax_id': self.supplier.tax_id, 'business_name': self.supplier.business_name,
                'address': self.supplier.address, 'reference': quotation.pk,
                'subtotal': '0', 'tax': '0', 'total': '0', 'total_in_words': 'CERO',
                'code': '', 'process': '', 'notes': '', 'report_name': '',
                'date': '01/01/2024', 'payment_method': self.payment_method.pk,
                'form-TOTAL_FORMS': '1', 'form-INITIAL_FORMS': '0',
                'form-MIN_NUM_FORMS': '0', 'form-MAX_NUM_FORMS': '1000',
                'form-0-quotation': quotation_detail.pk, 'form-0-code': service.pk,
                'form-0-name': service.description, 'form-0-unit': 'UND01',
                'form-0-quantity': '10', 'form-0-price': '3', 'form-0-amount': '30'}

        response = self.client.post(reverse('purchases:service_order_create'), data)

        self.assertEqual(302, response.status_code)
        service_order = ServiceOrder.objects.get(quotation=quotation)
        service_order_detail = service_order.details.get()
        requirement_detail.refresh_from_db()
        self.assertEqual(Decimal('10'), requirement_detail.purchased_quantity)

        data = {'reference': service_order.pk, 'subtotal': '0', 'total': '0',
                'total_in_words': 'CERO', 'code': '', 'supporting_document': '',
                'date': '01/01/2024',
                'form-TOTAL_FORMS': '1', 'form-INITIAL_FORMS': '0',
                'form-MIN_NUM_FORMS': '0', 'form-MAX_NUM_FORMS': '1000',
                'form-0-service_order': service_order_detail.pk, 'form-0-quantity': '10',
                'form-0-service': service.description, 'form-0-use': 'USO',
                'form-0-price': '3', 'form-0-amount': '30'}

        response = self.client.post(reverse('purchases:service_conformity_create'), data)

        self.assertEqual(302, response.status_code)
        service_order.refresh_from_db()
        service_order_detail.refresh_from_db()
        requirement_detail.refresh_from_db()
        requirement.refresh_from_db()
        self.assertEqual(Decimal('10'), service_order_detail.conformed_quantity)
        self.assertEqual(Decimal('10'), requirement_detail.served_quantity)
        self.assertEqual(ServiceOrder.STATUS.CONF, service_order.status)
        self.assertEqual(Requirement.STATUS.ATEN, requirement.status)
        self.assertEqual(1, ServiceConformity.objects.filter(service_order=service_order).count())
