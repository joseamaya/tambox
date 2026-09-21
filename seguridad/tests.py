from django.contrib import messages
from django.contrib.auth.models import Permission, User
from django.contrib.messages.storage.cookie import CookieStorage
from django.test import RequestFactory, TestCase
from django.urls import NoReverseMatch, get_resolver, reverse
from django.views.generic import TemplateView

from almacen.forms import MovementReportForm
from seguridad.permisos import permisos_declarados


class AutorizacionTestCase(TestCase):

    def setUp(self):
        self.usuario = User.objects.create_superuser('verificador', 'verificador@example.com', 'clave-segura-123')

    def test_contabilidad_exige_login(self):
        self.client.logout()
        for url in ['/contabilidad/cuentas_contables/',
                    '/contabilidad/tipos_cambio/',
                    '/contabilidad/impuestos/',
                    '/contabilidad/tipos_existencias/',
                    '/contabilidad/obtener_tipo_cambio/',
                    '/contabilidad/formas_pago/',
                    '/contabilidad/configuracion/',
                    '/contabilidad/cargar_cuentas_contables/']:
            respuesta = self.client.get(url)
            self.assertEqual(respuesta.status_code, 302, 'sin login no redirige: ' + url)
            self.assertIn('/?next=', respuesta['Location'], url)

    def test_eliminar_por_get_no_permitido(self):
        self.client.force_login(self.usuario)
        for url in ['/almacen/eliminar_almacen/',
                    '/almacen/eliminar_movimiento/',
                    '/almacen/eliminar_pedido/',
                    '/compras/eliminar_proveedor/',
                    '/compras/eliminar_orden_compra/',
                    '/compras/eliminar_cotizacion/',
                    '/compras/eliminar_orden_servicios/',
                    '/compras/eliminar_conformidad_servicio/',
                    '/productos/product_delete/',
                    '/productos/unit_of_measure_delete/',
                    '/productos/service_delete/',
                    '/productos/product_group_delete/',
                    '/contabilidad/eliminar_tipo_documento/',
                    '/contabilidad/eliminar_forma_pago/',
                    '/requerimientos/eliminar_requerimiento/']:
            respuesta = self.client.get(url)
            self.assertEqual(respuesta.status_code, 405, 'GET permitido en: ' + url)

    def test_logout_exige_post(self):
        self.client.force_login(self.usuario)
        self.assertEqual(self.client.get('/salir').status_code, 405)
        self.assertEqual(self.client.post('/salir').status_code, 302)

    def test_admin_login_sigue_publico(self):
        """Django exime AdminSite.login del middleware de login. Si esto falla,
        el admin queda inaccesible."""
        self.client.logout()

        self.assertEqual(self.client.get('/admin/login/').status_code, 200)

    def test_sin_permiso_responde_403(self):
        """La denegacion es un 403 de verdad. Antes era un redirect a una vista
        que respondia 200, asi que ni un monitor ni un test podian distinguirla
        de un acceso correcto."""
        self.client.raise_request_exception = False
        self.client.force_login(
            User.objects.create_user('consulta', 'consulta@example.com', 'clave-consulta-123'))

        respuesta = self.client.get('/contabilidad/impuestos/')

        self.assertEqual(respuesta.status_code, 403)
        self.assertTemplateUsed(respuesta, 'seguridad/permiso_denegado.html')


class RenderTestCase(TestCase):

    def setUp(self):
        self.usuario = User.objects.create_superuser('humo', 'humo@example.com', 'clave-segura-456')

    def test_login_renderiza(self):
        respuesta = self.client.get('/')
        self.assertEqual(respuesta.status_code, 200)
        self.assertContains(respuesta, 'TAMBOX')

    def test_pagina_autenticada_renderiza(self):
        self.client.force_login(self.usuario)
        respuesta = self.client.get('/inicio/')
        self.assertEqual(respuesta.status_code, 200)

    def test_listados_renderizan(self):
        self.client.force_login(self.usuario)
        for url in ['/contabilidad/impuestos/',
                    '/contabilidad/formas_pago/',
                    '/administracion/dashboard/',
                    '/almacen/tablero/']:
            respuesta = self.client.get(url)
            self.assertIn(respuesta.status_code, (200, 302), url)
            if respuesta.status_code == 200:
                self.assertContains(respuesta, 'TAMBOX', status_code=200)


