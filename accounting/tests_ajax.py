"""Endpoint AJAX del tipo de cambio.

El view devolvia el modelo directo a `simplejson.dumps`, que no serializa
instances de Django, asi que con un tipo de cambio cargado respondia 500.
"""
import datetime

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from model_bakery import baker

from accounting.models import ExchangeRate


class ExchangeRateFetchTest(TestCase):

    def setUp(self):
        self.client.force_login(User.objects.create_superuser('a', 'a@example.com', 'clave'))

    def fetch(self, date):
        return self.client.get(reverse('accounting:exchange_rate_fetch'), {'date': date},
                               HTTP_X_REQUESTED_WITH='XMLHttpRequest')

    def test_returns_the_amount(self):
        baker.make(ExchangeRate, date=datetime.date(2024, 1, 15), amount=3.5)

        response = self.fetch('15/01/2024')

        self.assertEqual(200, response.status_code)
        self.assertEqual(3.5, response.json()['amount'])

    def test_without_rate_returns_zero(self):
        response = self.fetch('16/01/2024')

        self.assertEqual(200, response.status_code)
        self.assertEqual(0, response.json()['amount'])
