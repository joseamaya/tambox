# -*- coding: utf-8 -*- 
from django.db import models
from model_utils.models import TimeStampedModel
from contabilidad.models import CuentaContable, TipoExistencia
from django.db.models import Max
from django.utils.encoding import force_str
from tambox.querysets import NavegableQuerySet
from tambox.dates import aware
from simple_history.models import HistoricalRecords
from django.db.models import Q
import datetime
from django.db.models import Sum


class UnidadMedida(TimeStampedModel):
    code = models.CharField(max_length=5, unique=True)
    sunat_code = models.CharField(max_length=2)
    description = models.CharField(max_length=50)
    is_active = models.BooleanField(default=True)
    objects = NavegableQuerySet.as_manager()
    history = HistoricalRecords()

    class Meta:
        permissions = (('ver_detalle_unidad_medida', 'Puede ver detalle Unidad de Medida'),
                       ('ver_tabla_unidades_medida', 'Puede ver tabla de unidades de medida'),
                       ('ver_reporte_unidades_medida_excel', 'Puede ver Reporte Unidades de Medida en excel'),)
        ordering = ['code']

    def anterior(self):
        ant = UnidadMedida.objects.anterior(self)
        return ant.pk

    def siguiente(self):
        sig = UnidadMedida.objects.siguiente(self)
        return sig.pk

    def __str__(self):
        return self.description


class GrupoProductos(TimeStampedModel):
    code = models.CharField(primary_key=True, max_length=6)
    description = models.CharField(max_length=100)
    account = models.ForeignKey(CuentaContable, on_delete=models.CASCADE, related_name='product_groups')
    contains_products = models.BooleanField(default=True)
    is_active = models.BooleanField(default=True)
    objects = NavegableQuerySet.as_manager()
    history = HistoricalRecords()

    class Meta:
        permissions = (('cargar_grupo_productos', 'Puede cargar Grupos de Productos desde un archivo externo'),
                       ('ver_detalle_grupo_productos', 'Puede ver detalle Grupo de Productos'),
                       ('ver_tabla_grupos_productos', 'Puede ver tabla Grupos de Productos'),
                       ('ver_reporte_grupo_productos_excel', 'Puede ver Reporte de grupo de productos en excel'),)

    def save(self, *args, **kwargs):
        if self.code == '':
            grupo_ant = GrupoProductos.objects.all().aggregate(Max('code'))
            cod_ant = grupo_ant['code__max']
            if cod_ant is None:
                aux = 1
            else:
                aux = int(cod_ant) + 1
            self.code = str(aux).zfill(6)
        super(GrupoProductos, self).save()

    def anterior(self):
        ant = GrupoProductos.objects.anterior(self)
        return ant.pk

    def siguiente(self):
        sig = GrupoProductos.objects.siguiente(self)
        return sig.pk

    def __str__(self):
        return self.description

    def obtener_kardex(self, almacen, desde, hasta):
        from almacen.models import Kardex
        desde, hasta = aware(desde), aware(hasta) + datetime.timedelta(days=1)
        listado_kardex = Kardex.objects.filter(almacen=almacen,
                                               operation_date__gte=desde,
                                               operation_date__lte=hasta,
                                               product__product_group=self).select_related(
            'movement__document_type', 'movement__movement_type').order_by('product__description',
                                                                                  'operation_date',
                                                                                  'out_quantity',
                                                                                  'created')
        totales = listado_kardex.aggregate(in_quantity=Sum('in_quantity'),
                                           out_quantity=Sum('out_quantity'),
                                           in_amount=Sum('in_amount'),
                                           out_amount=Sum('out_amount'))
        return (listado_kardex,
                totales['in_quantity'] or 0,
                totales['in_amount'] or 0,
                totales['out_quantity'] or 0,
                totales['out_amount'] or 0)

    @staticmethod
    def kardex_por_lote(grupos, almacen, desde, hasta):
        """Igual que `obtener_kardex()`, pero para todos los grupos de una vez.

        Devuelve {grupo_id: (filas, in_quantity, in_amount,
        out_quantity, out_amount)} con dos consultas en total.
        """
        from almacen.models import Kardex
        return Kardex.kardex_por_lote(desde, hasta, por_grupo=True,
                                      almacen=almacen,
                                      product__product_group__in=grupos)


