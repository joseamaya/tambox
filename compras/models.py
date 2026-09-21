# -*- coding: utf-8 -*- 
from django.db import models
from django.utils.encoding import force_str
from model_utils import Choices
from django.utils.translation import gettext as _
from requerimientos.models import Requerimiento, DetalleRequerimiento
from model_utils.models import TimeStampedModel
from django.db.models import Max
from contabilidad.models import FormaPago
from productos.models import Producto
from tambox.querysets import NavegableQuerySet
from tambox.estados import clasificar, PARCIAL, VACIO
from compras.settings import CHOICES_ESTADO_COTIZ
from tambox.configuracion import configuracion
from compras.managers import DetalleCotizacionManager, \
    DetalleConformidadServicioManager
from tambox.util import to_word
from simple_history.models import HistoricalRecords


class DetalleOrdenManager(models.Manager):

    def bulk_create(self, objs, cotizacion):
        if cotizacion is not None:
            self.guardar_detalles_con_referencia(objs, cotizacion)
        else:
            self.guardar_detalles_sin_referencia(objs)

    def actualizar_cotizaciones(self):
        cotizaciones = Cotizacion.objects.filter(estado=Cotizacion.STATUS.PEND)
        for cot in cotizaciones:
            cot.establecer_estado_comprado()
            cot.save()

    def actualizar_detalle_cotizaciones(self, detalle_requerimiento):
        if detalle_requerimiento.estado == DetalleRequerimiento.STATUS.COMP:
            DetalleCotizacion.objects.filter(detalle_requerimiento=detalle_requerimiento,
                                             estado=DetalleCotizacion.STATUS.PEND).update(
                estado=DetalleCotizacion.STATUS.DESC)

    def guardar_detalles_con_referencia(self, objs, cotizacion):
        requerimiento = cotizacion.requerimiento
        for detalle in objs:
            detalle_cotizacion = detalle.detalle_cotizacion
            detalle_cotizacion.purchased_quantity = detalle_cotizacion.purchased_quantity + detalle.quantity
            detalle_cotizacion.establecer_estado_comprado()
            detalle_cotizacion.save()
            detalle_requerimiento = detalle_cotizacion.detalle_requerimiento
            detalle_requerimiento.purchased_quantity = detalle_requerimiento.purchased_quantity + detalle_cotizacion.purchased_quantity
            detalle_requerimiento.establecer_estado_comprado()
            detalle_requerimiento.save()
            self.actualizar_detalle_cotizaciones(detalle_requerimiento)
            detalle.save()
        requerimiento.establecer_estado_comprado()
        requerimiento.save()
        cotizacion.establecer_estado_comprado()
        cotizacion.save()
        self.actualizar_cotizaciones()

    def guardar_detalles_sin_referencia(self, objs):
        for detalle in objs:
            detalle.save()


class RepresentanteLegal(TimeStampedModel):
    documento = models.CharField(primary_key=True, max_length=11)
    name = models.CharField(max_length=150)
    cargo = models.CharField(max_length=50)
    history = HistoricalRecords()

    class Meta:
        permissions = (('can_view', 'Can view Representante Legal'),
                       ('can_view_listado', 'Can view Listado Representante Legal'),
                       ('can_view_excel', 'Can view Representante Legal excel'),)

    def __str__(self):
        return self.name


class Proveedor(TimeStampedModel):
    ruc = models.CharField(unique=True, max_length=11)
    razon_social = models.CharField(max_length=150)
    direccion = models.CharField(max_length=200)
    telefono = models.CharField(max_length=15, null=True)
    correo = models.EmailField(null=True)
    estado_sunat = models.CharField(max_length=50)
    condicion = models.CharField(max_length=50)
    representantes = models.ManyToManyField(RepresentanteLegal)
    ciiu = models.CharField(max_length=250)
    registration_date = models.DateField()
    estado = models.BooleanField(default=True)
    objects = NavegableQuerySet.as_manager()
    history = HistoricalRecords()

    class Meta:
        permissions = (('ver_detalle_proveedor', 'Puede ver detalle Proveedor'),
                       ('ver_tabla_proveedores', 'Puede ver tabla de Proveedores'),
                       ('ver_reporte_proveedores_excel', 'Puede ver Reporte Proveedores en excel'),)
        ordering = ['ruc']

    def anterior(self):
        ant = Proveedor.objects.anterior(self)
        return ant.pk

    def siguiente(self):
        sig = Proveedor.objects.siguiente(self)
        return sig.pk

    def __str__(self):
        return force_str(self.razon_social)


