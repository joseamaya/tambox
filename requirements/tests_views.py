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

    def test_lists_return_htmx_fragment_and_search(self):
        requirement_fragment = self.client.get(
            reverse('requirements:requirement_list'), {'q': self.requirement.code},
            HTTP_HX_REQUEST='true')

        self.assertEqual(200, requirement_fragment.status_code)
        self.assertNotContains(requirement_fragment, '<html')
        self.assertContains(requirement_fragment, self.requirement.code)

        approval_fragment = self.client.get(
            reverse('requirements:requirement_approval_list'), HTTP_HX_REQUEST='true')

        self.assertEqual(200, approval_fragment.status_code)
        self.assertNotContains(approval_fragment, '<html')

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

    def test_requirement_pdf_with_other(self):
        from requirements.models import RequirementDetail

        baker.make(RequirementDetail, requirement=self.requirement, product=None,
                   otro='BIEN NO CATALOGADO', line_number=1, quantity=3, use='USO')

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

    def test_requirement_delete_with_quotations(self):
        baker.make(Quotation, requirement=self.requirement,
                   supplier=baker.make(Supplier))

        response = self.client.post(reverse('requirements:requirement_delete'),
                                    {'code': self.requirement.code},
                                    HTTP_X_REQUESTED_WITH='XMLHttpRequest')

        self.assertEqual(200, response.status_code)
        self.assertEqual('SI', response.json()['quotations'])

    def test_requirement_detail_row(self):
        response = self.client.get(reverse('requirements:requirement_detail_row'),
                                   {'index': '1'})

        self.assertEqual(200, response.status_code)
        self.assertContains(response, 'name="form-1-product"')

    def test_requirement_detail_fetch(self):
        from requirements.models import RequirementDetail

        baker.make(RequirementDetail, requirement=self.requirement,
                   product=baker.make('products.Product'), line_number=1,
                   quantity=5, use='USO')
        baker.make(RequirementDetail, requirement=self.requirement, product=None,
                   line_number=2, quantity=2, use='')

        for search_type in ('TODOS', 'PRODUCTOS'):
            with self.subTest(search_type=search_type):
                response = self.client.get(
                    reverse('requirements:requirement_detail_fetch'),
                    {'requirement': self.requirement.code, 'search_type': search_type},
                    HTTP_X_REQUESTED_WITH='XMLHttpRequest')
                self.assertEqual(200, response.status_code)

    def test_requirement_create_get(self):
        response = self.client.get(reverse('requirements:requirement_create'))

        self.assertEqual(200, response.status_code)

    def test_requirement_create_without_office(self):
        Office.objects.all().delete()

        response = self.client.get(reverse('requirements:requirement_create'))

        self.assertEqual(302, response.status_code)
        self.assertEqual(reverse('administration:office_create'), response.url)

    def test_requirement_create_without_worker(self):
        self.client.force_login(
            User.objects.create_superuser('b', 'b@example.com', 'clave'))

        response = self.client.get(reverse('requirements:requirement_create'))

        self.assertEqual(302, response.status_code)
        self.assertEqual(reverse('administration:worker_create'), response.url)

    def test_requirement_create_without_signature(self):
        self.worker.signature = ''
        self.worker.save()

        response = self.client.get(reverse('requirements:requirement_create'))

        self.assertEqual(302, response.status_code)
        self.assertEqual(reverse('administration:worker_update', args=[self.worker.pk]),
                         response.url)

    def test_requirement_create_without_position(self):
        Position.objects.filter(worker=self.worker).delete()

        response = self.client.get(reverse('requirements:requirement_create'))

        self.assertEqual(302, response.status_code)
        self.assertEqual(reverse('administration:position_create'), response.url)

    def test_requirement_create_without_boss_position(self):
        position = Position.objects.get(worker=self.worker)
        position.is_leadership = False
        position.save()

        response = self.client.get(reverse('requirements:requirement_create'))

        self.assertEqual(302, response.status_code)
        self.assertEqual(reverse('administration:position_create'), response.url)

    def test_requirement_create_without_approval_level(self):
        ApprovalLevel.objects.all().delete()

        response = self.client.get(reverse('requirements:requirement_create'))

        self.assertEqual(302, response.status_code)
        self.assertEqual(reverse('administration:approval_level_create'), response.url)

    def test_requirement_create_without_configuration(self):
        from accounting.models import Configuration

        Configuration.objects.all().delete()
        clear_cache()

        response = self.client.get(reverse('requirements:requirement_create'))

        self.assertEqual(302, response.status_code)
        self.assertEqual(reverse('accounting:configuration'), response.url)

    def test_requirement_update(self):
        from requirements.models import RequirementDetail

        product = baker.make('products.Product')
        baker.make(RequirementDetail, requirement=self.requirement, product=product,
                   line_number=1, quantity=5, use='USO')
        baker.make(RequirementDetail, requirement=self.requirement, product=None,
                   line_number=2, quantity=2, use='')

        response = self.client.get(reverse('requirements:requirement_update',
                                           args=[self.requirement.pk]))
        self.assertEqual(200, response.status_code)

        data = {'code': self.requirement.code, 'reason': 'MOTIVO EDITADO',
                'date': '01/01/2024', 'month': '1', 'year': '2024', 'notes': '',
                'report': '', 'direct_delivery_to_requester': 'on',
                'form-TOTAL_FORMS': '1', 'form-INITIAL_FORMS': '0',
                'form-MIN_NUM_FORMS': '0', 'form-MAX_NUM_FORMS': '1000',
                'form-0-code': product.code, 'form-0-product': product.description,
                'form-0-unit': 'UND01', 'form-0-quantity': '3', 'form-0-use': 'USO'}
        response = self.client.post(reverse('requirements:requirement_update',
                                            args=[self.requirement.pk]), data)

        self.assertEqual(302, response.status_code)
        self.requirement.refresh_from_db()
        self.assertEqual('MOTIVO EDITADO', self.requirement.reason)
        self.assertEqual(1, self.requirement.details.count())

    def test_requirement_create_with_details(self):
        product = baker.make('products.Product')
        Position.objects.filter(worker=self.worker).update(name='ZULU')
        boss = baker.make(Worker, user=baker.make('auth.User', email='jefe@example.com'))
        baker.make(Position, office=self.office, worker=boss, name='ALFA',
                   is_leadership=True, start_date=date(2020, 1, 1), end_date=None)
        data = {'code': '', 'reason': 'MOTIVO DETALLE', 'date': '01/01/2024',
                'month': '1', 'year': '2024', 'notes': '',
                'direct_delivery_to_requester': 'on',
                'form-TOTAL_FORMS': '1', 'form-INITIAL_FORMS': '0',
                'form-MIN_NUM_FORMS': '0', 'form-MAX_NUM_FORMS': '1000',
                'form-0-code': product.code, 'form-0-product': product.description,
                'form-0-unit': 'UND01', 'form-0-quantity': '3', 'form-0-use': 'USO'}

        response = self.client.post(reverse('requirements:requirement_create'), data)

        self.assertEqual(302, response.status_code)
        requirement = Requirement.objects.get(reason='MOTIVO DETALLE')
        self.assertEqual(1, requirement.details.count())

    def test_requirement_create_with_other(self):
        data = {'code': '', 'reason': 'OTRO E2E', 'date': '01/01/2024', 'month': '1',
                'year': '2024', 'notes': '', 'direct_delivery_to_requester': 'on',
                'form-TOTAL_FORMS': '1', 'form-INITIAL_FORMS': '0',
                'form-MIN_NUM_FORMS': '0', 'form-MAX_NUM_FORMS': '1000',
                'form-0-code': '', 'form-0-product': 'BIEN NO CATALOGADO',
                'form-0-unit': '', 'form-0-quantity': '3', 'form-0-use': 'USO'}

        response = self.client.post(reverse('requirements:requirement_create'), data)

        self.assertEqual(302, response.status_code)
        detail = Requirement.objects.get(reason='OTRO E2E').details.get()
        self.assertIsNone(detail.product)
        self.assertEqual('BIEN NO CATALOGADO', detail.otro)

    def test_requirement_update_with_other(self):
        data = {'code': self.requirement.code, 'reason': 'MOTIVO', 'date': '01/01/2024',
                'month': '1', 'year': '2024', 'notes': '', 'report': '',
                'direct_delivery_to_requester': 'on',
                'form-TOTAL_FORMS': '1', 'form-INITIAL_FORMS': '0',
                'form-MIN_NUM_FORMS': '0', 'form-MAX_NUM_FORMS': '1000',
                'form-0-code': '', 'form-0-product': 'BIEN NO CATALOGADO',
                'form-0-unit': '', 'form-0-quantity': '3', 'form-0-use': 'USO'}

        response = self.client.post(
            reverse('requirements:requirement_update', args=[self.requirement.pk]), data)

        self.assertEqual(302, response.status_code)
        detail = self.requirement.details.get()
        self.assertIsNone(detail.product)
        self.assertEqual('BIEN NO CATALOGADO', detail.otro)

    def test_requirement_create_invalid(self):
        response = self.client.post(reverse('requirements:requirement_create'),
                                    {'code': '', 'reason': '', 'date': 'fecha-mala',
                                     'month': '1', 'year': '2024', 'notes': '',
                                     'direct_delivery_to_requester': 'on',
                                     'form-TOTAL_FORMS': '0', 'form-INITIAL_FORMS': '0',
                                     'form-MIN_NUM_FORMS': '0', 'form-MAX_NUM_FORMS': '1000'})

        self.assertEqual(200, response.status_code)

    def test_requirement_update_invalid(self):
        response = self.client.post(reverse('requirements:requirement_update',
                                            args=[self.requirement.pk]),
                                    {'code': self.requirement.code, 'reason': '',
                                     'date': 'fecha-mala', 'month': '1', 'year': '2024',
                                     'notes': '', 'report': '',
                                     'direct_delivery_to_requester': 'on',
                                     'form-TOTAL_FORMS': '0', 'form-INITIAL_FORMS': '0',
                                     'form-MIN_NUM_FORMS': '0', 'form-MAX_NUM_FORMS': '1000'})

        self.assertEqual(200, response.status_code)

    def test_requirement_update_denied_when_approved(self):
        from django.contrib.auth.models import Permission

        self.requirement.approval.is_active = False
        self.requirement.approval.save()
        user = User.objects.create_user('u', 'u@example.com', 'clave')
        user.user_permissions.add(
            Permission.objects.get(codename='change_requirement'))
        self.client.force_login(user)

        response = self.client.get(reverse('requirements:requirement_update',
                                           args=[self.requirement.pk]))

        self.assertEqual(302, response.status_code)
        self.assertEqual(reverse('security:permission_denied'), response.url)

    def test_requirement_approval_list_guards(self):
        self.client.force_login(
            User.objects.create_superuser('c', 'c@example.com', 'clave'))

        response = self.client.get(reverse('requirements:requirement_approval_list'))
        self.assertEqual(reverse('administration:worker_create'), response.url)

        self.client.force_login(self.user)
        self.worker.signature = ''
        self.worker.save()
        response = self.client.get(reverse('requirements:requirement_approval_list'))
        self.assertEqual(reverse('administration:worker_update', args=[self.worker.pk]),
                         response.url)

        self.worker.signature = 'firmas/firma.png'
        self.worker.save()
        Position.objects.filter(worker=self.worker).delete()
        response = self.client.get(reverse('requirements:requirement_approval_list'))
        self.assertEqual(reverse('administration:position_create'), response.url)

        baker.make(Position, office=self.office, worker=self.worker,
                   is_leadership=False, end_date=None)
        response = self.client.get(reverse('requirements:requirement_approval_list'))
        self.assertEqual(reverse('security:permission_denied'), response.url)

