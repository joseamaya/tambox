"""Afirman valores renderizados, no solo que la pagina responda.

Django pinta vacio, sin error, cuando una plantilla referencia un campo que ya no
existe: `{{ producto.description }}` deja la celda en blanco y `{% if campo %}` se
vuelve falso. El test que recorre todas las URLs solo ve errores duros, asi que sin
estos tests un renombrado puede dejar una columna vacia con la suite en verde.

Cada pagina representativa afirma el valor de al menos un campo.
"""
from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from model_bakery import baker

from administracion.models import NivelAprobacion, Oficina, Puesto, Trabajador
from almacen.models import Movimiento, TipoMovimiento
from compras.models import OrdenCompra
from contabilidad.models import CuentaContable
from productos.models import Producto
from requerimientos.models import Requerimiento


class ContenidoDeLasPaginasTest(TestCase):

    def setUp(self):
        self.usuario = User.objects.create_superuser(
            'contenido', 'contenido@example.com', 'clave-segura-123')
        self.client.force_login(self.usuario)

    def test_la_lista_de_productos_muestra_la_description(self):
        # El code tiene que ser numerico: la URL de detalle pide (?P<pk>\d+).
        baker.make(Producto, code='0000000001', description='PRODUCTO-XYZ')

        respuesta = self.client.get(reverse('productos:productos'))

        self.assertEqual(respuesta.status_code, 200)
        self.assertContains(respuesta, 'PRODUCTO-XYZ')

    def test_la_lista_de_movimientos_muestra_el_tipo(self):
        tipo = baker.make(TipoMovimiento, description='TIPO-XYZ')
        baker.make(Movimiento, tipo_movimiento=tipo)

        respuesta = self.client.get(reverse('almacen:movimientos'))

        self.assertEqual(respuesta.status_code, 200)
        self.assertContains(respuesta, 'TIPO-XYZ')

    def test_el_detalle_de_movimiento_muestra_el_producto(self):
        producto = baker.make(Producto, description='PRODUCTO-XYZ')
        movimiento = baker.make(Movimiento)
        baker.make('almacen.DetalleMovimiento', movimiento=movimiento, producto=producto)

        respuesta = self.client.get(reverse('almacen:detalle_movimiento', args=[movimiento.pk]))

        self.assertEqual(respuesta.status_code, 200)
        self.assertContains(respuesta, 'PRODUCTO-XYZ')

    def test_la_lista_de_ordenes_de_compra_muestra_el_code(self):
        baker.make(OrdenCompra, code='ORD-XYZ')

        respuesta = self.client.get(reverse('compras:ordenes_compra'))

        self.assertEqual(respuesta.status_code, 200)
        self.assertContains(respuesta, 'ORD-XYZ')

    def test_el_detalle_de_requerimiento_muestra_el_producto(self):
        """La vista lee `request.user.worker`, asi que el grafo tiene que
        colgar del usuario que navega, no de uno cualquiera."""
        NivelAprobacion.objects.get_or_create(description='USUARIO')
        oficina = baker.make(Oficina)
        trabajador = baker.make(Trabajador, usuario=self.usuario)
        baker.make(Puesto, oficina=oficina, trabajador=trabajador, end_date=None)
        requerimiento = baker.make(Requerimiento, solicitante=trabajador, oficina=oficina)
        producto = baker.make(Producto, description='PRODUCTO-XYZ')
        baker.make('requerimientos.DetalleRequerimiento',
                   requerimiento=requerimiento, producto=producto)

        respuesta = self.client.get(reverse('requerimientos:detalle_requerimiento',
                                            args=[requerimiento.code]))

        self.assertEqual(respuesta.status_code, 200)
        self.assertContains(respuesta, 'PRODUCTO-XYZ')

    def test_la_lista_de_cuentas_contables_muestra_la_cuenta(self):
        baker.make(CuentaContable, cuenta='CTA-XYZ')

        respuesta = self.client.get(reverse('contabilidad:cuentas_contables'))

        self.assertEqual(respuesta.status_code, 200)
        self.assertContains(respuesta, 'CTA-XYZ')

    def test_la_lista_de_oficinas_muestra_el_name(self):
        baker.make(Oficina, name='OFICINA-XYZ')

        respuesta = self.client.get(reverse('administracion:maestro_oficinas'))

        self.assertEqual(respuesta.status_code, 200)
        self.assertContains(respuesta, 'OFICINA-XYZ')

    def test_un_formulario_sigue_pintando_sus_campos(self):
        """El widget lleva el nombre del campo del formulario, asi que si el campo
        se renombra y la plantilla no lo sigue, el cuadro desaparece de la pagina."""
        respuesta = self.client.get(reverse('almacen:crear_tipo_movimiento'))

        self.assertEqual(respuesta.status_code, 200)
        self.assertContains(respuesta, 'name="incrementa"')

    def test_la_lista_de_unidades_de_medida_muestra_la_description(self):
        baker.make('productos.UnidadMedida', code='UND01', description='UNIDAD-XYZ')

        respuesta = self.client.get(reverse('productos:unidades_medida'))

        self.assertEqual(respuesta.status_code, 200)
        self.assertContains(respuesta, 'UNIDAD-XYZ')

    def test_la_lista_de_grupos_de_productos_muestra_la_description(self):
        baker.make('productos.GrupoProductos', code='000001', description='GRUPO-XYZ')

        respuesta = self.client.get(reverse('productos:grupos_productos'))

        self.assertEqual(respuesta.status_code, 200)
        self.assertContains(respuesta, 'GRUPO-XYZ')

    def test_la_lista_de_tipos_de_existencia_muestra_la_description(self):
        baker.make('contabilidad.TipoExistencia', codigo_sunat='01', description='EXISTENCIA-XYZ')

        respuesta = self.client.get(reverse('contabilidad:tipos_existencias'))

        self.assertEqual(respuesta.status_code, 200)
        self.assertContains(respuesta, 'EXISTENCIA-XYZ')

    def test_la_lista_de_almacenes_muestra_la_description(self):
        baker.make('almacen.Almacen', code='AL01', description='ALMACEN-XYZ')

        respuesta = self.client.get(reverse('almacen:almacenes'))

        self.assertEqual(respuesta.status_code, 200)
        self.assertContains(respuesta, 'ALMACEN-XYZ')

    def test_la_lista_de_tipos_de_movimiento_muestra_la_description(self):
        baker.make('almacen.TipoMovimiento', code='T01', description='MOVIMIENTO-XYZ')

        respuesta = self.client.get(reverse('almacen:tipos_movimientos'))

        self.assertEqual(respuesta.status_code, 200)
        self.assertContains(respuesta, 'MOVIMIENTO-XYZ')
