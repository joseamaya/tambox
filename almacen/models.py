# -*- coding: utf-8 -*- 
from datetime import timedelta
from decimal import Decimal

from django.db import models, transaction
from django.db.models import Max, Sum
from compras.models import PurchaseOrder, PurchaseOrderDetail
from contabilidad.models import DocumentType
from django.utils.encoding import force_str
from administracion.models import Office, Worker, Producer
from model_utils.models import TimeStampedModel
from model_utils import Choices
from django.utils.translation import gettext as _
from productos.models import Product
from almacen.managers import MovementDetailManager
from tambox.querysets import NavigableQuerySet
from tambox.statuses import classify, PARTIAL, EMPTY
from simple_history.models import HistoricalRecords


class Warehouse(TimeStampedModel):
    code = models.CharField(unique=True, max_length=5, verbose_name='Código')
    description = models.CharField(max_length=30, verbose_name='Descripción')
    is_active = models.BooleanField(default=True, verbose_name='Estado')
    history = HistoricalRecords()

    class Meta:
        verbose_name = 'Almacen'
        verbose_name_plural = 'Almacenes'
        permissions = (('ver_bienvenida', 'Puede ver bienvenida a la aplicación'),
                       ('cargar_almacenes', 'Puede cargar Almacenes desde un archivo externo'),
                       ('ver_detalle_almacen', 'Puede ver detalle Almacén'),
                       ('ver_tabla_almacenes', 'Puede ver tabla de almacenes'),
                       ('ver_reporte_almacenes_excel', 'Puede ver Reporte Almacenes en excel'),)
        ordering = ['code']

    objects = NavigableQuerySet.as_manager()

    def previous(self):
        return Warehouse.objects.previous(self).pk

    def next(self):
        return Warehouse.objects.next(self).pk

    def __str__(self):
        return self.description


# Vislumbrar la posibilidad de agregar un campo que diga modifica price
class MovementType(TimeStampedModel):
    code = models.CharField(unique=True, max_length=10, verbose_name='Código')
    sunat_code = models.CharField(max_length=2)
    description = models.CharField(max_length=25, verbose_name='Descripción')
    increases = models.BooleanField()
    requires_reference = models.BooleanField(default=False)
    is_purchase = models.BooleanField(default=False)
    is_sale = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True, verbose_name='Estado')
    history = HistoricalRecords()

    objects = NavigableQuerySet.as_manager()

    def previous(self):
        return MovementType.objects.previous(self).pk

    def next(self):
        return MovementType.objects.next(self).pk

    class Meta:
        permissions = (('ver_detalle_tipo_movimiento', 'Puede ver detalle Tipo de Movimiento'),
                       ('ver_tabla_tipos_movimientos', 'Puede ver tabla de Tipos de Movimientos'),
                       ('ver_reporte_tipos_movimientos_excel', 'Puede ver Reporte Tipos de Movimientos en excel'),)
        ordering = ['code']

    def save(self, *args, **kwargs):
        if self.code == '':
            tipo_mov_ant = MovementType.objects.filter(increases=self.increases).aggregate(Max('code'))
            cod_ant = tipo_mov_ant['code__max']

            if self.increases:
                if cod_ant is None:
                    self.code = 'I00'
                else:
                    aux = int(cod_ant[1:]) + 1
                    self.code = 'I' + str(aux).zfill(2)
            else:
                if cod_ant is None:
                    self.code = 'S01'
                else:
                    aux = int(cod_ant[1:]) + 1
                    self.code = 'S' + str(aux).zfill(2)
        super(MovementType, self).save()

    def __str__(self):
        return force_str(self.description)


