# -*- coding: utf-8 -*- 
from datetime import timedelta
from decimal import Decimal

from django.db import models, transaction
from django.db.models import Max, Sum
from compras.models import OrdenCompra, DetalleOrdenCompra
from contabilidad.models import TipoDocumento
from django.utils.encoding import force_str
from administracion.models import Oficina, Trabajador, Productor
from model_utils.models import TimeStampedModel
from model_utils import Choices
from django.utils.translation import gettext as _
from productos.models import Producto
from almacen.managers import DetalleMovimientoManager
from tambox.querysets import NavegableQuerySet
from tambox.estados import clasificar, PARCIAL, VACIO
from simple_history.models import HistoricalRecords


class Almacen(TimeStampedModel):
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

    objects = NavegableQuerySet.as_manager()

    def anterior(self):
        return Almacen.objects.anterior(self).pk

    def siguiente(self):
        return Almacen.objects.siguiente(self).pk

    def __str__(self):
        return self.description


# Vislumbrar la posibilidad de agregar un campo que diga modifica price
class TipoMovimiento(TimeStampedModel):
    code = models.CharField(unique=True, max_length=10, verbose_name='Código')
    sunat_code = models.CharField(max_length=2)
    description = models.CharField(max_length=25, verbose_name='Descripción')
    increases = models.BooleanField()
    requires_reference = models.BooleanField(default=False)
    is_purchase = models.BooleanField(default=False)
    is_sale = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True, verbose_name='Estado')
    history = HistoricalRecords()

    objects = NavegableQuerySet.as_manager()

    def anterior(self):
        return TipoMovimiento.objects.anterior(self).pk

    def siguiente(self):
        return TipoMovimiento.objects.siguiente(self).pk

    class Meta:
        permissions = (('ver_detalle_tipo_movimiento', 'Puede ver detalle Tipo de Movimiento'),
                       ('ver_tabla_tipos_movimientos', 'Puede ver tabla de Tipos de Movimientos'),
                       ('ver_reporte_tipos_movimientos_excel', 'Puede ver Reporte Tipos de Movimientos en excel'),)
        ordering = ['code']

    def save(self, *args, **kwargs):
        if self.code == '':
            tipo_mov_ant = TipoMovimiento.objects.filter(increases=self.increases).aggregate(Max('code'))
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
        super(TipoMovimiento, self).save()

    def __str__(self):
        return force_str(self.description)


class Pedido(TimeStampedModel):
    code = models.CharField(unique=True, max_length=12)
    requester = models.ForeignKey(Trabajador, on_delete=models.CASCADE, related_name='orders')
    office = models.ForeignKey(Oficina, on_delete=models.CASCADE, related_name='orders')
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

    objects = NavegableQuerySet.as_manager()

    def anterior(self):
        return Pedido.objects.anterior(self).pk

    def siguiente(self):
        return Pedido.objects.siguiente(self).pk

    def establecer_estado_atendido(self):
        total = 0
        total_atendida = 0
        for detalle in DetallePedido.objects.filter(order=self):
            total = total + detalle.quantity
            total_atendida = total_atendida + detalle.served_quantity
        caso = clasificar(total_atendida, total)
        if caso == VACIO:
            estado = Pedido.STATUS.PEND
        elif caso == PARCIAL:
            estado = Pedido.STATUS.ATEN_PARC
        else:
            estado = Pedido.STATUS.ATEN
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
            mov_ant = Pedido.objects.filter(date__year=anio).aggregate(Max('code'))
            id_ant = mov_ant['code__max']
            if id_ant is None:
                aux = 1
            else:
                aux = int(id_ant[-6:]) + 1
            correlativo = str(aux).zfill(6)
            code = 'PE' + str(anio) + correlativo
            self.code = code
            super(Pedido, self).save()
        else:
            super(Pedido, self).save()


class DetallePedido(TimeStampedModel):
    line_number = models.IntegerField()
    order = models.ForeignKey(Pedido, on_delete=models.CASCADE, related_name='details')
    product = models.ForeignKey(Producto, on_delete=models.CASCADE, related_name='order_details', null=True)
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

    def cantidad_por_atender(self):
        resultado = self.quantity - self.served_quantity
        return resultado

    def establecer_estado_atendido(self):
        caso = clasificar(self.served_quantity, self.quantity)
        if caso == VACIO:
            estado = DetallePedido.STATUS.PEND
        elif caso == PARCIAL:
            estado = DetallePedido.STATUS.ATEN_PARC
        else:
            estado = DetallePedido.STATUS.ATEN
        self.status = estado
        return self.status

    class Meta:
        permissions = (('can_view', 'Can view Detalle Pedido'),)
        ordering = ['line_number']

    def __str__(self):
        return self.order.code + ' ' + str(self.line_number)


