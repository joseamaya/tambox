# -*- coding: utf-8 -*- 
from django.db import models
from model_utils.models import TimeStampedModel
from contabilidad.models import CuentaContable, TipoExistencia
from django.db.models import Max
from django.utils.encoding import force_str
from tambox.querysets import NavegableQuerySet
from simple_history.models import HistoricalRecords
from django.db.models import Q
import datetime
from django.db.models import Sum


class UnidadMedida(TimeStampedModel):
    codigo = models.CharField(max_length=5, unique=True)
    codigo_sunat = models.CharField(max_length=2)
    descripcion = models.CharField(max_length=50)
    estado = models.BooleanField(default=True)
    objects = NavegableQuerySet.as_manager()
    history = HistoricalRecords()

    class Meta:
        permissions = (('ver_detalle_unidad_medida', 'Puede ver detalle Unidad de Medida'),
                       ('ver_tabla_unidades_medida', 'Puede ver tabla de unidades de medida'),
                       ('ver_reporte_unidades_medida_excel', 'Puede ver Reporte Unidades de Medida en excel'),)
        ordering = ['codigo']

    def anterior(self):
        ant = UnidadMedida.objects.anterior(self)
        return ant.pk

    def siguiente(self):
        sig = UnidadMedida.objects.siguiente(self)
        return sig.pk

    def __str__(self):
        return self.descripcion


class GrupoProductos(TimeStampedModel):
    codigo = models.CharField(primary_key=True, max_length=6)
    descripcion = models.CharField(max_length=100)
    ctacontable = models.ForeignKey(CuentaContable, on_delete=models.CASCADE)
    son_productos = models.BooleanField(default=True)
    estado = models.BooleanField(default=True)
    objects = NavegableQuerySet.as_manager()
    history = HistoricalRecords()

    class Meta:
        permissions = (('cargar_grupo_productos', 'Puede cargar Grupos de Productos desde un archivo externo'),
                       ('ver_detalle_grupo_productos', 'Puede ver detalle Grupo de Productos'),
                       ('ver_tabla_grupos_productos', 'Puede ver tabla Grupos de Productos'),
                       ('ver_reporte_grupo_productos_excel', 'Puede ver Reporte de grupo de productos en excel'),)

    def save(self, *args, **kwargs):
        if self.codigo == '':
            grupo_ant = GrupoProductos.objects.all().aggregate(Max('codigo'))
            cod_ant = grupo_ant['codigo__max']
            if cod_ant is None:
                aux = 1
            else:
                aux = int(cod_ant) + 1
            self.codigo = str(aux).zfill(6)
        super(GrupoProductos, self).save()

    def anterior(self):
        ant = GrupoProductos.objects.anterior(self)
        return ant.pk

    def siguiente(self):
        sig = GrupoProductos.objects.siguiente(self)
        return sig.pk

    def __str__(self):
        return self.descripcion

    def obtener_kardex(self, almacen, desde, hasta):
        from almacen.models import Kardex
        hasta = hasta + datetime.timedelta(days=1)
        listado_kardex = Kardex.objects.filter(almacen=almacen,
                                               fecha_operacion__gte=desde,
                                               fecha_operacion__lte=hasta,
                                               producto__grupo_productos=self).select_related(
            'movimiento__tipo_documento', 'movimiento__tipo_movimiento').order_by('producto__descripcion',
                                                                                  'fecha_operacion',
                                                                                  'cantidad_salida',
                                                                                  'created')
        totales = listado_kardex.aggregate(cantidad_ingreso=Sum('cantidad_ingreso'),
                                           cantidad_salida=Sum('cantidad_salida'),
                                           valor_ingreso=Sum('valor_ingreso'),
                                           valor_salida=Sum('valor_salida'))
        return (listado_kardex,
                totales['cantidad_ingreso'] or 0,
                totales['valor_ingreso'] or 0,
                totales['cantidad_salida'] or 0,
                totales['valor_salida'] or 0)


