"""Metodos y propiedades de dominio de los modelos de compras.

Los precios e importes dependen de `Configuration.purchase_tax` y de si la orden
trae el impuesto incluido (`with_tax`), asi que se fijan los dos caminos.
"""
from datetime import date
from decimal import Decimal

from django.test import TestCase
from model_bakery import baker

from accounting.models import Configuration, Tax
from administration.models import ApprovalLevel, Office, Position, Worker
from purchases.models import (PurchaseOrder, PurchaseOrderDetail, Quotation,
                              QuotationDetail, ServiceConformity,
                              ServiceConformityDetail, ServiceOrder,
                              ServiceOrderDetail, Supplier)
from requirements.models import Requirement, RequirementDetail
from tambox.config import clear_cache


def create_requirement(**kwargs):
    ApprovalLevel.objects.get_or_create(description='USUARIO')
    office = baker.make(Office)
    worker = baker.make(Worker)
    baker.make(Position, office=office, worker=worker, end_date=None)
    return baker.make(Requirement, code='', requester=worker, office=office, **kwargs)


class PurchaseOrderDetailPriceTest(TestCase):

    def setUp(self):
        baker.make(Configuration, purchase_tax=baker.make(Tax, amount=Decimal('0.18')))
        clear_cache()
        self.addCleanup(clear_cache)

    def detail(self, with_tax):
        order = baker.make(PurchaseOrder, supplier=baker.make(Supplier),
                           with_tax=with_tax)
        return baker.make(PurchaseOrderDetail, order=order, quantity=Decimal('2'),
                          price=Decimal('118'))

    def test_with_tax_included(self):
        detail = self.detail(with_tax=True)

        self.assertEqual(Decimal('118'), detail.price_with_tax)
        self.assertEqual(Decimal('100'), detail.price_without_tax)
        self.assertEqual(Decimal('200'), detail.amount_without_tax)
        self.assertEqual(Decimal('236'), detail.amount_with_tax)
        self.assertEqual(Decimal('36'), detail.tax)

    def test_without_tax(self):
        detail = self.detail(with_tax=False)

        self.assertEqual(Decimal('139.24'), detail.price_with_tax)
        self.assertEqual(Decimal('118'), detail.price_without_tax)
        self.assertEqual(Decimal('236'), detail.amount_without_tax)
        self.assertEqual(Decimal('278.48'), detail.amount_with_tax)
        self.assertEqual(Decimal('42.48'), detail.tax)


class PurchaseOrderTest(TestCase):

    def setUp(self):
        baker.make(Configuration, purchase_tax=baker.make(Tax, amount=Decimal('0.18')))
        clear_cache()
        self.addCleanup(clear_cache)

    def chain(self):
        requirement = create_requirement()
        requirement_detail = baker.make(RequirementDetail, requirement=requirement,
                                        product=baker.make('products.Product'),
                                        quantity=Decimal('10'),
                                        purchased_quantity=Decimal('4'))
        quotation = baker.make(Quotation, requirement=requirement,
                               supplier=baker.make(Supplier))
        quotation_detail = baker.make(QuotationDetail, quotation=quotation,
                                      requirement_detail=requirement_detail,
                                      quantity=Decimal('10'),
                                      purchased_quantity=Decimal('4'))
        order = baker.make(PurchaseOrder, quotation=quotation,
                           supplier=baker.make(Supplier))
        return requirement_detail, quotation, quotation_detail, order

    def test_set_status(self):
        order = baker.make(PurchaseOrder, supplier=baker.make(Supplier))

        self.assertEqual(PurchaseOrder.STATUS.PEND, order.set_status())
        baker.make(PurchaseOrderDetail, order=order, quantity=Decimal('10'),
                   received_quantity=Decimal('4'))
        self.assertEqual(PurchaseOrder.STATUS.ING_PARC, order.set_status())
        PurchaseOrderDetail.objects.filter(order=order).update(received_quantity=Decimal('10'))
        self.assertEqual(PurchaseOrder.STATUS.ING, order.set_status())

    def test_delete_reference(self):
        requirement_detail, quotation, quotation_detail, order = self.chain()
        baker.make(PurchaseOrderDetail, order=order,
                   quotation_detail=quotation_detail, quantity=Decimal('4'),
                   price=Decimal('3'))

        order.delete_reference()

        quotation_detail.refresh_from_db()
        requirement_detail.refresh_from_db()
        self.assertEqual(Decimal('0'), quotation_detail.purchased_quantity)
        self.assertEqual(Decimal('0'), requirement_detail.purchased_quantity)

    def test_total_and_words(self):
        order = baker.make(PurchaseOrder, supplier=baker.make(Supplier))
        baker.make(PurchaseOrderDetail, order=order, quantity=Decimal('2'),
                   price=Decimal('5'))

        self.assertEqual(Decimal('10'), order.subtotal)
        self.assertEqual(Decimal('1.8'), order.tax)
        self.assertEqual(Decimal('11.8'), order.total)
        self.assertTrue(order.total_in_words)