class Movimiento(TimeStampedModel):
    movement_id = models.CharField(unique=True, max_length=16)
    movement_type = models.ForeignKey(TipoMovimiento, on_delete=models.CASCADE, related_name='movements')
    reference = models.ForeignKey(OrdenCompra, on_delete=models.CASCADE, related_name='movements', null=True)
    order = models.ForeignKey(Pedido, on_delete=models.CASCADE, related_name='movements', null=True)
    document_type = models.ForeignKey(TipoDocumento, on_delete=models.CASCADE, related_name='movements', null=True)
    series = models.CharField(max_length=15, null=True)
    number = models.CharField(max_length=10, null=True)
    operation_date = models.DateTimeField()
    almacen = models.ForeignKey(Almacen, on_delete=models.CASCADE, related_name='movements')
    office = models.ForeignKey(Oficina, on_delete=models.CASCADE, related_name='movements', null=True)
    worker = models.ForeignKey(Trabajador, on_delete=models.CASCADE, related_name='movements', null=True)
    producer = models.ForeignKey(Productor, on_delete=models.CASCADE, related_name='movements', null=True)
    notes = models.TextField(default='')
    STATUS = Choices(('ACT', _('ACTIVO')),
                     ('CANC', _('CANCELADA')),
                     )
    status = models.CharField(choices=STATUS, default=STATUS.ACT, max_length=20, verbose_name='Estado')
    history = HistoricalRecords()

    objects = NavegableQuerySet.as_manager()

    def anterior(self):
        return Movimiento.objects.anterior(self).pk

    def siguiente(self):
        return Movimiento.objects.siguiente(self).pk

    @transaction.atomic
    def eliminar_referencia(self):
        order = self.reference
        requirement = None
        if order.quotation is not None:
            requirement = order.quotation.requirement
        detalles = DetalleMovimiento.objects.filter(movement=self)
        for detalle in detalles:
            purchase_order_detail = detalle.purchase_order_detail
            if purchase_order_detail.quotation_detail is not None:
                requirement_detail = purchase_order_detail.quotation_detail.requirement_detail
                requirement_detail.served_quantity = requirement_detail.served_quantity - detalle.quantity
                requirement_detail.establecer_estado_atendido()
                requirement_detail.save()
            purchase_order_detail.received_quantity = purchase_order_detail.received_quantity - detalle.quantity
            purchase_order_detail.establecer_estado()
            purchase_order_detail.save()
        order.establecer_estado()
        order.save()
        if requirement is not None:
            requirement.establecer_estado_atendido()
            requirement.save()

    @transaction.atomic
    def eliminar_pedido(self):
        order = self.order
        detalles = DetalleMovimiento.objects.filter(movement=self)
        for detalle in detalles:
            order_detail = detalle.order_detail
            order_detail.served_quantity = order_detail.served_quantity - detalle.quantity
            order_detail.establecer_estado_atendido()
            order_detail.save()
        order.establecer_estado_atendido()
        order.save()

    def eliminar_detalles(self):
        DetalleMovimiento.objects.filter(movement=self).delete()

    @transaction.atomic
    def eliminar_kardex(self):
        movement = self
        almacen = movement.almacen
        detalle_kardex = Kardex.objects.filter(movement=movement,
                                               almacen=almacen)
        for kardex in detalle_kardex:
            control = ControlProductoAlmacen.objects.get(product=kardex.product, almacen=almacen)
            control.stock = control.stock - kardex.in_quantity
            control.save()
            kardex.delete()

    @property
    def total(self):
        """Suma la columna `amount`, asi que el agregado es exacto."""
        if not hasattr(self, '_total_calculado'):
            self._total_calculado = DetalleMovimiento.objects.filter(
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
            mov_ant = Movimiento.objects.filter(movement_type__increases=tipo.increases,
                                                operation_date__year=anio).aggregate(Max('movement_id'))
            id_ant = mov_ant['movement_id__max']
            if id_ant is None:
                aux = 1
            else:
                aux = int(id_ant[-7:]) + 1
            correlativo = str(aux).zfill(7)
            code = str(tipo.code[0:1]) + str(anio) + correlativo
            self.movement_id = code
        super(Movimiento, self).save()


class DetalleMovimiento(TimeStampedModel):
    objects = DetalleMovimientoManager()
    line_number = models.IntegerField()
    movement = models.ForeignKey(Movimiento, on_delete=models.CASCADE, related_name='details')
    purchase_order_detail = models.ForeignKey(DetalleOrdenCompra, on_delete=models.CASCADE, related_name='movement_details', null=True)
    order_detail = models.ForeignKey(DetallePedido, on_delete=models.CASCADE, related_name='movement_details', null=True)
    product = models.ForeignKey(Producto, on_delete=models.CASCADE, related_name='movement_details')
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
                        almacen=movi.almacen)
        if t_movimiento.increases:
            kardex.in_quantity = self.quantity
            kardex.in_price = self.price
            kardex.in_amount = val
            kardex.out_quantity = 0
            kardex.out_price = 0
            kardex.out_amount = 0
            try:
                kardex_ant = Kardex.objects.filter(product=self.product,
                                                   almacen=self.movement.almacen,
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
                                                   almacen=self.movement.almacen,
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

        control_producto, creado = ControlProductoAlmacen.objects.update_or_create(
            almacen=self.movement.almacen,
            product=self.product,
            defaults={'stock': kardex.total_quantity,
                      'price': precio_control}
        )
        super(DetalleMovimiento, self).save()
        kardex.save()

    class Meta:
        unique_together = (('line_number', 'movement'),)


class Kardex(TimeStampedModel):
    movement = models.ForeignKey(Movimiento, on_delete=models.CASCADE, related_name='kardex_entries')
    movement_line_number = models.IntegerField()
    product = models.ForeignKey(Producto, on_delete=models.CASCADE, related_name='kardex_entries')
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
    almacen = models.ForeignKey(Almacen, on_delete=models.CASCADE, related_name='kardex_entries')
    history = HistoricalRecords()

    objects = NavegableQuerySet.as_manager()

    def anterior(self):
        return Kardex.objects.anterior(self).pk

    def siguiente(self):
        return Kardex.objects.siguiente(self).pk

    @classmethod
    def ultimos_por_producto(cls, productos, antes_de=None, **filtro):
        """Ultimo Kardex de cada producto del lote, en una sola consulta.

        Con `antes_de` devuelve el ultimo movimiento anterior a esa date, que
        es el saldo inicial de los informes de kardex.

        Las vistas pedian un `latest('operation_date')` por producto: una
        consulta por fila y, si dos movimientos compartian date,
        MultipleObjectsReturned. Aqui el desempate es por `pk`, asi que el
        resultado es el mismo pero determinista.

        `filtro` es el que identifica el almacen (`almacen=`, `almacen__pk=`,
        `almacen__code=`), porque cada vista lo tiene de una forma distinta.
        """
        from tambox.dates import aware

        consulta = cls.objects.filter(product__in=productos, **filtro)
        if antes_de is not None:
            consulta = consulta.filter(operation_date__lt=aware(antes_de))
        ultimos = (consulta.select_related('product__unit_of_measure')
                   .order_by('product_id', '-operation_date', '-pk')
                   .distinct('product_id'))
        return {kardex.product_id: kardex for kardex in ultimos}

    @classmethod
    def kardex_por_lote(cls, desde, hasta, por_grupo=False, **filtro):
        """Kardex del periodo de todo el lote, en dos consultas.

        Devuelve {clave: (filas, in_quantity, in_amount,
        out_quantity, out_amount)}, con la misma forma que
        `obtener_kardex()`, agrupado por producto o por grupo segun `por_grupo`.

        Los informes llamaban a `obtener_kardex()` dentro del bucle, o sea dos
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


class ControlProductoAlmacen(TimeStampedModel):
    product = models.ForeignKey(Producto, on_delete=models.CASCADE, related_name='warehouse_controls')
    almacen = models.ForeignKey(Almacen, on_delete=models.CASCADE, related_name='warehouse_controls')
    stock = models.DecimalField(max_digits=25, decimal_places=8, default=0)
    price = models.DecimalField(max_digits=25, decimal_places=8, default=0)
    history = HistoricalRecords()

    class Meta:
        unique_together = (('product', 'almacen'),)
        permissions = (('ver_reporte_stock_excel', 'Puede ver Reporte de Stock'),
                       ('ver_reporte_inventario_excel', 'Puede ver Inventario de Stock'),)
