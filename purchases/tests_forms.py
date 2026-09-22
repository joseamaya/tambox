"""Validaciones de los formularios de compras.

Los `clean_*` son los que evitan que entre una cotizacion duplicada o un codigo
con el largo equivocado; hasta ahora solo se ejercitaban por casualidad.
"""
from django.core.exceptions import ValidationError
from django.test import TestCase
from model_bakery import baker

from purchases.forms import PurchaseOrderForm, QuotationForm, SupplierForm
from purchases.models import Quotation, ServiceOrder, Supplier


class SupplierFormTest(TestCase):

    def test_tax_id_must_have_eleven_digits(self):
        form = SupplierForm()
        form.cleaned_data = {'tax_id': '123'}

        with self.assertRaises(ValidationError):
            form.clean_tax_id()

    def test_tax_id_valid(self):
        form = SupplierForm()
        form.cleaned_data = {'tax_id': '12345678901'}

        self.assertEqual('12345678901', form.clean_tax_id())


class QuotationFormTest(TestCase):

    def test_order_code_wrong_length(self):
        form = QuotationForm()
        form.cleaned_data = {'order': '123'}

        with self.assertRaises(ValidationError):
            form.clean_order()

    def test_order_code_empty_is_allowed(self):
        form = QuotationForm()
        form.cleaned_data = {'order': ''}

        self.assertEqual('', form.clean_order())

    def test_order_code_already_exists(self):
        baker.make(ServiceOrder, code='123456789012')
        form = QuotationForm()
        form.cleaned_data = {'order': '123456789012'}

        with self.assertRaises(ValidationError):
            form.clean_order()

    def test_duplicate_quotation_is_rejected(self):
        supplier = baker.make(Supplier, tax_id='12345678901')
        quotation = baker.make(Quotation, supplier=supplier)
        form = QuotationForm()
        form.cleaned_data = {'tax_id': '12345678901',
                             'reference': quotation.requirement_id}

        with self.assertRaises(ValidationError):
            form.clean()


class PurchaseOrderFormTest(TestCase):

    def test_code_wrong_length(self):
        form = PurchaseOrderForm()
        form.cleaned_data = {'code': '123'}

        with self.assertRaises(ValidationError):
            form.clean_code()

    def test_code_empty_is_allowed(self):
        form = PurchaseOrderForm()
        form.cleaned_data = {'code': ''}

        self.assertEqual('', form.clean_code())