class Order(TimeStampedModel):
    code = models.CharField(unique=True, max_length=12)
    requester = models.ForeignKey(Worker, on_delete=models.CASCADE, related_name='orders')
    office = models.ForeignKey(Office, on_delete=models.CASCADE, related_name='orders')
    date = models.DateField()
    notes = models.TextField(blank=True)
    STATUS = Choices(('PEND', _('PENDIENTE')),
                     ('APROB', _('APROBADO')),
                     ('DESAP', _('DESAPROBADO')),
                     ('ATEN', _('ATENDIDO')),
                     ('ATEN_PARC', _('ATENDIDO PARCIALMENTE')),
                     ('CANC', _('CANCELADO')),
                     )
    status = models.CharField(choices=STATUS, default=STATUS.PEND, max_length=20)
    history = HistoricalRecords()

    objects = NavigableQuerySet.as_manager()

    def previous(self):
        return Order.objects.previous(self).pk

    def next(self):
        return Order.objects.next(self).pk

    def set_status_served(self):
        total = 0
        total_atendida = 0
        for detail in OrderDetail.objects.filter(order=self):
            total = total + detail.quantity
            total_atendida = total_atendida + detail.served_quantity
        caso = classify(total_atendida, total)
        if caso == EMPTY:
            estado = Order.STATUS.PEND
        elif caso == PARTIAL:
            estado = Order.STATUS.ATEN_PARC
        else:
            estado = Order.STATUS.ATEN
        self.status = estado
        return self.status

    class Meta:
        permissions = (('aprobar_pedido', 'Puede aprobar Pedido'),
                       ('ver_detalle_pedido', 'Puede ver detalle de Pedido'),
                       ('ver_tabla_aprobacion_pedidos', 'Puede ver tabla de Aprobación de Pedidos'),
                       ('ver_tabla_pedidos', 'Puede ver tabla de Pedidos'),
                       ('ver_reporte_pedidos_excel', 'Puede ver Reporte de Pedidos en excel'),)

    def __str__(self):
        return self.code

    def save(self, *args, **kwargs):
        if self.code == '':
            anio = self.date.year
            mov_ant = Order.objects.filter(date__year=anio).aggregate(Max('code'))
            id_ant = mov_ant['code__max']
            if id_ant is None:
                aux = 1
            else:
                aux = int(id_ant[-6:]) + 1
            correlativo = str(aux).zfill(6)
            code = 'PE' + str(anio) + correlativo
            self.code = code
            super(Order, self).save()
        else:
            super(Order, self).save()


class OrderDetail(TimeStampedModel):
    line_number = models.IntegerField()
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='details')
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='order_details', null=True)
    quantity = models.DecimalField(max_digits=15, decimal_places=5)
    served_quantity = models.DecimalField(max_digits=15, decimal_places=5, default=0)
    STATUS = Choices(('PEND', _('PENDIENTE')),
                     ('APROB', _('APROBADO')),
                     ('DESAP', _('DESAPROBADO')),
                     ('ATEN', _('ATENDIDO')),
                     ('ATEN_PARC', _('ATENDIDO PARCIALMENTE')),
                     ('CANC', _('CANCELADO')),
                     )
    status = models.CharField(choices=STATUS, default=STATUS.PEND, max_length=20)
    history = HistoricalRecords()

    def quantity_to_serve(self):
        resultado = self.quantity - self.served_quantity
        return resultado

    def set_status_served(self):
        caso = classify(self.served_quantity, self.quantity)
        if caso == EMPTY:
            estado = OrderDetail.STATUS.PEND
        elif caso == PARTIAL:
            estado = OrderDetail.STATUS.ATEN_PARC
        else:
            estado = OrderDetail.STATUS.ATEN
        self.status = estado
        return self.status

    class Meta:
        permissions = (('can_view', 'Can view Detalle Pedido'),)
        ordering = ['line_number']

    def __str__(self):
        return self.order.code + ' ' + str(self.line_number)