class ServiceOrderTest(TestCase):

    def chain(self):
        requirement = create_requirement()
        requirement_detail = baker.make(RequirementDetail, requirement=requirement,
                                        product=baker.make('products.Product'),
                                        quantity=Decimal('10'),
                                        purchased_quantity=Decimal('4'))
        quotation = baker.make(Quotation, requirement=requirement,
                               supplier=baker.make(Supplier))
        quotation_detail = baker.make(QuotationDetail, quotation=quotation,
                                      requirement_detail=requirement_detail,
                                      quantity=Decimal('10'),
                                      purchased_quantity=Decimal('4'))
        order = baker.make(ServiceOrder, quotation=quotation,
                           supplier=baker.make(Supplier))
        return requirement_detail, quotation, quotation_detail, order

    def test_generate_code(self):
        order = baker.make(ServiceOrder, code='', supplier=baker.make(Supplier),
                           date=date(2024, 1, 1))

        self.assertTrue(order.code.startswith('OS2024'))

    def test_set_status(self):
        order = baker.make(ServiceOrder, supplier=baker.make(Supplier))

        self.assertEqual(ServiceOrder.STATUS.PEND, order.set_status())
        baker.make(ServiceOrderDetail, order=order, quantity=Decimal('10'),
                   conformed_quantity=Decimal('4'), price=Decimal('3'))
        self.assertEqual(ServiceOrder.STATUS.CONF_PARC, order.set_status())
        ServiceOrderDetail.objects.filter(order=order).update(conformed_quantity=Decimal('10'))
        self.assertEqual(ServiceOrder.STATUS.CONF, order.set_status())

    def test_delete_reference_updates_the_requirement(self):
        requirement_detail, quotation, quotation_detail, order = self.chain()
        baker.make(ServiceOrderDetail, order=order,
                   quotation_detail=quotation_detail, quantity=Decimal('4'),
                   price=Decimal('3'))

        order.delete_reference()

        quotation_detail.refresh_from_db()
        requirement_detail.refresh_from_db()
        self.assertEqual(Decimal('0'), quotation_detail.purchased_quantity)
        self.assertEqual(Decimal('0'), requirement_detail.purchased_quantity)


class ServiceConformityTest(TestCase):

    def test_save_generates_code(self):
        conformity = baker.make(ServiceConformity, code='',
                                service_order=baker.make(ServiceOrder,
                                                         supplier=baker.make(Supplier)),
                                date=date(2024, 1, 1))

        self.assertTrue(conformity.code.startswith('CS2024'))

    def test_delete_reference(self):
        requirement = create_requirement()
        requirement_detail = baker.make(RequirementDetail, requirement=requirement,
                                        product=baker.make('products.Product'),
                                        quantity=Decimal('10'),
                                        served_quantity=Decimal('4'))
        quotation = baker.make(Quotation, requirement=requirement,
                               supplier=baker.make(Supplier))
        quotation_detail = baker.make(QuotationDetail, quotation=quotation,
                                      requirement_detail=requirement_detail,
                                      quantity=Decimal('10'))
        order = baker.make(ServiceOrder, quotation=quotation,
                           supplier=baker.make(Supplier))
        order_detail = baker.make(ServiceOrderDetail, order=order,
                                  quotation_detail=quotation_detail,
                                  quantity=Decimal('10'),
                                  conformed_quantity=Decimal('4'),
                                  price=Decimal('3'))
        conformity = baker.make(ServiceConformity, service_order=order)
        baker.make(ServiceConformityDetail, conformity=conformity,
                   service_order_detail=order_detail, quantity=Decimal('4'))

        conformity.delete_reference()

        order_detail.refresh_from_db()
        requirement_detail.refresh_from_db()
        self.assertEqual(Decimal('0'), order_detail.conformed_quantity)
        self.assertEqual(Decimal('0'), requirement_detail.served_quantity)
        order.refresh_from_db()
        self.assertEqual(ServiceOrder.STATUS.PEND, order.status)


class QuotationTest(TestCase):

    def test_set_status_purchased(self):
        requirement = create_requirement()
        quotation = baker.make(Quotation, requirement=requirement,
                               supplier=baker.make(Supplier))
        baker.make(QuotationDetail, quotation=quotation, line_number=1,
                   requirement_detail=None, quantity=Decimal('10'),
                   purchased_quantity=Decimal('0'))
        self.assertEqual(Quotation.STATUS.DESC, quotation.set_status_purchased())

        QuotationDetail.objects.filter(quotation=quotation).update(
            purchased_quantity=Decimal('4'))
        self.assertEqual(Quotation.STATUS.ELEG_PARC, quotation.set_status_purchased())

        QuotationDetail.objects.filter(quotation=quotation).update(
            purchased_quantity=Decimal('10'))
        self.assertEqual(Quotation.STATUS.ELEG, quotation.set_status_purchased())
