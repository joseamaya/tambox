# -*- coding: utf-8 -*- 
from django.db import models
from model_utils.models import TimeStampedModel
from contabilidad.models import Account, StockType
from django.db.models import Max
from django.utils.encoding import force_str
from tambox.querysets import NavigableQuerySet
from tambox.dates import aware
from simple_history.models import HistoricalRecords
from django.db.models import Q
import datetime
from django.db.models import Sum


class UnitOfMeasure(TimeStampedModel):
    code = models.CharField(max_length=5, unique=True)
    sunat_code = models.CharField(max_length=2)
    description = models.CharField(max_length=50)
    is_active = models.BooleanField(default=True)
    objects = NavigableQuerySet.as_manager()
    history = HistoricalRecords()

    class Meta:
        permissions = (('ver_detalle_unidad_medida', 'Puede ver detail Unidad de Medida'),
                       ('ver_tabla_unidades_medida', 'Puede ver tabla de unidades de medida'),
                       ('ver_reporte_unidades_medida_excel', 'Puede ver Reporte Unidades de Medida en excel'),)
        ordering = ['code']

    def previous(self):
        previous = UnitOfMeasure.objects.previous(self)
        return previous.pk

    def next(self):
        sig = UnitOfMeasure.objects.next(self)
        return sig.pk

    def __str__(self):
        return self.description