class Movement(TimeStampedModel):
    movement_id = models.CharField(unique=True, max_length=16)
    movement_type = models.ForeignKey(MovementType, on_delete=models.CASCADE, related_name='movements')
    reference = models.ForeignKey(PurchaseOrder, on_delete=models.CASCADE, related_name='movements', null=True)
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='movements', null=True)
    document_type = models.ForeignKey(DocumentType, on_delete=models.CASCADE, related_name='movements', null=True)
    series = models.CharField(max_length=15, null=True)
    number = models.CharField(max_length=10, null=True)
    operation_date = models.DateTimeField()
    warehouse = models.ForeignKey(Warehouse, on_delete=models.CASCADE, related_name='movements')
    office = models.ForeignKey(Office, on_delete=models.CASCADE, related_name='movements', null=True)
    worker = models.ForeignKey(Worker, on_delete=models.CASCADE, related_name='movements', null=True)
    producer = models.ForeignKey(Producer, on_delete=models.CASCADE, related_name='movements', null=True)
    notes = models.TextField(default='')
    STATUS = Choices(('ACT', _('ACTIVO')),
                     ('CANC', _('CANCELADA')),
                     )
    status = models.CharField(choices=STATUS, default=STATUS.ACT, max_length=20, verbose_name='Estado')
    history = HistoricalRecords()

    objects = NavigableQuerySet.as_manager()

    def previous(self):
        return Movement.objects.previous(self).pk

    def next(self):
        return Movement.objects.next(self).pk

    @transaction.atomic
    def delete_reference(self):
        order = self.reference
        requirement = None
        if order.quotation is not None:
            requirement = order.quotation.requirement
        detalles = MovementDetail.objects.filter(movement=self)
        for detail in detalles:
            purchase_order_detail = detail.purchase_order_detail
            if purchase_order_detail.quotation_detail is not None:
                requirement_detail = purchase_order_detail.quotation_detail.requirement_detail
                requirement_detail.served_quantity = requirement_detail.served_quantity - detail.quantity
                requirement_detail.set_status_served()
                requirement_detail.save()
            purchase_order_detail.received_quantity = purchase_order_detail.received_quantity - detail.quantity
            purchase_order_detail.set_status()
            purchase_order_detail.save()
        order.set_status()
        order.save()
        if requirement is not None:
            requirement.set_status_served()
            requirement.save()

    @transaction.atomic
    def delete_order(self):
        order = self.order
        detalles = MovementDetail.objects.filter(movement=self)
        for detail in detalles:
            order_detail = detail.order_detail
            order_detail.served_quantity = order_detail.served_quantity - detail.quantity
            order_detail.set_status_served()
            order_detail.save()
        order.set_status_served()
        order.save()

    def delete_details(self):
        MovementDetail.objects.filter(movement=self).delete()

    @transaction.atomic
    def delete_kardex(self):
        movement = self
        warehouse = movement.warehouse
        detalle_kardex = Kardex.objects.filter(movement=movement,
                                               warehouse=warehouse)
        for kardex in detalle_kardex:
            control = WarehouseProductControl.objects.get(product=kardex.product, warehouse=warehouse)
            control.stock = control.stock - kardex.in_quantity
            control.save()
            kardex.delete()

    @property
    def total(self):
        """Suma la columna `amount`, asi que el agregado es exacto."""
        if not hasattr(self, '_total_calculado'):
            self._total_calculado = MovementDetail.objects.filter(
                movement=self).aggregate(total=Sum('amount'))['total'] or 0
        return self._total_calculado

    class Meta:
        permissions = (('ver_detalle_movimiento', 'Puede ver detalle de Movimiento'),
                       ('ver_tabla_movimientos', 'Puede ver tabla de Movimientos'),
                       ('ver_reporte_movimientos_excel', 'Puede ver Reporte de Movimientos en excel'),)
        ordering = ['movement_id']

    def __str__(self):
        return self.movement_id

    def save(self, *args, **kwargs):
        if self.movement_id == '':
            tipo = self.movement_type
            anio = self.operation_date.year
            mov_ant = Movement.objects.filter(movement_type__increases=tipo.increases,
                                                operation_date__year=anio).aggregate(Max('movement_id'))
            id_ant = mov_ant['movement_id__max']
            if id_ant is None:
                aux = 1
            else:
                aux = int(id_ant[-7:]) + 1
            correlativo = str(aux).zfill(7)
            code = str(tipo.code[0:1]) + str(anio) + correlativo
            self.movement_id = code
        super(Movement, self).save()


