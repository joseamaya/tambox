from django.contrib import messages
from django.contrib.auth.models import Permission, User
from django.contrib.messages.storage.cookie import CookieStorage
from django.test import RequestFactory, TestCase
from django.urls import NoReverseMatch, get_resolver, reverse
from django.views.generic import TemplateView

from almacen.forms import MovementReportForm
from seguridad.permisos import declared_permissions


class AuthorizationTestCase(TestCase):

    def setUp(self):
        self.user = User.objects.create_superuser('verificador', 'verificador@example.com', 'key-segura-123')

    def test_accounting_requires_login(self):
        self.client.logout()
        for url in ['/contabilidad/account_list/',
                    '/contabilidad/exchange_rate_list/',
                    '/contabilidad/tax_list/',
                    '/contabilidad/stock_type_list/',
                    '/contabilidad/exchange_rate_fetch/',
                    '/contabilidad/payment_method_list/',
                    '/contabilidad/configuration/',
                    '/contabilidad/account_import/']:
            respuesta = self.client.get(url)
            self.assertEqual(respuesta.status_code, 302, 'sin login no redirige: ' + url)
            self.assertIn('/?next=', respuesta['Location'], url)

    def test_delete_by_get_not_allowed(self):
        self.client.force_login(self.user)
        for url in ['/almacen/warehouse_delete/',
                    '/almacen/movement_delete/',
                    '/almacen/order_delete/',
                    '/compras/supplier_delete/',
                    '/compras/purchase_order_delete/',
                    '/compras/quotation_delete/',
                    '/compras/service_order_delete/',
                    '/compras/service_conformity_delete/',
                    '/productos/product_delete/',
                    '/productos/unit_of_measure_delete/',
                    '/productos/service_delete/',
                    '/productos/product_group_delete/',
                    '/contabilidad/document_type_delete/',
                    '/contabilidad/payment_method_delete/',
                    '/requerimientos/requirement_delete/']:
            respuesta = self.client.get(url)
            self.assertEqual(respuesta.status_code, 405, 'GET permitido en: ' + url)

    def test_logout_requires_post(self):
        self.client.force_login(self.user)
        self.assertEqual(self.client.get('/logout').status_code, 405)
        self.assertEqual(self.client.post('/logout').status_code, 302)

    def test_admin_login_follows_public(self):
        """Django exime AdminSite.login del middleware de login. Si esto falla,
        el admin queda inaccesible."""
        self.client.logout()

        self.assertEqual(self.client.get('/admin/login/').status_code, 200)

    def test_without_permission_responds_403(self):
        """La denegacion es un 403 de verdad. Antes era un redirect a una vista
        que respondia 200, asi que ni un monitor ni un test podian distinguirla
        de un acceso correcto."""
        self.client.raise_request_exception = False
        self.client.force_login(
            User.objects.create_user('consulta', 'consulta@example.com', 'key-consulta-123'))

        respuesta = self.client.get('/contabilidad/tax_list/')

        self.assertEqual(respuesta.status_code, 403)
        self.assertTemplateUsed(respuesta, 'security/permission_denied.html')


class RenderTestCase(TestCase):

    def setUp(self):
        self.user = User.objects.create_superuser('humo', 'humo@example.com', 'key-segura-456')

    def test_login_renders(self):
        respuesta = self.client.get('/')
        self.assertEqual(respuesta.status_code, 200)
        self.assertContains(respuesta, 'TAMBOX')

    def test_page_authenticated_renders(self):
        self.client.force_login(self.user)
        respuesta = self.client.get('/home/')
        self.assertEqual(respuesta.status_code, 200)

    def test_lists_render(self):
        self.client.force_login(self.user)
        for url in ['/contabilidad/tax_list/',
                    '/contabilidad/payment_method_list/',
                    '/administracion/dashboard/',
                    '/almacen/dashboard/']:
            respuesta = self.client.get(url)
            self.assertIn(respuesta.status_code, (200, 302), url)
            if respuesta.status_code == 200:
                self.assertContains(respuesta, 'TAMBOX', status_code=200)


class FormOptionsTestCase(TestCase):
    """Las opciones que salen de la base de datos se leen al construir el
    formulario, no al importar el modulo: antes quedaban congeladas y un almacén
    nuevo no aparecia en el desplegable hasta reiniciar el process."""

    def test_options_read_base_data(self):
        from almacen.models import Warehouse

        Warehouse.objects.create(code='AL01', description='ALMACEN UNO')
        formulario = MovementReportForm()
        codes = [code for code, _ in formulario.fields['warehouses'].choices]

        self.assertIn('AL01', codes)

    def test_warehouse_new_appears_without_restart(self):
        from almacen.models import Warehouse

        formulario = MovementReportForm()
        self.assertEqual([], list(formulario.fields['warehouses'].choices))

        Warehouse.objects.create(code='AL02', description='ALMACEN DOS')
        formulario = MovementReportForm()
        codes = [code for code, _ in formulario.fields['warehouses'].choices]

        self.assertIn('AL02', codes)


