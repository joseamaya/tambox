"""Login y cambio de contraseña.

`PasswordChangeForm` validaba en metodos `clean_password_actual` /
`clean_password_verificacion`, nombres que no coinciden con los campos, asi que
Django nunca los llamaba: se podia cambiar la contraseña sin saber la actual.
Los tests fijan las tres validaciones.
"""
from django.contrib.auth.models import User
from django.test import RequestFactory, TestCase
from django.urls import reverse

from security.views import permission_denied


class LoginTest(TestCase):

    def setUp(self):
        self.user = User.objects.create_user('navegante', 'n@example.com', 'clave-segura')

    def test_valid_login_redirects_home(self):
        response = self.client.post(reverse('security:login'),
                                    {'username': 'navegante', 'password': 'clave-segura'})

        self.assertRedirects(response, reverse('security:home'))

    def test_invalid_login_shows_the_error(self):
        response = self.client.post(reverse('security:login'),
                                    {'username': 'navegante', 'password': 'incorrecta'})

        self.assertEqual(200, response.status_code)
        self.assertTrue(response.context['form'].errors)

    def test_authenticated_user_goes_home(self):
        self.client.force_login(self.user)

        response = self.client.get(reverse('security:login'))

        self.assertRedirects(response, reverse('security:home'))

    def test_home_renders(self):
        self.client.force_login(self.user)

        response = self.client.get(reverse('security:home'))

        self.assertEqual(200, response.status_code)


class PasswordChangeTest(TestCase):

    def setUp(self):
        self.user = User.objects.create_user('navegante', 'n@example.com', 'clave-vieja')
        self.client.force_login(self.user)
        self.url = reverse('security:password_change')

    def change(self, old, new, confirmation):
        return self.client.post(self.url, {'old_password': old,
                                           'new_password': new,
                                           'password_confirmation': confirmation})

    def test_changes_the_password(self):
        response = self.change('clave-vieja', 'clave-nueva', 'clave-nueva')

        self.assertRedirects(response, reverse('security:login'))
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password('clave-nueva'))

    def test_wrong_current_password(self):
        response = self.change('incorrecta', 'clave-nueva', 'clave-nueva')

        self.assertEqual(200, response.status_code)
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password('clave-vieja'))

    def test_new_password_too_short(self):
        response = self.change('clave-vieja', 'corta', 'corta')

        self.assertEqual(200, response.status_code)
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password('clave-vieja'))

    def test_confirmation_does_not_match(self):
        response = self.change('clave-vieja', 'clave-nueva', 'otra-clave')

        self.assertEqual(200, response.status_code)
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password('clave-vieja'))


class PermissionDeniedTest(TestCase):

    def test_view_renders(self):
        self.client.force_login(User.objects.create_user('consulta', 'c@example.com', 'clave'))

        response = self.client.get(reverse('security:permission_denied'))

        self.assertEqual(200, response.status_code)

    def test_handler_responds_403(self):
        response = permission_denied(RequestFactory().get('/'))

        self.assertEqual(403, response.status_code)
