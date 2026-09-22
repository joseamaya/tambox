"""Validaciones de los formularios de almacen.

`clean_hasta` no coincidia con el campo `end_date`, asi que Django nunca lo
llamaba y el informe no extendia el rango un dia; ahora es `clean_end_date`.
"""
import datetime

from django.core.exceptions import ValidationError
from django.test import TestCase
from model_bakery import baker

from warehouse.forms import MovementForm, MovementReportForm, OutboundDetailForm
from warehouse.models import MovementType


class EndDateTest(TestCase):

    def test_movement_report_end_date_adds_a_day(self):
        form = MovementReportForm()
        form.cleaned_data = {'end_date': datetime.datetime(2024, 1, 15)}

        self.assertEqual(datetime.datetime(2024, 1, 16), form.clean_end_date())

    def test_product_movement_end_date_adds_a_day(self):
        from warehouse.forms import ProductMovementForm

        form = ProductMovementForm()
        form.cleaned_data = {'end_date': datetime.datetime(2024, 1, 15)}

        self.assertEqual(datetime.datetime(2024, 1, 16), form.clean_end_date())


class OutboundDetailFormTest(TestCase):

    def test_quantity_cannot_be_zero(self):
        form = OutboundDetailForm()
        form.cleaned_data = {'quantity': 0}

        with self.assertRaises(ValidationError):
            form.clean_quantity()

    def test_quantity_cannot_be_negative(self):
        form = OutboundDetailForm()
        form.cleaned_data = {'quantity': -1}

        with self.assertRaises(ValidationError):
            form.clean_quantity()

    def test_valid_quantity(self):
        form = OutboundDetailForm()
        form.cleaned_data = {'quantity': 5}

        self.assertEqual(5, form.clean_quantity())


class MovementFormReceiverDniTest(TestCase):

    def test_sale_with_unknown_producer_is_invalid(self):
        movement_type = baker.make(MovementType, code='S01', increases=False, is_sale=True)
        form = MovementForm(movement_type='S')
        form.cleaned_data = {'receiver_dni': '12345678', 'movement_type': movement_type}

        with self.assertRaises(ValidationError):
            form.clean_receiver_dni()

    def test_empty_dni_is_allowed(self):
        form = MovementForm(movement_type='I')
        form.cleaned_data = {'receiver_dni': '', 'movement_type': None}

        self.assertEqual('', form.clean_receiver_dni())