class Cotizacion(TimeStampedModel):
    code = models.CharField(unique=True, max_length=12)
    proveedor = models.ForeignKey(Proveedor, on_delete=models.CASCADE)
    requerimiento = models.ForeignKey(Requerimiento, on_delete=models.CASCADE, null=True)
    date = models.DateField()
    notes = models.TextField(blank=True)
    STATUS = CHOICES_ESTADO_COTIZ
    estado = models.CharField(choices=STATUS, default=STATUS.PEND, max_length=20)
    objects = NavegableQuerySet.as_manager()
    history = HistoricalRecords()

    def anterior(self):
        ant = Cotizacion.objects.anterior(self)
        return ant.pk

    def siguiente(self):
        sig = Cotizacion.objects.siguiente(self)
        return sig.pk

    def eliminar_cotizacion(self):
        self.estado = Cotizacion.STATUS.CANC
        self.save()

    def eliminar_referencia(self):
        cotizacion = self
        requerimiento = cotizacion.requerimiento
        detalles = DetalleCotizacion.objects.filter(cotizacion=cotizacion)
        for detalle in detalles:
            detalle_requerimiento = detalle.detalle_requerimiento
            if detalle_requerimiento.quoted_quantity > 0:
                detalle_requerimiento.quoted_quantity = detalle_requerimiento.quoted_quantity - detalle.quantity
            detalle_requerimiento.establecer_estado_cotizado()
            detalle_requerimiento.save()
        requerimiento.establecer_estado_cotizado()
        requerimiento.save()
        DetalleCotizacion.objects.filter(cotizacion=cotizacion).delete()

    def establecer_estado_comprado(self):
        total = 0
        total_comprado = 0
        for detalle in DetalleCotizacion.objects.filter(cotizacion=self):
            total = total + detalle.quantity
            total_comprado = total_comprado + detalle.purchased_quantity
        caso = clasificar(total_comprado, total)
        if caso == VACIO:
            estado = Cotizacion.STATUS.DESC
        elif caso == PARCIAL:
            estado = Cotizacion.STATUS.ELEG_PARC
        else:
            estado = Cotizacion.STATUS.ELEG
        self.estado = estado
        return self.estado

    class Meta:
        unique_together = (('proveedor', 'requerimiento'),)
        permissions = (('ver_detalle_cotizacion', 'Puede ver detalle de Cotización'),
                       ('ver_tabla_cotizaciones', 'Puede ver tabla Cotizaciones'),
                       ('ver_reporte_cotizaciones_excel', 'Puede ver Reporte de Cotizaciones en excel'),
                       ('puede_hacer_transferencia_cotizacion', 'Puede hacer transferencia de Cotización'),)

    def save(self, *args, **kwargs):
        if self.code == '':
            anio = self.date.year
            mov_ant = Cotizacion.objects.filter(date__year=anio).aggregate(Max('code'))
            id_ant = mov_ant['code__max']
            if id_ant is None:
                aux = 1
            else:
                aux = int(id_ant[-6:]) + 1
            correlativo = str(aux).zfill(6)
            self.code = 'CO' + str(anio) + correlativo
        super(Cotizacion, self).save()

    def __str__(self):
        return self.code


class DetalleCotizacion(TimeStampedModel):
    objects = DetalleCotizacionManager()
    nro_detalle = models.IntegerField()
    cotizacion = models.ForeignKey(Cotizacion, on_delete=models.CASCADE)
    detalle_requerimiento = models.ForeignKey(DetalleRequerimiento, on_delete=models.CASCADE, null=True)
    quantity = models.DecimalField(max_digits=15, decimal_places=5)
    purchased_quantity = models.DecimalField(max_digits=15, decimal_places=5, default=0)
    STATUS = Choices(('PEND', _('PENDIENTE')),
                     ('ELEG', _('ELEGIDA')),
                     ('ELEG_PARC', _('ELEGIDA PARCIALMENTE')),
                     ('DESC', _('DESCARTADA')),
                     ('CANC', _('CANCELADO')), )
    estado = models.CharField(choices=STATUS, default=STATUS.PEND, max_length=20)
    history = HistoricalRecords()

    def establecer_estado_comprado(self):
        caso = clasificar(self.purchased_quantity, self.quantity)
        if caso == VACIO:
            estado = DetalleCotizacion.STATUS.PEND
        elif caso == PARCIAL:
            estado = DetalleCotizacion.STATUS.ELEG_PARC
        else:
            estado = DetalleCotizacion.STATUS.ELEG
        self.estado = estado
        return self.estado

    class Meta:
        permissions = (('can_view', 'Can view Detalle Orden de Compra'),)


