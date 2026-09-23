"""Importadores CSV de administracion.

Cada uno arma un grafo distinto: la oficina necesita su dependencia, el puesto
necesita oficina y trabajador, y el trabajador puede crear su usuario.
"""
import tempfile

from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.urls import reverse
from model_bakery import baker

from administration.models import Office, Position, Producer, Worker


class AdministrationImportTest(TestCase):

    def setUp(self):
        self.client.force_login(User.objects.create_superuser(
            'cargador', 'c@example.com', 'key-segura'))

    def upload(self, name, filename, content):
        file = SimpleUploadedFile(filename, content.encode('utf8'), content_type='text/csv')
        with tempfile.TemporaryDirectory() as media, self.settings(MEDIA_ROOT=media):
            return self.client.post(reverse(name), {'file': file})

    def test_import_offices(self):
        baker.make(Office, code='OF00', name='GERENCIA')

        response = self.upload('administration:office_import', 'offices.csv',
                               'OF01,OFICINA UNO,OF00\n')

        self.assertEqual(302, response.status_code)
        office = Office.objects.get(code='OF01')
        self.assertEqual('OFICINA UNO', office.name)
        self.assertEqual('OF00', office.dependency.code)

    def test_import_producers(self):
        response = self.upload('administration:producer_import', 'producers.csv',
                               '12345678,LOPEZ,GARCIA,JUAN\n')

        self.assertEqual(302, response.status_code)
        producer = Producer.objects.get(dni='12345678')
        self.assertEqual('LOPEZ GARCIA', producer.last_name)
        self.assertEqual('JUAN', producer.first_name)

    def test_import_workers_creates_the_user(self):
        response = self.upload('administration:worker_import', 'workers.csv',
                               'jperez,12345678,LOPEZ,GARCIA,JUAN,j@example.com\n')

        self.assertEqual(302, response.status_code)
        worker = Worker.objects.get(dni='12345678')
        self.assertEqual('jperez', worker.user.username)
        self.assertFalse(worker.user.has_usable_password())

    def test_import_positions(self):
        office = baker.make(Office, code='OF01')
        worker = baker.make(Worker, dni='12345678')

        response = self.upload('administration:position_import', 'positions.csv',
                               'PUESTO UNO,OF01,12345678,01/01/2024,SI\n')

        self.assertEqual(302, response.status_code)
        position = Position.objects.get(name='PUESTO UNO')
        self.assertEqual(office, position.office)
        self.assertEqual(worker, position.worker)
        self.assertTrue(position.is_leadership)