class OpcionesDeFormularioTestCase(TestCase):
    """Las opciones que salen de la base de datos se leen al construir el
    formulario, no al importar el modulo: antes quedaban congeladas y un almacén
    nuevo no aparecia en el desplegable hasta reiniciar el process."""

    def test_las_opciones_se_leen_de_la_base_de_datos(self):
        from almacen.models import Warehouse

        Warehouse.objects.create(code='AL01', description='ALMACEN UNO')
        formulario = MovementReportForm()
        codes = [code for code, _ in formulario.fields['almacenes'].choices]

        self.assertIn('AL01', codes)

    def test_un_almacen_nuevo_aparece_sin_reiniciar(self):
        from almacen.models import Warehouse

        formulario = MovementReportForm()
        self.assertEqual([], list(formulario.fields['almacenes'].choices))

        Warehouse.objects.create(code='AL02', description='ALMACEN DOS')
        formulario = MovementReportForm()
        codes = [code for code, _ in formulario.fields['almacenes'].choices]

        self.assertIn('AL02', codes)


def recorrer_urls(patrones=None, prefijo='', espacio=''):
    """Baja por el arbol de URLs y devuelve (name, callback) de cada vista.

    El nombre sale del namespace y el nombre del patron (`seguridad:login`), y si
    el patron no tiene nombre cae al texto del patron.
    """
    if patrones is None:
        patrones = get_resolver().url_patterns
    for patron in patrones:
        if hasattr(patron, 'url_patterns'):
            yield from recorrer_urls(patron.url_patterns,
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

    def test_lo_publico_es_una_lista_cerrada(self):
        vistas = list(recorrer_urls())
        self.assertTrue(vistas, 'No se recorrio ninguna URL')

        publicas = {name for name, callback in vistas
                    if not getattr(callback, 'login_required', True)}

        self.assertEqual(self.PUBLICAS_ESPERADAS, publicas,
                         'Cambio el conjunto de vistas publicas sin login')


class PermisosDeclaradosTest(TestCase):
    """Los permisos se piden por cadena, asi que uno mal escrito no rompe nada:
    deniega a todo el mundo en silencio. El registro de `seguridad.permisos`
    hace que se puedan comprobar."""

    def test_los_permisos_declarados_existen(self):
        get_resolver().url_patterns  # importa las vistas y llena el registro

        declarados = permisos_declarados()
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
        self.usuario = User.objects.create_superuser('navegante', 'navegante@example.com',
                                                     'clave-segura-123')
        self.client.force_login(self.usuario)

    def test_ninguna_pagina_responde_500(self):
        fallos = {}
        for name, _ in recorrer_urls():
            try:
                url = reverse(name)
            except NoReverseMatch:
                continue    # necesita argumentos: la cubren los tests de su vista
            try:
                respuesta = self.client.get(url, raise_request_exception=False)
                estado = respuesta.status_code
            except Exception as error:
                estado = '%s: %s' % (type(error).__name__, error)
            if not isinstance(estado, int) or estado >= 500:
                fallos[name] = '%s (%s) -> %s' % (name, url, estado)

        self.assertEqual(sorted(fallos), sorted(self.PENDIENTES))


class ErroresDeFormularioTest(TestCase):
    """Los bloques de error de los formularios son dos includes compartidos.

    El test de paginas no ejerce este caso: pide los formularios sin errores, y
    un `{% include %}` dentro de un `{% if %}` falso no se renderiza, asi que un
    include roto solo se veria cuando un formulario falla de verdad.
    """

    def setUp(self):
        self.client.force_login(User.objects.create_superuser('errores', 'errores@example.com',
                                                              'clave-segura-123'))

    def test_el_error_de_un_campo_se_ve(self):
        respuesta = self.client.post(reverse('contabilidad:crear_cuenta_contable'), {})

        self.assertEqual(respuesta.status_code, 200)
        self.assertTrue(respuesta.context['form'].errors)
        self.assertContains(respuesta, 'Error:')
        self.assertContains(respuesta, 'alert-danger')


class MensajesEnPantallaTest(TestCase):
    """`base.html` no pintaba los mensajes: el context processor estaba puesto,
    pero los `messages.error` del proyecto se perdian y el usuario no se
    enteraba de que un guardado habia fallado."""

    def test_el_error_se_ve_como_alerta_de_peligro(self):
        peticion = RequestFactory().get('/')
        setattr(peticion, '_messages', CookieStorage(peticion))
        messages.error(peticion, 'Error guardando la cotizacion.')

        respuesta = TemplateView.as_view(template_name='base.html')(peticion)

        self.assertEqual(respuesta.status_code, 200)
        self.assertContains(respuesta, 'Error guardando la cotizacion.')
        self.assertContains(respuesta, 'alert-danger')
