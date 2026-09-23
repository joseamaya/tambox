"""Endpoints AJAX de requerimientos."""
from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from model_bakery import baker

from administration.models import ApprovalLevel, Office, Position, Worker
from requirements.models import Requirement, RequirementDetail


def create_requirement(**kwargs):
    ApprovalLevel.objects.get_or_create(description='USUARIO')
    office = baker.make(Office)
    worker = baker.make(Worker)
    baker.make(Position, office=office, worker=worker, end_date=None)
    return baker.make(Requirement, requester=worker, office=office, **kwargs)


class RequirementsAjaxTest(TestCase):

    def setUp(self):
        self.client.force_login(User.objects.create_superuser('a', 'a@example.com', 'clave'))

    def get(self, name, params=None):
        return self.client.get(reverse(name), params or {},
                               HTTP_X_REQUESTED_WITH='XMLHttpRequest')

    def test_detail_row(self):
        response = self.get('requirements:requirement_detail_row', {'index': '4'})

        self.assertEqual(200, response.status_code)
        self.assertContains(response, 'name="form-4-product"')

    def test_detail_fetch_all(self):
        requirement = create_requirement(code='REQ0001')
        baker.make(RequirementDetail, requirement=requirement,
                   product=baker.make('products.Product'), use='USO')

        response = self.get('requirements:requirement_detail_fetch',
                            {'requirement': requirement.code, 'search_type': 'TODOS'})

        self.assertEqual(200, response.status_code)
        self.assertEqual(1, len(response.json()))

    def test_detail_fetch_products(self):
        requirement = create_requirement(code='REQ0002')
        baker.make(RequirementDetail, requirement=requirement,
                   product=baker.make('products.Product'), use='USO')

        response = self.get('requirements:requirement_detail_fetch',
                            {'requirement': requirement.code, 'search_type': 'PRODUCTOS'})

        self.assertEqual(200, response.status_code)
        self.assertEqual(1, len(response.json()))