class OrdenCompra(TimeStampedModel):
    code = models.CharField(unique=True, max_length=12)
    cotizacion = models.ForeignKey(Cotizacion, on_delete=models.CASCADE, null=True)
    proveedor = models.ForeignKey(Proveedor, on_delete=models.CASCADE, null=True)
    date = models.DateField()
    forma_pago = models.ForeignKey(FormaPago, on_delete=models.CASCADE)
    notes = models.TextField(default='')
    STATUS = Choices(('PEND', _('PENDIENTE')),
                     ('ING', _('INGRESADA')),
                     ('ING_PARC', _('INGRESADA PARCIALMENTE')),
                     ('CANC', _('CANCELADA')),
                     )
    con_impuesto = models.BooleanField(default=False)
    dolares = models.BooleanField(default=False)
    estado = models.CharField(choices=STATUS, default=STATUS.PEND, max_length=20)
    objects = NavegableQuerySet.as_manager()
    history = HistoricalRecords()

    def anterior(self):
        ant = OrdenCompra.objects.anterior(self)
        return ant.pk

    def siguiente(self):
        sig = OrdenCompra.objects.siguiente(self)
        return sig.pk

    def eliminar_referencia(self):
        cotizacion = self.cotizacion
        requerimiento = cotizacion.requerimiento
        detalles = DetalleOrdenCompra.objects.filter(orden=self)
        for detalle in detalles:
            detalle_cotizacion = detalle.detalle_cotizacion
            detalle_cotizacion.purchased_quantity = detalle_cotizacion.purchased_quantity - detalle.quantity
            detalle_cotizacion.establecer_estado_comprado()
            detalle_cotizacion.save()
            detalle_requerimiento = detalle_cotizacion.detalle_requerimiento
            detalle_requerimiento.purchased_quantity = detalle_requerimiento.purchased_quantity - detalle.quantity
            detalle_requerimiento.establecer_estado_comprado()
            detalle_requerimiento.save()
        cotizacion.establecer_estado_comprado()
        requerimiento.establecer_estado_comprado()
        cotizacion.save()

    def establecer_estado(self):
        total = 0
        total_ingresado = 0
        for detalle in DetalleOrdenCompra.objects.filter(orden=self):
            total = total + detalle.quantity
            total_ingresado = total_ingresado + detalle.received_quantity
        caso = clasificar(total_ingresado, total)
        if caso == VACIO:
            estado = OrdenCompra.STATUS.PEND
        elif caso == PARCIAL:
            estado = OrdenCompra.STATUS.ING_PARC
        else:
            estado = OrdenCompra.STATUS.ING
        self.estado = estado
        return self.estado

    @property
    def total(self):
        total = self.subtotal + self.impuesto
        return total

    @property
    def impuesto(self):
        """Se memoriza: `total` y `total_letras` la encadenan, y las plantillas
        las invocan mas de una vez en la misma pagina.

        No se convierte en agregado SQL a proposito: suma una propiedad que
        redondea fila a fila, y SUM(...) redondearia una sola vez al final, lo
        que cambia los ultimos decimales del importe.
        """
        if not hasattr(self, '_impuesto_calculado'):
            imp = 0
            for detalle in self.detalleordencompra_set.all():
                imp = imp + detalle.impuesto
            self._impuesto_calculado = imp
        return self._impuesto_calculado

    @property
    def subtotal(self):
        if not hasattr(self, '_subtotal_calculado'):
            subtotal = 0
            for detalle in self.detalleordencompra_set.all():
                subtotal = subtotal + detalle.valor_sin_igv
            self._subtotal_calculado = subtotal
        return self._subtotal_calculado

    @property
    def total_letras(self):
        letras = to_word(self.total).upper()
        return letras

    class Meta:
        permissions = (('ver_bienvenida', 'Puede ver bienvenida a la aplicación'),
                       ('ver_detalle_orden_compra', 'Puede ver detalle de Orden de Compra'),
                       ('ver_tabla_ordenes_compra', 'Puede ver tabla Ordenes de Compra'),
                       ('ver_reporte_ordenes_compra_excel', 'Puede ver Reporte de Ordenes de Compra en excel'),
                       ('puede_hacer_transferencia_orden_compra', 'Puede hacer transferencia de Orden de Compra'),)
        ordering = ('code',)

    def save(self, *args, **kwargs):
        if self.code == '':
            anio = self.date.year
            mov_ant = OrdenCompra.objects.filter(date__year=anio).aggregate(Max('code'))
            id_ant = mov_ant['code__max']
            if id_ant is None:
                aux = 1
            else:
                aux = int(id_ant[-6:]) + 1
            correlativo = str(aux).zfill(6)
            self.code = 'OC' + str(anio) + correlativo
        super(OrdenCompra, self).save()

    def __str__(self):
        return self.code