class MovementDetail(TimeStampedModel):
    objects = MovementDetailManager()
    line_number = models.IntegerField()
    movement = models.ForeignKey(Movement, on_delete=models.CASCADE, related_name='details')
    purchase_order_detail = models.ForeignKey(PurchaseOrderDetail, on_delete=models.CASCADE, related_name='movement_details', null=True)
    order_detail = models.ForeignKey(OrderDetail, on_delete=models.CASCADE, related_name='movement_details', null=True)
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='movement_details')
    quantity = models.DecimalField(max_digits=25, decimal_places=8)
    price = models.DecimalField(max_digits=25, decimal_places=8)
    amount = models.DecimalField(max_digits=25, decimal_places=8)
    history = HistoricalRecords()

    @transaction.atomic
    def save(self, *args, **kwargs):
        movi = self.movement
        t_movimiento = movi.movement_type
        val = self.amount
        kardex = Kardex(product=self.product,
                        operation_date=movi.operation_date,
                        movement=movi,
                        movement_line_number=self.line_number,
                        warehouse=movi.warehouse)
        if t_movimiento.increases:
            kardex.in_quantity = self.quantity
            kardex.in_price = self.price
            kardex.in_amount = val
            kardex.out_quantity = 0
            kardex.out_price = 0
            kardex.out_amount = 0
            try:
                kardex_ant = Kardex.objects.filter(product=self.product,
                                                   warehouse=self.movement.warehouse,
                                                   operation_date__lt=kardex.operation_date).latest('operation_date')
                kardex.total_quantity = self.quantity + kardex_ant.total_quantity
                kardex.total_amount = val + kardex_ant.total_amount
                kardex.total_price = self.price
            except Kardex.DoesNotExist:
                kardex.total_quantity = self.quantity
                kardex.total_price = self.price
                kardex.total_amount = val
        else:
            kardex.in_quantity = 0
            kardex.in_price = 0
            kardex.in_amount = 0
            kardex.out_quantity = self.quantity
            kardex.out_price = self.price
            kardex.out_amount = val
            try:
                kardex_ant = Kardex.objects.filter(product=self.product,
                                                   warehouse=self.movement.warehouse,
                                                   operation_date__lt=kardex.operation_date).latest('operation_date')
                kardex.total_quantity = kardex_ant.total_quantity - self.quantity
                kardex.total_amount = kardex_ant.total_amount - val
                kardex.total_price = self.price
            except Kardex.DoesNotExist:
                kardex.total_quantity = 0 - self.quantity
                kardex.total_price = 0 - self.price
                kardex.total_amount = 0 - val
        if kardex.total_quantity == 0:
            precio_control = 0
        else:
            precio_control = kardex.total_amount / kardex.total_quantity

        control_producto, creado = WarehouseProductControl.objects.update_or_create(
            warehouse=self.movement.warehouse,
            product=self.product,
            defaults={'stock': kardex.total_quantity,
                      'price': precio_control}
        )
        super(MovementDetail, self).save()
        kardex.save()

    class Meta:
        unique_together = (('line_number', 'movement'),)


