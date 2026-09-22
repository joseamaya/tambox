"""Buscadores AJAX de receptores.

El tipo de movimiento decide si el receptor es un productor (venta) o un
trabajador, y hay que cubrir los dos caminos del `if`.
"""
from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from model_bakery import baker

from administration.models import Producer, Worker
from warehouse.models import MovementType


class ReceiverSearchTest(TestCase):

    def setUp(self):
        self.client.force_login(User.objects.create_superuser('a', 'a@example.com', 'clave'))
        self.sale = baker.make(MovementType, is_sale=True)
        self.purchase = baker.make(MovementType, is_sale=False)

    def search(self, name, params):
        return self.client.get(reverse(name), params,
                               HTTP_X_REQUESTED_WITH='XMLHttpRequest')

    def test_dni_search_producer(self):
        baker.make(Producer, dni='12345678', first_name='JUAN', last_name='PEREZ')

        response = self.search('administration:receiver_dni_search',
                               {'dni': '12345678', 'movement_type': self.sale.pk})

        self.assertEqual(200, response.status_code)
        self.assertIn('PEREZ', response.json()['full_name'])

    def test_dni_search_worker(self):
        baker.make(Worker, dni='87654321', first_name='ANA', last_name='TORRES')

        response = self.search('administration:receiver_dni_search',
                               {'dni': '87654321', 'movement_type': self.purchase.pk})

        self.assertEqual(200, response.status_code)
        self.assertIn('TORRES', response.json()['full_name'])

    def test_name_search_producer(self):
        baker.make(Producer, dni='12345678', first_name='JUAN', last_name='PEREZ')

        response = self.search('administration:receiver_name_search',
                               {'name': 'PEREZ', 'movement_type': self.sale.pk})

        self.assertEqual(200, response.status_code)
        self.assertIn('PEREZ', response.json()[0]['label'])

    def test_name_search_worker(self):
        baker.make(Worker, dni='87654321', first_name='ANA', last_name='TORRES')

        response = self.search('administration:receiver_name_search',
                               {'name': 'ANA', 'movement_type': self.purchase.pk})

        self.assertEqual(200, response.status_code)
        self.assertIn('TORRES', response.json()[0]['label'])