class DetalleOrdenCompra(TimeStampedModel):
    objects = DetalleOrdenManager()
    nro_detalle = models.IntegerField()
    orden = models.ForeignKey(OrdenCompra, on_delete=models.CASCADE)
    detalle_cotizacion = models.ForeignKey(DetalleCotizacion, on_delete=models.CASCADE, null=True)
    producto = models.ForeignKey(Producto, on_delete=models.CASCADE, null=True)
    quantity = models.DecimalField(max_digits=25, decimal_places=8)
    received_quantity = models.DecimalField(max_digits=25, decimal_places=8, default=0)
    price = models.DecimalField(max_digits=25, decimal_places=8)
    STATUS = Choices(('PEND', _('PENDIENTE')),
                     ('ING', _('INGRESADO')),
                     ('ING_PARC', _('INGRESADO PARCIALMENTE')),
                     ('CANC', _('CANCELADO')),
                     )
    estado = models.CharField(choices=STATUS, default=STATUS.PEND, max_length=20)
    history = HistoricalRecords()

    @property
    def precio_con_igv(self):
        if self.orden.con_impuesto:
            precio_con_igv = self.price
        else:
            monto_impuesto = configuracion().impuesto_compra.amount
            precio_con_igv = round(self.price * (monto_impuesto + 1), 5)
        return precio_con_igv

    @property
    def precio_sin_igv(self):
        if self.orden.con_impuesto:
            monto_impuesto = configuracion().impuesto_compra.amount
            precio_sin_igv = round(self.price / (monto_impuesto + 1), 5)
        else:
            precio_sin_igv = self.price
        return precio_sin_igv

    @property
    def valor_sin_igv(self):
        if self.orden.con_impuesto:
            monto_impuesto = configuracion().impuesto_compra.amount
            valor_sin_igv = (self.price * self.quantity) / (monto_impuesto + 1)
        else:
            valor_sin_igv = self.price * self.quantity
        return round(valor_sin_igv, 5)

    @property
    def valor_con_igv(self):
        if self.orden.con_impuesto:
            valor_con_igv = self.price * self.quantity
        else:
            monto_impuesto = configuracion().impuesto_compra.amount
            valor_con_igv = (self.price * self.quantity) * (monto_impuesto + 1)
        return round(valor_con_igv, 5)

    @property
    def impuesto(self):
        monto_impuesto = configuracion().impuesto_compra.amount
        if self.orden.con_impuesto:
            imp = self.price * self.quantity - (self.price * self.quantity) / (monto_impuesto + 1)
        else:
            imp = self.price * self.quantity * monto_impuesto
        return round(imp, 5)

    def establecer_estado(self):
        caso = clasificar(self.received_quantity, self.quantity)
        if caso == VACIO:
            estado = DetalleOrdenCompra.STATUS.PEND
        elif caso == PARCIAL:
            estado = DetalleOrdenCompra.STATUS.ING_PARC
        else:
            estado = DetalleOrdenCompra.STATUS.ING
        self.estado = estado
        return self.estado

    class Meta:
        permissions = (('can_view', 'Can view Detalle Orden de Compra'),)