class Producto(TimeStampedModel):
    codigo = models.CharField(primary_key=True, max_length=10)
    grupo_productos = models.ForeignKey(GrupoProductos, on_delete=models.CASCADE)
    descripcion = models.CharField(max_length=100, unique=True)
    es_servicio = models.BooleanField(default=False)
    unidad_medida = models.ForeignKey(UnidadMedida, on_delete=models.CASCADE)
    marca = models.CharField(max_length=40, blank=True)
    modelo = models.CharField(max_length=40, blank=True)
    precio = models.DecimalField(max_digits=15, decimal_places=5, default=0)
    stock_minimo = models.DecimalField(max_digits=15, decimal_places=5, default=0)
    imagen = models.ImageField(upload_to='productos', default='productos/sinimagen.png')
    tipo_existencia = models.ForeignKey(TipoExistencia, on_delete=models.CASCADE, null=True)
    estado = models.BooleanField(default=True)
    objects = NavegableQuerySet.as_manager()
    history = HistoricalRecords()

    @property
    def stock(self):
        """Ultimo kardex de cada almacen, en una sola consulta.

        Antes recorria Almacen.objects.all() lanzando un .latest() por almacen, y
        las plantillas invocan la property varias veces en la misma pagina. El
        resultado se memoriza para no repetirla en el mismo render.
        """
        if not hasattr(self, '_stock_calculado'):
            from almacen.models import Kardex
            ultimos = (Kardex.objects.filter(producto=self)
                       .order_by('almacen_id', '-fecha_operacion', '-pk')
                       .distinct('almacen_id'))
            self._stock_calculado = sum(kardex.cantidad_total for kardex in ultimos)
        return self._stock_calculado

    @property
    def previsto(self):
        if not hasattr(self, '_previsto_calculado'):
            from compras.models import DetalleOrdenCompra
            self._previsto_calculado = DetalleOrdenCompra.objects.filter(
                Q(producto=self) | Q(detalle_cotizacion__detalle_requerimiento__producto=self)
            ).aggregate(total=Sum('cantidad'))['total'] or 0
        return self._previsto_calculado

    def obtener_kardex(self, almacen, desde, hasta):
        from almacen.models import Movimiento, Kardex
        hasta = hasta + datetime.timedelta(days=1)
        listado_kardex = Kardex.objects.filter(almacen=almacen,
                                               movimiento__estado=Movimiento.STATUS.ACT,
                                               fecha_operacion__gte=desde,
                                               fecha_operacion__lte=hasta,
                                               producto=self).select_related(
            'movimiento__tipo_documento', 'movimiento__tipo_movimiento').order_by('producto__descripcion',
                                                                                  'fecha_operacion',
                                                                                  'cantidad_salida',
                                                                                  'created')
        totales = listado_kardex.aggregate(cantidad_ingreso=Sum('cantidad_ingreso'),
                                           cantidad_salida=Sum('cantidad_salida'),
                                           valor_ingreso=Sum('valor_ingreso'),
                                           valor_salida=Sum('valor_salida'))
        return (listado_kardex,
                totales['cantidad_ingreso'] or 0,
                totales['valor_ingreso'] or 0,
                totales['cantidad_salida'] or 0,
                totales['valor_salida'] or 0)

    class Meta:
        permissions = (('ver_bienvenida', 'Puede ver bienvenida a la aplicación'),
                       ('cargar_productos', 'Puede cargar Productos desde un archivo externo'),
                       ('ver_detalle_producto', 'Puede ver detalle de Productos'),
                       ('ver_tabla_productos', 'Puede ver tabla Productos'),
                       ('ver_reporte_productos_excel', 'Puede ver Reporte de Productos en excel'),
                       ('puede_hacer_busqueda_producto', 'Puede hacer busqueda Producto'),)

    def anterior(self):
        ant = Producto.objects.anterior(self)
        return ant.pk

    def siguiente(self):
        sig = Producto.objects.siguiente(self)
        return sig.pk

    def save(self, *args, **kwargs):
        if self.codigo == '':
            prod_ant = Producto.objects.filter(grupo_productos=self.grupo_productos).aggregate(Max('codigo'))
            cod_ant = prod_ant['codigo__max']
            if cod_ant is None:
                self.codigo = self.grupo_productos.codigo + '0001'
            else:
                aux = int(cod_ant) + 1
                self.codigo = str(aux).zfill(10)
            if self.es_servicio:
                unidad_medida, creado = UnidadMedida.objects.get_or_create(codigo='SERV',
                                                                           defaults={'descripcion': 'SERVICIO'})
                self.unidad_medida = unidad_medida
        super(Producto, self).save()

    def __str__(self):
        return force_str(self.descripcion)