def walk_urls(patrones=None, prefijo='', espacio=''):
    """Baja por el arbol de URLs y devuelve (name, callback) de cada vista.

    El nombre sale del namespace y el nombre del patron (`seguridad:login`), y si
    el patron no tiene nombre cae al texto del patron.
    """
    if patrones is None:
        patrones = get_resolver().url_patterns
    for patron in patrones:
        if hasattr(patron, 'url_patterns'):
            yield from walk_urls(patron.url_patterns,
                                     prefijo + str(patron.pattern),
                                     patron.namespace or espacio)
        else:
            if espacio and patron.name:
                name = '%s:%s' % (espacio, patron.name)
            else:
                name = prefijo + str(patron.pattern)
            yield name, patron.callback


class URLsProtegidasTest(TestCase):
    """El middleware de login invierte el defecto: una vista nueva nace protegida
    aunque nadie se acuerde de envolverla (que es como se colo el hueco de
    contabilidad, donde el `urlpatterns += [...]` final quedo fuera).

    La prueba lee el mismo atributo que lee el middleware, asi que lo publico
    tiene que ser una lista cerrada y justificada.
    """

    PUBLICAS_ESPERADAS = {
        'seguridad:login',   # el propio login, o el middleware crea un bucle
        'admin:login',       # Django lo exime en AdminSite.login
    }

    def test_public_is_lists_cerrada(self):
        vistas = list(walk_urls())
        self.assertTrue(vistas, 'No se recorrio ninguna URL')

        publicas = {name for name, callback in vistas
                    if not getattr(callback, 'login_required', True)}

        self.assertEqual(self.PUBLICAS_ESPERADAS, publicas,
                         'Cambio el conjunto de vistas publicas sin login')


class DeclaredPermissionsTest(TestCase):
    """Los permisos se piden por cadena, asi que uno mal escrito no rompe nada:
    deniega a todo el mundo en silencio. El registro de `seguridad.permisos`
    hace que se puedan comprobar."""

    def test_permissions_declared_exist(self):
        get_resolver().url_patterns  # importa las vistas y llena el registro

        declarados = declared_permissions()
        self.assertTrue(declarados, 'El registro esta vacio: no se importaron las vistas')

        existentes = {'%s.%s' % (app, codename)
                      for app, codename in Permission.objects.values_list(
                          'content_type__app_label', 'codename')}

        for permiso in declarados:
            with self.subTest(permiso=permiso):
                self.assertIn(permiso, existentes)


class TodasLasPaginasTest(TestCase):
    """Pide con sesion todas las URLs invertibles y exige que ninguna devuelva
    500.

    Es la red que hace seguro tocar plantillas: sin esto, un `{% include %}` mal
    armado al deduplicar plantillas solo se descubriria al abrir la pagina.

    `PENDIENTES` es la deuda conocida y la lista tiene que ser exacta: la prueba
    compara el conjunto de fallos con estas claves, asi que arreglar una pagina
    obliga a sacarla de aqui, y romper una nueva falla de inmediato.
    """

    # Vacio: no queda ninguna pagina que responda 500. La prueba compara el
    # conjunto de fallos con estas claves, asi que si una pagina nueva empieza a
    # fallar aparece aqui de inmediato, y si se arregla hay que sacarla.
    PENDIENTES = {
    }

    def setUp(self):
        self.user = User.objects.create_superuser('navegante', 'navegante@example.com',
                                                     'key-segura-123')
        self.client.force_login(self.user)

    def test_none_page_responds_500(self):
        fallos = {}
        for name, _ in walk_urls():
            try:
                url = reverse(name)
            except NoReverseMatch:
                continue    # necesita argumentos: la cubren los tests de su vista
            try:
                respuesta = self.client.get(url, raise_request_exception=False)
                status = respuesta.status_code
            except Exception as error:
                status = '%s: %s' % (type(error).__name__, error)
            if not isinstance(status, int) or status >= 500:
                fallos[name] = '%s (%s) -> %s' % (name, url, status)

        self.assertEqual(sorted(fallos), sorted(self.PENDIENTES))


class FormErrorsTest(TestCase):
    """Los bloques de error de los formularios son dos includes compartidos.

    El test de paginas no ejerce este caso: pide los formularios sin errores, y
    un `{% include %}` dentro de un `{% if %}` falso no se renderiza, asi que un
    include roto solo se veria cuando un formulario falla de verdad.
    """

    def setUp(self):
        self.client.force_login(User.objects.create_superuser('errores', 'errores@example.com',
                                                              'key-segura-123'))

    def test_error_field_sees(self):
        respuesta = self.client.post(reverse('contabilidad:account_create'), {})

        self.assertEqual(respuesta.status_code, 200)
        self.assertTrue(respuesta.context['form'].errors)
        self.assertContains(respuesta, 'Error:')
        self.assertContains(respuesta, 'alert-danger')


class OnScreenMessagesTest(TestCase):
    """`base.html` no pintaba los mensajes: el context processor estaba puesto,
    pero los `messages.error` del proyecto se perdian y el usuario no se
    enteraba de que un guardado habia fallado."""

    def test_error_sees_as_alert_danger(self):
        peticion = RequestFactory().get('/')
        setattr(peticion, '_messages', CookieStorage(peticion))
        messages.error(peticion, 'Error guardando la cotizacion.')

        respuesta = TemplateView.as_view(template_name='base.html')(peticion)

        self.assertEqual(respuesta.status_code, 200)
        self.assertContains(respuesta, 'Error guardando la cotizacion.')
        self.assertContains(respuesta, 'alert-danger')