class OrdenServicios(TimeStampedModel):
    code = models.CharField(unique=True, max_length=12)
    cotizacion = models.ForeignKey(Cotizacion, on_delete=models.CASCADE, null=True)
    proveedor = models.ForeignKey(Proveedor, on_delete=models.CASCADE, null=True)
    forma_pago = models.ForeignKey(FormaPago, on_delete=models.CASCADE)
    proceso = models.CharField(max_length=50, default='')
    report_name = models.CharField(max_length=150, default='')
    informe = models.FileField(upload_to='informes', null=True)
    date = models.DateField()
    notes = models.TextField(default='')
    STATUS = Choices(('PEND', _('PENDIENTE')),
                     ('CONF', _('CONFORME')),
                     ('CONF_PARC', _('CONFORME PARCIALMENTE')),
                     ('CANC', _('CANCELADA')),
                     )
    estado = models.CharField(choices=STATUS, default=STATUS.PEND, max_length=20)
    objects = NavegableQuerySet.as_manager()
    history = HistoricalRecords()

    @property
    def subtotal(self):
        if not hasattr(self, '_subtotal_calculado'):
            self._subtotal_calculado = sum(detalle.amount
                                           for detalle in self.detalleordenservicios_set.all())
        return self._subtotal_calculado

    @property
    def impuesto(self):
        return 0

    @property
    def total(self):
        total = self.subtotal
        return total

    @property
    def total_letras(self):
        letras = to_word(self.total).upper()
        return letras

    def anterior(self):
        ant = OrdenServicios.objects.anterior(self)
        return ant.pk

    def siguiente(self):
        sig = OrdenServicios.objects.siguiente(self)
        return sig.pk

    def eliminar_referencia(self):
        cotizacion = self.cotizacion
        requerimiento = self.cotizacion
        detalles = DetalleOrdenServicios.objects.filter(orden=self)
        for detalle in detalles:
            detalle_cotizacion = detalle.detalle_cotizacion
            detalle_cotizacion.purchased_quantity = detalle_cotizacion.purchased_quantity - detalle.quantity
            detalle_cotizacion.establecer_estado_comprado()
            detalle_cotizacion.save()
            detalle_requerimiento = detalle_cotizacion.detalle_requerimiento
            detalle_requerimiento.purchased_quantity = detalle_requerimiento.purchased_quantity - detalle.quantity
            detalle_requerimiento.establecer_estado_comprado()
            detalle_requerimiento.save()
        cotizacion.establecer_estado_comprado()
        requerimiento.establecer_estado_comprado()
        cotizacion.save()

    def establecer_estado(self):
        total = 0
        total_conforme = 0
        for detalle in DetalleOrdenServicios.objects.filter(orden=self):
            total = total + detalle.quantity
            total_conforme = total_conforme + detalle.conformed_quantity
        caso = clasificar(total_conforme, total)
        if caso == VACIO:
            estado = OrdenServicios.STATUS.PEND
        elif caso == PARCIAL:
            estado = OrdenServicios.STATUS.CONF_PARC
        else:
            estado = OrdenServicios.STATUS.CONF
        self.estado = estado
        return self.estado

    class Meta:
        permissions = (('ver_detalle_orden_servicios', 'Puede ver detalle de Orden de Servicios'),
                       ('ver_tabla_ordenes_servicios', 'Puede ver tabla de Ordenes de Servicios'),
                       ('ver_reporte_ordenes_servicios_excel', 'Puede ver Reporte de Ordenes de Servicios en excel'),)
        ordering = ('code',)

    def generar_code(self):
        anio = self.date.year
        mov_ant = OrdenServicios.objects.filter(date__year=anio).aggregate(Max('code'))
        id_ant = mov_ant['code__max']
        if id_ant is None:
            aux = 1
        else:
            aux = int(id_ant[-6:]) + 1
        correlativo = str(aux).zfill(6)
        code = 'OS' + str(anio) + correlativo
        return code

    def save(self, *args, **kwargs):
        if self.code == '':
            self.code = self.generar_code()
        super(OrdenServicios, self).save()

    def __str__(self):
        return self.code


