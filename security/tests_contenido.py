"""Afirman valores renderizados, no solo que la pagina responda.

Django pinta vacio, sin error, cuando una plantilla referencia un campo que ya no
existe: `{{ product.description }}` deja la celda en blanco y `{% if campo %}` se
vuelve falso. El test que recorre todas las URLs solo ve errores duros, asi que sin
estos tests un renombrado puede dejar una columna vacia con la suite en verde.

Cada pagina representativa afirma el valor de al menos un campo.
"""
from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from model_bakery import baker

from administration.models import ApprovalLevel, Office, Position, Worker
from warehouse.models import Movement, MovementType
from purchases.models import PurchaseOrder
from accounting.models import Account
from products.models import Product
from requirements.models import Requirement


class PageContentTest(TestCase):

    def setUp(self):
        self.user = User.objects.create_superuser(
            'contenido', 'contenido@example.com', 'key-segura-123')
        self.client.force_login(self.user)

    def test_lists_products_shows_description(self):
        # El code tiene que ser numerico: la URL de detalle pide (?P<pk>\d+).
        baker.make(Product, code='0000000001', description='PRODUCTO-XYZ')

        response = self.client.get(reverse('products:product_list'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'PRODUCTO-XYZ')

    def test_lists_movements_shows_type(self):
        type = baker.make(MovementType, description='TIPO-XYZ')
        baker.make(Movement, movement_type=type)

        response = self.client.get(reverse('warehouse:movement_list'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'TIPO-XYZ')

    def test_detail_movement_shows_product(self):
        product = baker.make(Product, description='PRODUCTO-XYZ')
        movement = baker.make(Movement)
        baker.make('warehouse.MovementDetail', movement=movement, product=product)

        response = self.client.get(reverse('warehouse:movement_detail_view', args=[movement.pk]))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'PRODUCTO-XYZ')

    def test_lists_orders_purchase_shows_code(self):
        baker.make(PurchaseOrder, code='ORD-XYZ')

        response = self.client.get(reverse('purchases:purchase_order_list'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'ORD-XYZ')

    def test_detail_requirement_shows_product(self):
        """La vista lee `request.user.worker`, asi que el grafo tiene que
        colgar del usuario que navega, no de uno cualquiera."""
        ApprovalLevel.objects.get_or_create(description='USUARIO')
        office = baker.make(Office)
        worker = baker.make(Worker, user=self.user)
        baker.make(Position, office=office, worker=worker, end_date=None)
        requirement = baker.make(Requirement, requester=worker, office=office)
        product = baker.make(Product, description='PRODUCTO-XYZ')
        baker.make('requirements.RequirementDetail',
                   requirement=requirement, product=product)

        response = self.client.get(reverse('requirements:requirement_detail',
                                            args=[requirement.code]))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'PRODUCTO-XYZ')

    def test_lists_accounts_shows_account(self):
        baker.make(Account, account_number='CTA-XYZ')

        response = self.client.get(reverse('accounting:account_list'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'CTA-XYZ')

    def test_lists_offices_shows_name(self):
        baker.make(Office, name='OFICINA-XYZ')

        response = self.client.get(reverse('administration:office_list'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'OFICINA-XYZ')

    def test_form_follows_rendering_fields(self):
        """El widget lleva el nombre del campo del formulario, asi que si el campo
        se renombra y la plantilla no lo sigue, el cuadro desaparece de la pagina."""
        response = self.client.get(reverse('warehouse:movement_type_create'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'name="increases"')

    def test_lists_units_measure_shows_description(self):
        baker.make('products.UnitOfMeasure', code='UND01', description='UNIDAD-XYZ')

        response = self.client.get(reverse('products:unit_of_measure_list'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'UNIDAD-XYZ')

    def test_lists_groups_products_shows_description(self):
        baker.make('products.ProductGroup', code='000001', description='GRUPO-XYZ')

        response = self.client.get(reverse('products:product_group_list'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'GRUPO-XYZ')

    def test_lists_types_stock_type_shows_description(self):
        baker.make('accounting.StockType', sunat_code='01', description='EXISTENCIA-XYZ')

        response = self.client.get(reverse('accounting:stock_type_list'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'EXISTENCIA-XYZ')

    def test_lists_warehouses_shows_description(self):
        baker.make('warehouse.Warehouse', code='AL01', description='ALMACEN-XYZ')

        response = self.client.get(reverse('warehouse:warehouse_list'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'ALMACEN-XYZ')

    def test_lists_types_movement_shows_description(self):
        baker.make('warehouse.MovementType', code='T01', description='MOVIMIENTO-XYZ')

        response = self.client.get(reverse('warehouse:movement_type_list'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'MOVIMIENTO-XYZ')
