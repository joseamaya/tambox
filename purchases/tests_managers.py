"""Logica de negocio de los managers de compras.

`QuotationDetailManager` reparte la cantidad cotizada en el detalle del
requerimiento; `ServiceConformityDetailManager` hace lo propio con la cantidad
conformada en el detalle de la orden de servicio.
"""
from decimal import Decimal

from django.test import TestCase
from model_bakery import baker

from administration.models import ApprovalLevel, Office, Position, Worker
from purchases.models import (PurchaseOrder, PurchaseOrderDetail, Quotation,
                              QuotationDetail, ServiceConformity,
                              ServiceConformityDetail, ServiceOrder,
                              ServiceOrderDetail, Supplier)
from requirements.models import Requirement, RequirementDetail


def create_requirement(**kwargs):
    ApprovalLevel.objects.get_or_create(description='USUARIO')
    office = baker.make(Office)
    worker = baker.make(Worker)
    baker.make(Position, office=office, worker=worker, end_date=None)
    return baker.make(Requirement, code='', requester=worker, office=office, **kwargs)


class QuotationDetailManagerTest(TestCase):

    def test_without_reference_just_saves(self):
        quotation = baker.make(Quotation, supplier=baker.make(Supplier))
        detail = QuotationDetail(line_number=1, quotation=quotation,
                                 requirement_detail=None, quantity=Decimal('2'))

        QuotationDetail.objects.bulk_create([detail], None, None)

        self.assertTrue(QuotationDetail.objects.filter(pk=detail.pk).exists())

    def test_with_requirement_updates_the_quoted_quantity(self):
        requirement = create_requirement()
        requirement_detail = baker.make(RequirementDetail, requirement=requirement,
                                        product=baker.make('products.Product'),
                                        quantity=Decimal('10'),
                                        quoted_quantity=Decimal('0'))
        quotation = baker.make(Quotation, requirement=requirement,
                               supplier=baker.make(Supplier))
        detail = QuotationDetail(line_number=1, quotation=quotation,
                                 requirement_detail=requirement_detail,
                                 quantity=Decimal('4'))

        QuotationDetail.objects.bulk_create([detail], requirement, None)

        requirement_detail.refresh_from_db()
        self.assertEqual(Decimal('4'), requirement_detail.quoted_quantity)


class OrderDetailManagerTest(TestCase):
    """`OrderDetailManager` (el de `PurchaseOrderDetail`) descuenta la cantidad
    comprada en la cotizacion y el requerimiento."""

    def chain(self):
        requirement = create_requirement()
        requirement_detail = baker.make(RequirementDetail, requirement=requirement,
                                        product=baker.make('products.Product'),
                                        quantity=Decimal('10'),
                                        purchased_quantity=Decimal('0'))
        quotation = baker.make(Quotation, requirement=requirement,
                               supplier=baker.make(Supplier))
        quotation_detail = baker.make(QuotationDetail, quotation=quotation,
                                      requirement_detail=requirement_detail,
                                      quantity=Decimal('10'),
                                      purchased_quantity=Decimal('0'))
        order = baker.make(PurchaseOrder, quotation=quotation,
                           supplier=baker.make(Supplier))
        return requirement_detail, quotation, quotation_detail, order

    def test_without_reference_just_saves(self):
        order = baker.make(PurchaseOrder, supplier=baker.make(Supplier))
        detail = PurchaseOrderDetail(line_number=1, order=order,
                                     quotation_detail=None,
                                     product=baker.make('products.Product'),
                                     quantity=Decimal('2'), price=Decimal('3'))

        PurchaseOrderDetail.objects.bulk_create([detail], None)

        self.assertTrue(PurchaseOrderDetail.objects.filter(pk=detail.pk).exists())

    def test_with_quotation_updates_the_purchased_quantity(self):
        requirement_detail, quotation, quotation_detail, order = self.chain()
        baker.make(Quotation, supplier=baker.make(Supplier))
        detail = PurchaseOrderDetail(line_number=1, order=order,
                                     quotation_detail=quotation_detail,
                                     quantity=Decimal('4'), price=Decimal('3'))

        PurchaseOrderDetail.objects.bulk_create([detail], quotation)

        quotation_detail.refresh_from_db()
        requirement_detail.refresh_from_db()
        self.assertEqual(Decimal('4'), quotation_detail.purchased_quantity)
        self.assertEqual(Decimal('4'), requirement_detail.purchased_quantity)

    def test_update_quotation_details_discards_pending(self):
        requirement_detail, quotation, quotation_detail, order = self.chain()
        requirement_detail.status = RequirementDetail.STATUS.COMP
        requirement_detail.save()
        pending = baker.make(QuotationDetail, quotation=quotation,
                             requirement_detail=requirement_detail,
                             line_number=2, quantity=Decimal('1'))

        PurchaseOrderDetail.objects.update_quotation_details(requirement_detail)

        pending.refresh_from_db()
        self.assertEqual(QuotationDetail.STATUS.DESC, pending.status)


class ServiceConformityDetailManagerTest(TestCase):

    def chain(self):
        requirement = create_requirement()
        requirement_detail = baker.make(RequirementDetail, requirement=requirement,
                                        product=baker.make('products.Product'),
                                        quantity=Decimal('10'),
                                        served_quantity=Decimal('0'))
        quotation = baker.make(Quotation, requirement=requirement,
                               supplier=baker.make(Supplier))
        quotation_detail = baker.make(QuotationDetail, quotation=quotation,
                                      requirement_detail=requirement_detail,
                                      quantity=Decimal('10'))
        service_order = baker.make(ServiceOrder, quotation=quotation,
                                   supplier=baker.make(Supplier))
        service_order_detail = baker.make(ServiceOrderDetail, order=service_order,
                                          quotation_detail=quotation_detail,
                                          quantity=Decimal('10'),
                                          conformed_quantity=Decimal('0'))
        conformity = baker.make(ServiceConformity, service_order=service_order)
        return requirement_detail, service_order, service_order_detail, conformity

    def test_without_reference_just_saves(self):
        conformity = baker.make(ServiceConformity,
                                service_order=baker.make(ServiceOrder,
                                                         supplier=baker.make(Supplier)))
        detail = ServiceConformityDetail(line_number=1, conformity=conformity,
                                         service_order_detail=None,
                                         quantity=Decimal('2'))

        ServiceConformityDetail.objects.bulk_create([detail], None)

        self.assertTrue(ServiceConformityDetail.objects.filter(pk=detail.pk).exists())

    def test_with_service_order_updates_the_conformed_quantity(self):
        requirement_detail, service_order, service_order_detail, conformity = self.chain()
        detail = ServiceConformityDetail(line_number=1, conformity=conformity,
                                         service_order_detail=service_order_detail,
                                         quantity=Decimal('4'))

        ServiceConformityDetail.objects.bulk_create([detail], service_order)

        service_order_detail.refresh_from_db()
        self.assertEqual(Decimal('4'), service_order_detail.conformed_quantity)