class ProductGroup(TimeStampedModel):
    code = models.CharField(primary_key=True, max_length=6)
    description = models.CharField(max_length=100)
    account = models.ForeignKey(Account, on_delete=models.CASCADE, related_name='product_groups')
    contains_products = models.BooleanField(default=True)
    is_active = models.BooleanField(default=True)
    objects = NavigableQuerySet.as_manager()
    history = HistoricalRecords()

    class Meta:
        permissions = (('cargar_grupo_productos', 'Puede cargar Grupos de Productos desde un archivo externo'),
                       ('ver_detalle_grupo_productos', 'Puede ver detail Grupo de Productos'),
                       ('ver_tabla_grupos_productos', 'Puede ver table Grupos de Productos'),
                       ('ver_reporte_grupo_productos_excel', 'Puede ver Reporte de grupo de productos en excel'),)

    def save(self, *args, **kwargs):
        if self.code == '':
            previous_group = ProductGroup.objects.all().aggregate(Max('code'))
            previous_code = previous_group['code__max']
            if previous_code is None:
                aux = 1
            else:
                aux = int(previous_code) + 1
            self.code = str(aux).zfill(6)
        super(ProductGroup, self).save()

    def previous(self):
        previous = ProductGroup.objects.previous(self)
        return previous.pk

    def next(self):
        sig = ProductGroup.objects.next(self)
        return sig.pk

    def __str__(self):
        return self.description

    def get_kardex(self, warehouse, start_date, end_date):
        from almacen.models import Kardex
        start_date, end_date = aware(start_date), aware(end_date) + datetime.timedelta(days=1)
        listado_kardex = Kardex.objects.filter(warehouse=warehouse,
                                               operation_date__gte=start_date,
                                               operation_date__lte=end_date,
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
    def kardex_by_batch(groups, warehouse, start_date, end_date):
        """Igual que `get_kardex()`, pero para todos los grupos de una vez.

        Devuelve {grupo_id: (rows, in_quantity, in_amount,
        out_quantity, out_amount)} con dos consultas en total.
        """
        from almacen.models import Kardex
        return Kardex.kardex_by_batch(start_date, end_date, by_group=True,
                                      warehouse=warehouse,
                                      product__product_group__in=groups)


class Product(TimeStampedModel):
    code = models.CharField(primary_key=True, max_length=10, verbose_name='Código')
    product_group = models.ForeignKey(ProductGroup, on_delete=models.CASCADE, related_name='products')
    description = models.CharField(max_length=100, unique=True, verbose_name='Descripción')
    is_service = models.BooleanField(default=False)
    unit_of_measure = models.ForeignKey(UnitOfMeasure, on_delete=models.CASCADE, related_name='products')
    brand = models.CharField(max_length=40, blank=True)
    model = models.CharField(max_length=40, blank=True)
    price = models.DecimalField(max_digits=15, decimal_places=5, default=0)
    minimum_stock = models.DecimalField(max_digits=15, decimal_places=5, default=0)
    image = models.ImageField(upload_to='productos', default='productos/sinimagen.png')
    stock_type = models.ForeignKey(StockType, on_delete=models.CASCADE, related_name='products', null=True)
    is_active = models.BooleanField(default=True, verbose_name='Estado')
    objects = NavigableQuerySet.as_manager()
    history = HistoricalRecords()

    @property
    def stock(self):
        """Ultimo kardex de cada almacén, en una sola consulta.

        Antes recorria Warehouse.objects.all() lanzando un .latest() por almacén, y
        las plantillas invocan la property varias veces en la misma page. El
        resultado se memoriza para no repetirla en el mismo render.
        """
        if not hasattr(self, '_calculated_stock'):
            from almacen.models import Kardex
            last_records = (Kardex.objects.filter(product=self)
                       .order_by('warehouse_id', '-operation_date', '-pk')
                       .distinct('warehouse_id'))
            self._calculated_stock = sum(kardex.total_quantity for kardex in last_records)
        return self._calculated_stock

    @property
    def forecast(self):
        if not hasattr(self, '_calculated_forecast'):
            from compras.models import PurchaseOrderDetail
            self._calculated_forecast = PurchaseOrderDetail.objects.filter(
                Q(product=self) | Q(quotation_detail__requirement_detail__product=self)
            ).aggregate(total=Sum('quantity'))['total'] or 0
        return self._calculated_forecast

    def get_kardex(self, warehouse, start_date, end_date):
        from almacen.models import Movement, Kardex
        start_date, end_date = aware(start_date), aware(end_date) + datetime.timedelta(days=1)
        listado_kardex = Kardex.objects.filter(warehouse=warehouse,
                                               movement__status=Movement.STATUS.ACT,
                                               operation_date__gte=start_date,
                                               operation_date__lte=end_date,
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
    def kardex_by_batch(productos, warehouse, start_date, end_date):
        """Igual que `get_kardex()`, pero para todo el lote de una vez.

        Devuelve {product_id: (rows, in_quantity, in_amount,
        out_quantity, out_amount)} con dos consultas en total, en vez de
        dos por producto.
        """
        from almacen.models import Kardex, Movement
        return Kardex.kardex_by_batch(start_date, end_date,
                                      warehouse=warehouse,
                                      product__in=productos,
                                      movement__status=Movement.STATUS.ACT)

    class Meta:
        permissions = (('ver_bienvenida', 'Puede ver bienvenida a la aplicación'),
                       ('cargar_productos', 'Puede cargar Productos desde un archivo externo'),
                       ('ver_detalle_producto', 'Puede ver detalle de Productos'),
                       ('ver_tabla_productos', 'Puede ver table Productos'),
                       ('ver_reporte_productos_excel', 'Puede ver Reporte de Productos en excel'),
                       ('puede_hacer_busqueda_producto', 'Puede hacer busqueda Producto'),)

    def previous(self):
        previous = Product.objects.previous(self)
        return previous.pk

    def next(self):
        sig = Product.objects.next(self)
        return sig.pk

    def save(self, *args, **kwargs):
        if self.code == '':
            previous_product = Product.objects.filter(product_group=self.product_group).aggregate(Max('code'))
            previous_code = previous_product['code__max']
            if previous_code is None:
                self.code = self.product_group.code + '0001'
            else:
                aux = int(previous_code) + 1
                self.code = str(aux).zfill(10)
            if self.is_service:
                unit_of_measure, creado = UnitOfMeasure.objects.get_or_create(code='SERV',
                                                                           defaults={'description': 'SERVICIO'})
                self.unit_of_measure = unit_of_measure
        super(Product, self).save()

    def __str__(self):
        return force_str(self.description)