class DetalleOrdenServicios(TimeStampedModel):
    objects = DetalleOrdenManager()
    nro_detalle = models.IntegerField()
    orden = models.ForeignKey(OrdenServicios, on_delete=models.CASCADE)
    detalle_cotizacion = models.ForeignKey(DetalleCotizacion, on_delete=models.CASCADE, null=True)
    producto = models.ForeignKey(Producto, on_delete=models.CASCADE, null=True)
    quantity = models.DecimalField(max_digits=15, decimal_places=5)
    conformed_quantity = models.DecimalField(max_digits=15, decimal_places=5, default=0)
    price = models.DecimalField(max_digits=15, decimal_places=5)
    STATUS = Choices(('PEND', _('PENDIENTE')),
                     ('CONF', _('CONFORME')),
                     ('CONF_PARC', _('CONFORME PARCIALMENTE')),
                     ('CANC', _('CANCELADA')),
                     )
    estado = models.CharField(choices=STATUS, default=STATUS.PEND, max_length=20)
    history = HistoricalRecords()

    @property
    def amount(self):
        return round(self.price * self.quantity, 5)

    @property
    def impuesto(self):
        return 0

    class Meta:
        permissions = (('ver_detalle_orden_servicios', 'Puede ver Detalle Orden de Servicios'),)
        ordering = ['nro_detalle']

    def establecer_estado_atendido(self):
        caso = clasificar(self.conformed_quantity, self.quantity)
        if caso == VACIO:
            estado = DetalleOrdenServicios.STATUS.PEND
        elif caso == PARCIAL:
            estado = DetalleOrdenServicios.STATUS.CONF_PARC
        else:
            estado = DetalleOrdenServicios.STATUS.CONF
        self.estado = estado
        return self.estado


class ConformidadServicio(TimeStampedModel):
    code = models.CharField(unique=True, max_length=12)
    orden_servicios = models.ForeignKey(OrdenServicios, on_delete=models.CASCADE)
    doc_sustento = models.CharField(max_length=50)
    file = models.FileField(upload_to='informes', null=True)
    date = models.DateField()
    total = models.DecimalField(max_digits=15, decimal_places=5)
    total_letras = models.CharField(max_length=150)
    estado = models.BooleanField(default=True)
    objects = NavegableQuerySet.as_manager()
    history = HistoricalRecords()

    class Meta:
        permissions = (('ver_detalle_conformidad_servicio', 'Puede ver detalle de Conformidad de Servicio'),
                       ('ver_tabla_conformidades_servicio', 'Puede ver tabla de Conformidades de Servicio'),
                       ('ver_reporte_conformidades_servicio_excel',
                        'Puede ver Reporte de Conformidades de Servicio en excel'),)

    def anterior(self):
        ant = ConformidadServicio.objects.anterior(self)
        return ant.pk

    def siguiente(self):
        sig = ConformidadServicio.objects.siguiente(self)
        return sig.pk

    def eliminar_referencia(self):
        orden = self.orden_servicios
        cotizacion = orden.cotizacion
        requerimiento = cotizacion.requerimiento
        detalles = DetalleConformidadServicio.objects.filter(conformidad=self)
        for detalle in detalles:
            detalle_orden = detalle.detalle_orden_servicios
            detalle_orden.conformed_quantity = detalle_orden.conformed_quantity - detalle.quantity
            detalle_orden.establecer_estado_atendido()
            detalle_orden.save()
            detalle_requerimiento = detalle_orden.detalle_cotizacion.detalle_requerimiento
            detalle_requerimiento.served_quantity = detalle_requerimiento.served_quantity - detalle.quantity
            detalle_requerimiento.establecer_estado_atendido()
            detalle_requerimiento.save()
        orden.establecer_estado()
        orden.save()
        requerimiento.establecer_estado_atendido()
        requerimiento.save()

    def save(self, *args, **kwargs):
        if self.code == '':
            anio = self.date.year
            conf_ant = ConformidadServicio.objects.filter(date__year=anio).aggregate(Max('code'))
            id_ant = conf_ant['code__max']
            if id_ant is None:
                aux = 1
            else:
                aux = int(id_ant[-6:]) + 1
            correlativo = str(aux).zfill(6)
            self.code = 'CS' + str(anio) + correlativo
        super(ConformidadServicio, self).save()

    def __str__(self):
        return self.code


class DetalleConformidadServicio(TimeStampedModel):
    objects = DetalleConformidadServicioManager()
    nro_detalle = models.IntegerField()
    conformidad = models.ForeignKey(ConformidadServicio, on_delete=models.CASCADE)
    detalle_orden_servicios = models.ForeignKey(DetalleOrdenServicios, on_delete=models.CASCADE, null=True)
    quantity = models.DecimalField(max_digits=15, decimal_places=5, default=0)
    history = HistoricalRecords()
