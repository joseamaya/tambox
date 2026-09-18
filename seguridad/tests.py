from django.contrib.auth.models import User
from django.test import TestCase

from almacen.forms import FormularioReporteMovimientos


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
                    '/productos/eliminar_producto/',
                    '/productos/eliminar_unidad_medida/',
                    '/productos/eliminar_servicio/',
                    '/productos/eliminar_grupo_productos/',
                    '/contabilidad/eliminar_tipo_documento/',
                    '/contabilidad/eliminar_forma_pago/',
                    '/requerimientos/eliminar_requerimiento/']:
            respuesta = self.client.get(url)
            self.assertEqual(respuesta.status_code, 405, 'GET permitido en: ' + url)

    def test_logout_exige_post(self):
        self.client.force_login(self.usuario)
        self.assertEqual(self.client.get('/salir').status_code, 405)
        self.assertEqual(self.client.post('/salir').status_code, 302)


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
                    '/administracion/tablero/',
                    '/almacen/tablero/']:
            respuesta = self.client.get(url)
            self.assertIn(respuesta.status_code, (200, 302), url)
            if respuesta.status_code == 200:
                self.assertContains(respuesta, 'TAMBOX', status_code=200)


class OpcionesDeFormularioTestCase(TestCase):
    """Las opciones que salen de la base de datos se leen al construir el
    formulario, no al importar el modulo: antes quedaban congeladas y un almacen
    nuevo no aparecia en el desplegable hasta reiniciar el proceso."""

    def test_las_opciones_se_leen_de_la_base_de_datos(self):
        from almacen.models import Almacen

        Almacen.objects.create(codigo='AL01', descripcion='ALMACEN UNO')
        formulario = FormularioReporteMovimientos()
        codigos = [codigo for codigo, _ in formulario.fields['almacenes'].choices]

        self.assertIn('AL01', codigos)

    def test_un_almacen_nuevo_aparece_sin_reiniciar(self):
        from almacen.models import Almacen

        formulario = FormularioReporteMovimientos()
        self.assertEqual([], list(formulario.fields['almacenes'].choices))

        Almacen.objects.create(codigo='AL02', descripcion='ALMACEN DOS')
        formulario = FormularioReporteMovimientos()
        codigos = [codigo for codigo, _ in formulario.fields['almacenes'].choices]

        self.assertIn('AL02', codigos)
