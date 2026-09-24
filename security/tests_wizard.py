"""Wizard de configuracion inicial y bloqueo de la aplicacion.

El bloqueo se prueba activando `SETUP_WIZARD_ENFORCED` con `override_settings`;
la suite normal lo lleva desactivado (ver `tambox.settings.development`).
"""
from django.contrib.auth.models import User
from django.test import TestCase, override_settings
from django.urls import reverse
from model_bakery import baker

from tambox.setup import clear_setup_cache, seed_base_data


def complete_system():
    """Deja el sistema configurado por completo (todos los pasos requeridos)."""
    seed_base_data()
    baker.make('accounting.StockType')
    baker.make('accounting.Configuration')
    baker.make('accounting.Company', business_name='TAMBOX', tax_id='12345678901')
    baker.make('administration.Worker')
    baker.make('administration.Position')
    baker.make('warehouse.Warehouse')
    baker.make('products.Product')


@override_settings(SETUP_WIZARD_ENFORCED=True)
class SetupWizardMiddlewareTest(TestCase):

    def setUp(self):
        clear_setup_cache()
        self.user = User.objects.create_superuser('wizard', 'wizard@example.com', 'key-segura-123')
        self.client.force_login(self.user)

    def tearDown(self):
        clear_setup_cache()

    def test_blocks_app_when_incomplete(self):
        response = self.client.get('/contabilidad/tax_list/')

        self.assertRedirects(response, reverse('security:setup'),
                             fetch_redirect_response=False)

    def test_allows_wizard(self):
        response = self.client.get(reverse('security:setup'))

        self.assertEqual(302, response.status_code)
        self.assertTrue(response['Location'].startswith('/configuracion/'))

    def test_allows_login(self):
        self.client.logout()

        response = self.client.get(reverse('security:login'))

        self.assertEqual(200, response.status_code)

    def test_allows_admin(self):
        response = self.client.get('/admin/')

        self.assertNotIn('/configuracion/', response.get('Location', ''))

    def test_does_not_block_when_configured(self):
        complete_system()
        clear_setup_cache()

        response = self.client.get('/contabilidad/tax_list/')

        self.assertEqual(200, response.status_code)

    def test_non_privileged_sees_blocked_page(self):
        self.client.force_login(
            User.objects.create_user('basico', 'basico@example.com', 'key-segura-123'))

        response = self.client.get(reverse('security:setup'))

        self.assertEqual(200, response.status_code)
        self.assertContains(response, 'no está configurado')


class WizardStepTest(TestCase):

    def setUp(self):
        clear_setup_cache()
        self.user = User.objects.create_superuser('wizard', 'wizard@example.com', 'key-segura-123')
        self.client.force_login(self.user)

    def tearDown(self):
        clear_setup_cache()

    def test_entry_seeds_base_and_redirects_to_first_step(self):
        from administration.models import Office

        response = self.client.get(reverse('security:setup'))

        self.assertEqual(302, response.status_code)
        self.assertTrue(response['Location'].endswith('/configuracion/catalog/'))
        self.assertTrue(Office.objects.filter(code='GGEN').exists())

    def test_catalog_step_creates_account_and_group(self):
        from accounting.models import Account
        from products.models import ProductGroup

        self.client.get(reverse('security:setup'))

        response = self.client.post(reverse('security:wizard_step', args=['catalog']), {
            'account-account_number': '70111',
            'account-description': 'MERCADERIAS',
            'account-depreciation': '0',
            'group-description': 'GENERAL',
            'group-contains_products': 'on',
        })

        self.assertEqual(302, response.status_code)
        account = Account.objects.get(account_number='70111')
        group = ProductGroup.objects.get(description='GENERAL')
        self.assertEqual(account, group.account)

    def test_stock_step_creates_stock_type(self):
        from accounting.models import StockType

        response = self.client.post(reverse('security:wizard_step', args=['stock']), {
            'stock-sunat_code': '01',
            'stock-description': 'MERCADERIA',
        })

        self.assertEqual(302, response.status_code)
        self.assertTrue(StockType.objects.filter(sunat_code='01').exists())

    def test_invalid_step_shows_errors(self):
        response = self.client.post(reverse('security:wizard_step', args=['stock']), {
            'stock-sunat_code': '',
            'stock-description': '',
        })

        self.assertEqual(200, response.status_code)
        self.assertTrue(response.context['forms'][0]['form'].errors)

    def test_done_step_shows_already_configured(self):
        from accounting.models import StockType

        StockType.objects.create(sunat_code='01', description='MERCADERIA')

        response = self.client.get(reverse('security:wizard_step', args=['stock']))

        self.assertEqual(200, response.status_code)
        self.assertTrue(response.context['already_done'])

    def test_completing_system_unblocks(self):
        complete_system()
        clear_setup_cache()

        response = self.client.get(reverse('security:setup'))

        self.assertRedirects(response, reverse('security:home'))
