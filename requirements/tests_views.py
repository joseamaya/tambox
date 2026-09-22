"""Vistas de requerimientos.

El usuario que navega necesita su `worker` con firma y un puesto de jefatura
activo: de ahi salen la oficina, la cadena de aprobaciones y el acceso a la
bandeja de aprobaciones. El requerimiento se crea con `code=''` para que
`save()` genere el codigo y arme su aprobacion.
"""
from datetime import date

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from model_bakery import baker

from administration.models import ApprovalLevel, Office, Position, Worker
from purchases.models import Quotation, Supplier
from requirements.models import Requirement
from tambox.config import clear_cache


class RequirementsViewsTest(TestCase):

    def setUp(self):
        ApprovalLevel.objects.get_or_create(description='USUARIO')
        self.user = User.objects.create_superuser('a', 'a@example.com', 'clave')
        self.client.force_login(self.user)
        self.office = baker.make(Office)
        self.worker = baker.make(Worker, user=self.user, signature='firmas/firma.png')
        baker.make(Position, office=self.office, worker=self.worker,
                   is_leadership=True, end_date=None)
        self.requirement = baker.make(Requirement, code='', requester=self.worker,
                                      office=self.office)

        logistics = baker.make(Office)
        baker.make('accounting.Configuration', administration=logistics,
                   logistics=logistics, budget=logistics)
        baker.make(Position, office=logistics,
                   worker=baker.make(Worker, signature='firmas/firma.png'),
                   is_leadership=True, start_date=date(2020, 1, 1), end_date=None)
        clear_cache()
        self.addCleanup(clear_cache)

    def test_dashboard(self):
        self.assertEqual(200, self.client.get(reverse('requirements:dashboard')).status_code)

    def test_requirement_list(self):
        response = self.client.get(reverse('requirements:requirement_list'))

        self.assertEqual(200, response.status_code)
        self.assertContains(response, self.requirement.code)

    def test_requirement_detail(self):
        response = self.client.get(
            reverse('requirements:requirement_detail', args=[self.requirement.code]))

        self.assertEqual(200, response.status_code)

    def test_requirement_approval_list(self):
        response = self.client.get(reverse('requirements:requirement_approval_list'))

        self.assertEqual(200, response.status_code)

    def test_quotation_list_by_requirement(self):
        baker.make(Quotation, requirement=self.requirement,
                   supplier=baker.make(Supplier))

        response = self.client.get(
            reverse('requirements:quotation_list_by_requirement',
                    args=[self.requirement.pk]))

        self.assertEqual(200, response.status_code)

    def test_requirement_transfer(self):
        response = self.client.get(reverse('requirements:requirement_transfer'))

        self.assertEqual(200, response.status_code)

    def test_requirement_pdf(self):
        response = self.client.get(
            reverse('requirements:requirement_pdf', args=[self.requirement.code]))

        self.assertEqual(200, response.status_code)
        self.assertTrue(response.content.startswith(b'%PDF'))

    def test_requirement_excel_report(self):
        response = self.client.get(reverse('requirements:requirement_excel_report'))

        self.assertEqual(200, response.status_code)

    def test_requirement_approve(self):
        user_level = ApprovalLevel.objects.get(description='USUARIO')
        ApprovalLevel.objects.create(description='JEFATURA', superior_level=user_level)
        approval = self.requirement.approval

        response = self.client.post(
            reverse('requirements:requirement_approve', args=[approval.pk]),
            {'is_active': 'on', 'rejection_reason': ''})

        self.assertEqual(302, response.status_code)

    def test_requirement_create(self):
        baker.make('products.Product', code='P000000001')
        data = {'code': '', 'reason': 'MOTIVO', 'date': '01/01/2024', 'month': '1',
                'year': '2024', 'notes': '', 'direct_delivery_to_requester': 'on',
                'form-TOTAL_FORMS': '0', 'form-INITIAL_FORMS': '0',
                'form-MIN_NUM_FORMS': '0', 'form-MAX_NUM_FORMS': '1000'}

        response = self.client.post(reverse('requirements:requirement_create'), data)

        self.assertEqual(302, response.status_code)
        self.assertTrue(Requirement.objects.filter(reason='MOTIVO').exists())

    def test_requirement_delete(self):
        response = self.client.post(reverse('requirements:requirement_delete'),
                                    {'code': self.requirement.code},
                                    HTTP_X_REQUESTED_WITH='XMLHttpRequest')

        self.assertEqual(200, response.status_code)
        self.requirement.refresh_from_db()
        self.assertEqual(Requirement.STATUS.CANC, self.requirement.status)

