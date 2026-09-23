"""Validaciones de los formularios de requerimientos."""
from django.core.exceptions import ValidationError
from django.test import TestCase
from model_bakery import baker

from administration.models import ApprovalLevel, Office, Position, Worker
from requirements.forms import RequirementApprovalForm, RequirementDetailForm
from requirements.models import Requirement


class RequirementDetailFormTest(TestCase):

    def test_code_must_exist(self):
        form = RequirementDetailForm()
        form.cleaned_data = {'code': 'NO-EXISTE'}

        with self.assertRaises(ValidationError):
            form.clean_code()

    def test_valid_code(self):
        product = baker.make('products.Product')
        form = RequirementDetailForm()
        form.cleaned_data = {'code': product.code}

        self.assertEqual(product.code, form.clean_code())

    def test_quantity_cannot_be_zero(self):
        form = RequirementDetailForm()
        form.cleaned_data = {'quantity': 0}

        with self.assertRaises(ValidationError):
            form.clean_quantity()

    def test_valid_quantity(self):
        form = RequirementDetailForm()
        form.cleaned_data = {'quantity': 5}

        self.assertEqual(5, form.clean_quantity())


class RequirementApprovalFormTest(TestCase):

    def approval(self):
        """El nivel USUARIO delega en la oficina del propio requerimiento."""
        ApprovalLevel.objects.get_or_create(description='USUARIO')
        self.office = baker.make(Office)
        worker = baker.make(Worker)
        baker.make(Position, office=self.office, worker=worker, end_date=None)
        requirement = baker.make(Requirement, code='', requester=worker,
                                 office=self.office)
        return requirement.approval

    def test_sends_the_mail_to_the_superior(self):
        approval = self.approval()
        boss = baker.make(Worker, user=baker.make('auth.User', email='jefe@example.com'))
        baker.make(Position, office=self.office, worker=boss, is_leadership=True,
                   is_active=True)

        form = RequirementApprovalForm(instance=approval, request=None,
                                       data={'is_active': 'on', 'rejection_reason': ''})

        self.assertTrue(form.is_valid(), form.errors)

    def test_without_the_superior_position_is_invalid(self):
        form = RequirementApprovalForm(instance=self.approval(), request=None,
                                       data={'is_active': 'on', 'rejection_reason': ''})

        self.assertFalse(form.is_valid())
