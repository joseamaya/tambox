"""CRUD de administracion.

`Worker.signature` es obligatorio, asi que el alta del trabajador sube una
imagen minima: el formulario no valida sin ella.
"""
import io
import tempfile

from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.urls import reverse
from model_bakery import baker
from PIL import Image

from administration.models import ApprovalLevel, Office, Position, Producer, Profession, Worker


def png():
    buffer = io.BytesIO()
    Image.new('RGB', (2, 2)).save(buffer, format='PNG')
    return SimpleUploadedFile('firma.png', buffer.getvalue(), content_type='image/png')


class AdministrationViewsTest(TestCase):

    def setUp(self):
        self.client.force_login(User.objects.create_superuser('a', 'a@example.com', 'clave'))

    def test_office_crud(self):
        response = self.client.post(reverse('administration:office_create'),
                                    {'code': 'OF01', 'name': 'OFICINA UNO',
                                     'is_management': 'on'})
        self.assertEqual(302, response.status_code)
        office = Office.objects.get(code='OF01')

        self.assertEqual(200, self.client.get(
            reverse('administration:office_detail', args=[office.pk])).status_code)
        response = self.client.post(reverse('administration:office_update', args=[office.pk]),
                                    {'code': 'OF01', 'name': 'OFICINA EDITADA',
                                     'is_management': 'on'})
        self.assertEqual(302, response.status_code)
        office.refresh_from_db()
        self.assertEqual('OFICINA EDITADA', office.name)

    def test_profession_crud(self):
        response = self.client.post(reverse('administration:profession_create'),
                                    {'abbreviation': 'ING', 'description': 'INGENIERO'})
        self.assertEqual(302, response.status_code)
        profession = Profession.objects.get(abbreviation='ING')

        self.assertEqual(200, self.client.get(
            reverse('administration:profession_detail', args=[profession.pk])).status_code)
        response = self.client.post(reverse('administration:profession_update',
                                            args=[profession.pk]),
                                    {'abbreviation': 'ING', 'description': 'INGENIERO EDITADO'})
        self.assertEqual(302, response.status_code)

    def test_worker_crud(self):
        user = User.objects.create_user('trabajador', 't@example.com', 'clave')

        with tempfile.TemporaryDirectory() as media, self.settings(MEDIA_ROOT=media):
            response = self.client.post(reverse('administration:worker_create'),
                                        {'dni': '12345678', 'last_name': 'PEREZ',
                                         'first_name': 'JUAN', 'user': user.pk,
                                         'signature': png()})
        self.assertEqual(302, response.status_code)
        worker = Worker.objects.get(dni='12345678')

        self.assertEqual(200, self.client.get(
            reverse('administration:worker_detail', args=[worker.pk])).status_code)
        response = self.client.post(reverse('administration:worker_update', args=[worker.pk]),
                                    {'dni': '12345678', 'last_name': 'PEREZ EDITADO',
                                     'first_name': 'JUAN', 'user': user.pk})
        self.assertEqual(302, response.status_code)

    def test_producer_crud(self):
        response = self.client.post(reverse('administration:producer_create'),
                                    {'dni': '87654321', 'last_name': 'TORRES',
                                     'first_name': 'ANA'})
        self.assertEqual(302, response.status_code)
        producer = Producer.objects.get(dni='87654321')

        self.assertEqual(200, self.client.get(
            reverse('administration:producer_detail', args=[producer.pk])).status_code)
        response = self.client.post(reverse('administration:producer_update',
                                            args=[producer.pk]),
                                    {'dni': '87654321', 'last_name': 'TORRES EDITADA',
                                     'first_name': 'ANA'})
        self.assertEqual(302, response.status_code)

    def test_position_crud(self):
        office = baker.make(Office)
        worker = baker.make(Worker)

        response = self.client.post(reverse('administration:position_create'),
                                    {'name': 'PUESTO UNO', 'office': office.pk,
                                     'worker': worker.pk, 'start_date': '01/01/2024'})
        self.assertEqual(302, response.status_code)
        position = Position.objects.get(name='PUESTO UNO')

        self.assertEqual(200, self.client.get(
            reverse('administration:position_detail', args=[position.pk])).status_code)
        response = self.client.post(reverse('administration:position_update',
                                            args=[position.pk]),
                                    {'name': 'PUESTO EDITADO', 'office': office.pk,
                                     'worker': worker.pk, 'start_date': '01/01/2024'})
        self.assertEqual(302, response.status_code)

    def test_approval_level_crud(self):
        response = self.client.post(reverse('administration:approval_level_create'),
                                    {'description': 'NIVEL UNO'})
        self.assertEqual(302, response.status_code)
        level = ApprovalLevel.objects.get(description='NIVEL UNO')

        self.assertEqual(200, self.client.get(
            reverse('administration:approval_level_detail', args=[level.pk])).status_code)
        response = self.client.post(reverse('administration:approval_level_update',
                                            args=[level.pk]),
                                    {'description': 'NIVEL EDITADO'})
        self.assertEqual(302, response.status_code)

    def test_lists_return_htmx_fragment_and_search(self):
        office = baker.make(Office, code='OF01', name='OFICINA UNICA')
        worker = baker.make(Worker, dni='12345678', last_name='TRABAJADOR UNICO')
        baker.make(Producer, dni='87654321', last_name='PRODUCTOR UNICO')
        baker.make(Position, office=office, worker=worker, name='PUESTO UNICO',
                   end_date=None)
        baker.make(Profession, abbreviation='ING', description='PROFESION UNICA')
        baker.make(ApprovalLevel, description='NIVEL UNICO')
        cases = [
            ('administration:office_list', 'OFICINA UNICA'),
            ('administration:worker_list', 'TRABAJADOR UNICO'),
            ('administration:producer_list', 'PRODUCTOR UNICO'),
            ('administration:position_list', 'PUESTO UNICO'),
            ('administration:profession_list', 'PROFESION UNICA'),
            ('administration:approval_level_list', 'NIVEL UNICO'),
        ]

        for name, term in cases:
            with self.subTest(name=name):
                fragment = self.client.get(reverse(name), {'q': term},
                                           HTTP_HX_REQUEST='true')
                self.assertEqual(200, fragment.status_code)
                self.assertNotContains(fragment, '<html')
                self.assertContains(fragment, term)

    def test_dashboard_and_reports(self):
        self.assertEqual(200, self.client.get(reverse('administration:dashboard')).status_code)

        for name in ('administration:office_excel_report',
                     'administration:worker_excel_report',
                     'administration:position_excel_report',
                     'administration:profession_excel_report'):
            with self.subTest(name=name):
                self.assertEqual(200, self.client.get(reverse(name)).status_code)