class Producto(TimeStampedModel):
    code = models.CharField(primary_key=True, max_length=10, verbose_name='Código')
    product_group = models.ForeignKey(GrupoProductos, on_delete=models.CASCADE, related_name='products')
    description = models.CharField(max_length=100, unique=True, verbose_name='Descripción')
    is_service = models.BooleanField(default=False)
    unit_of_measure = models.ForeignKey(UnidadMedida, on_delete=models.CASCADE, related_name='products')
    brand = models.CharField(max_length=40, blank=True)
    model = models.CharField(max_length=40, blank=True)
    price = models.DecimalField(max_digits=15, decimal_places=5, default=0)
    minimum_stock = models.DecimalField(max_digits=15, decimal_places=5, default=0)
    image = models.ImageField(upload_to='productos', default='productos/sinimagen.png')
    stock_type = models.ForeignKey(TipoExistencia, on_delete=models.CASCADE, related_name='products', null=True)
    is_active = models.BooleanField(default=True, verbose_name='Estado')
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
            ultimos = (Kardex.objects.filter(product=self)
                       .order_by('almacen_id', '-operation_date', '-pk')
                       .distinct('almacen_id'))
            self._stock_calculado = sum(kardex.total_quantity for kardex in ultimos)
        return self._stock_calculado

    @property
    def previsto(self):
        if not hasattr(self, '_previsto_calculado'):
            from compras.models import DetalleOrdenCompra
            self._previsto_calculado = DetalleOrdenCompra.objects.filter(
                Q(product=self) | Q(quotation_detail__requirement_detail__product=self)
            ).aggregate(total=Sum('quantity'))['total'] or 0
        return self._previsto_calculado

    def obtener_kardex(self, almacen, desde, hasta):
        from almacen.models import Movimiento, Kardex
        desde, hasta = aware(desde), aware(hasta) + datetime.timedelta(days=1)
        listado_kardex = Kardex.objects.filter(almacen=almacen,
                                               movement__status=Movimiento.STATUS.ACT,
                                               operation_date__gte=desde,
                                               operation_date__lte=hasta,
                                               product=self).select_related(
            'movement__document_type', 'movement__movement_type').order_by('product__description',
                                                                                  'operation_date',
                                                                                  'out_quantity',
                                                                                  'created')
        totales = listado_kardex.aggregate(in_quantity=Sum('in_quantity'),
                                           out_quantity=Sum('out_quantity'),
                                           in_amount=Sum('in_amount'),
                                           out_amount=Sum('out_amount'))
        return (listado_kardex,
                totales['in_quantity'] or 0,
                totales['in_amount'] or 0,
                totales['out_quantity'] or 0,
                totales['out_amount'] or 0)

    @staticmethod
    def kardex_por_lote(productos, almacen, desde, hasta):
        """Igual que `obtener_kardex()`, pero para todo el lote de una vez.

        Devuelve {product_id: (filas, in_quantity, in_amount,
        out_quantity, out_amount)} con dos consultas en total, en vez de
        dos por producto.
        """
        from almacen.models import Kardex, Movimiento
        return Kardex.kardex_por_lote(desde, hasta,
                                      almacen=almacen,
                                      product__in=productos,
                                      movement__status=Movimiento.STATUS.ACT)

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
        if self.code == '':
            prod_ant = Producto.objects.filter(product_group=self.product_group).aggregate(Max('code'))
            cod_ant = prod_ant['code__max']
            if cod_ant is None:
                self.code = self.product_group.code + '0001'
            else:
                aux = int(cod_ant) + 1
                self.code = str(aux).zfill(10)
            if self.is_service:
                unit_of_measure, creado = UnidadMedida.objects.get_or_create(code='SERV',
                                                                           defaults={'description': 'SERVICIO'})
                self.unit_of_measure = unit_of_measure
        super(Producto, self).save()

    def __str__(self):
        return force_str(self.description)