class Kardex(TimeStampedModel):
    movement = models.ForeignKey(Movement, on_delete=models.CASCADE, related_name='kardex_entries')
    movement_line_number = models.IntegerField()
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='kardex_entries')
    operation_date = models.DateTimeField()
    in_quantity = models.DecimalField(max_digits=25, decimal_places=8)
    in_price = models.DecimalField(max_digits=25, decimal_places=8)
    in_amount = models.DecimalField(max_digits=25, decimal_places=8)
    out_quantity = models.DecimalField(max_digits=25, decimal_places=8)
    out_price = models.DecimalField(max_digits=25, decimal_places=8)
    out_amount = models.DecimalField(max_digits=25, decimal_places=8)
    total_quantity = models.DecimalField(max_digits=25, decimal_places=8)
    total_price = models.DecimalField(max_digits=25, decimal_places=8)
    total_amount = models.DecimalField(max_digits=25, decimal_places=8)
    warehouse = models.ForeignKey(Warehouse, on_delete=models.CASCADE, related_name='kardex_entries')
    history = HistoricalRecords()

    objects = NavigableQuerySet.as_manager()

    def previous(self):
        return Kardex.objects.previous(self).pk

    def next(self):
        return Kardex.objects.next(self).pk

    @classmethod
    def last_by_product(cls, productos, antes_de=None, **filtro):
        """Ultimo Kardex de cada producto del lote, en una sola consulta.

        Con `antes_de` devuelve el ultimo movimiento anterior a esa date, que
        es el saldo inicial de los informes de kardex.

        Las vistas pedian un `latest('operation_date')` por producto: una
        consulta por fila y, si dos movimientos compartian date,
        MultipleObjectsReturned. Aqui el desempate es por `pk`, asi que el
        resultado es el mismo pero determinista.

        `filtro` es el que identifica el almacén (`warehouse=`, `warehouse__pk=`,
        `warehouse__code=`), porque cada vista lo tiene de una forma distinta.
        """
        from tambox.dates import aware

        consulta = cls.objects.filter(product__in=productos, **filtro)
        if antes_de is not None:
            consulta = consulta.filter(operation_date__lt=aware(antes_de))
        last_records = (consulta.select_related('product__unit_of_measure')
                   .order_by('product_id', '-operation_date', '-pk')
                   .distinct('product_id'))
        return {kardex.product_id: kardex for kardex in last_records}

    @classmethod
    def kardex_by_batch(cls, desde, hasta, por_grupo=False, **filtro):
        """Kardex del periodo de todo el lote, en dos consultas.

        Devuelve {clave: (filas, in_quantity, in_amount,
        out_quantity, out_amount)}, con la misma forma que
        `get_kardex()`, agrupado por producto o por grupo segun `por_grupo`.

        Los informes llamaban a `get_kardex()` dentro del bucle, o sea dos
        consultas por producto. Los totales se suman aqui en Python: con Decimal
        el resultado es el mismo que el del agregado de SQL.
        """
        from tambox.dates import aware

        desde, hasta = aware(desde), aware(hasta) + timedelta(days=1)
        filas = (cls.objects.filter(operation_date__gte=desde,
                                    operation_date__lte=hasta,
                                    **filtro)
                 .select_related('product', 'movement__document_type',
                                 'movement__movement_type')
                 .order_by('product__description', 'operation_date',
                           'out_quantity', 'created'))
        lote = {}
        for kardex in filas:
            clave = kardex.product.product_group_id if por_grupo else kardex.product_id
            totales = lote.setdefault(clave, [[], Decimal(0), Decimal(0), Decimal(0), Decimal(0)])
            totales[0].append(kardex)
            totales[1] = totales[1] + kardex.in_quantity
            totales[2] = totales[2] + kardex.in_amount
            totales[3] = totales[3] + kardex.out_quantity
            totales[4] = totales[4] + kardex.out_amount
        return lote

    def __str__(self):
        return str(self.movement.movement_id) + '-' + str(
            self.movement_line_number) + '-' + self.product.description

    class Meta:
        verbose_name = 'Kardex'
        verbose_name_plural = 'Kardex'
        permissions = (('ver_detalle_kardex', 'Puede ver detalle de Kardex'),
                       ('ver_tabla_kardex', 'Puede ver tabla de Kardex'),
                       ('ver_reporte_kardex_excel', 'Puede ver Reporte de Kardex en excel'),)
        ordering = ['movement', 'movement_line_number']


class WarehouseProductControl(TimeStampedModel):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='warehouse_controls')
    warehouse = models.ForeignKey(Warehouse, on_delete=models.CASCADE, related_name='warehouse_controls')
    stock = models.DecimalField(max_digits=25, decimal_places=8, default=0)
    price = models.DecimalField(max_digits=25, decimal_places=8, default=0)
    history = HistoricalRecords()

    class Meta:
        unique_together = (('product', 'warehouse'),)
        permissions = (('ver_reporte_stock_excel', 'Puede ver Reporte de Stock'),
                       ('ver_reporte_inventario_excel', 'Puede ver Inventario de Stock'),)
