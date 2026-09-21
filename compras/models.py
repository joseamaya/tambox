# -*- coding: utf-8 -*- 
from django.db import models
from django.utils.encoding import force_str
from model_utils import Choices
from django.utils.translation import gettext as _
from requerimientos.models import Requirement, RequirementDetail
from model_utils.models import TimeStampedModel
from django.db.models import Max
from contabilidad.models import PaymentMethod
from productos.models import Product
from tambox.querysets import NavigableQuerySet
from tambox.statuses import classify, PARTIAL, EMPTY
from compras.settings import CHOICES_ESTADO_COTIZ
from tambox.config import configuration
from compras.managers import QuotationDetailManager, \
    ServiceConformityDetailManager
from tambox.util import to_word
from simple_history.models import HistoricalRecords


class DetalleOrdenManager(models.Manager):

    def bulk_create(self, objs, quotation):
        if quotation is not None:
            self.guardar_detalles_con_referencia(objs, quotation)
        else:
            self.guardar_detalles_sin_referencia(objs)

    def actualizar_cotizaciones(self):
        cotizaciones = Quotation.objects.filter(status=Quotation.STATUS.PEND)
        for cot in cotizaciones:
            cot.establecer_estado_comprado()
            cot.save()

    def actualizar_detalle_cotizaciones(self, requirement_detail):
        if requirement_detail.status == RequirementDetail.STATUS.COMP:
            QuotationDetail.objects.filter(requirement_detail=requirement_detail,
                                             status=QuotationDetail.STATUS.PEND).update(
                status=QuotationDetail.STATUS.DESC)

    def guardar_detalles_con_referencia(self, objs, quotation):
        requirement = quotation.requirement
        for detalle in objs:
            quotation_detail = detalle.quotation_detail
            quotation_detail.purchased_quantity = quotation_detail.purchased_quantity + detalle.quantity
            quotation_detail.establecer_estado_comprado()
            quotation_detail.save()
            requirement_detail = quotation_detail.requirement_detail
            requirement_detail.purchased_quantity = requirement_detail.purchased_quantity + quotation_detail.purchased_quantity
            requirement_detail.establecer_estado_comprado()
            requirement_detail.save()
            self.actualizar_detalle_cotizaciones(requirement_detail)
            detalle.save()
        requirement.establecer_estado_comprado()
        requirement.save()
        quotation.establecer_estado_comprado()
        quotation.save()
        self.actualizar_cotizaciones()

    def guardar_detalles_sin_referencia(self, objs):
        for detalle in objs:
            detalle.save()


class LegalRepresentative(TimeStampedModel):
    document = models.CharField(primary_key=True, max_length=11)
    name = models.CharField(max_length=150)
    position = models.CharField(max_length=50)
    history = HistoricalRecords()

    class Meta:
        permissions = (('can_view', 'Can view Representante Legal'),
                       ('can_view_listado', 'Can view Listado Representante Legal'),
                       ('can_view_excel', 'Can view Representante Legal excel'),)

    def __str__(self):
        return self.name


class Supplier(TimeStampedModel):
    tax_id = models.CharField(unique=True, max_length=11)
    business_name = models.CharField(max_length=150)
    address = models.CharField(max_length=200)
    phone = models.CharField(max_length=15, null=True)
    email = models.EmailField(null=True)
    sunat_status = models.CharField(max_length=50)
    sunat_condition = models.CharField(max_length=50)
    representantes = models.ManyToManyField(LegalRepresentative, related_name='suppliers')
    ciiu = models.CharField(max_length=250)
    registration_date = models.DateField()
    is_active = models.BooleanField(default=True)
    objects = NavigableQuerySet.as_manager()
    history = HistoricalRecords()

    class Meta:
        permissions = (('ver_detalle_proveedor', 'Puede ver detalle Proveedor'),
                       ('ver_tabla_proveedores', 'Puede ver tabla de Proveedores'),
                       ('ver_reporte_proveedores_excel', 'Puede ver Reporte Proveedores en excel'),)
        ordering = ['tax_id']

    def anterior(self):
        ant = Supplier.objects.anterior(self)
        return ant.pk

    def siguiente(self):
        sig = Supplier.objects.siguiente(self)
        return sig.pk

    def __str__(self):
        return force_str(self.business_name)


class Quotation(TimeStampedModel):
    code = models.CharField(unique=True, max_length=12)
    supplier = models.ForeignKey(Supplier, on_delete=models.CASCADE, related_name='quotations')
    requirement = models.ForeignKey(Requirement, on_delete=models.CASCADE, related_name='quotations', null=True)
    date = models.DateField()
    notes = models.TextField(blank=True)
    STATUS = CHOICES_ESTADO_COTIZ
    status = models.CharField(choices=STATUS, default=STATUS.PEND, max_length=20)
    objects = NavigableQuerySet.as_manager()
    history = HistoricalRecords()

    def anterior(self):
        ant = Quotation.objects.anterior(self)
        return ant.pk

    def siguiente(self):
        sig = Quotation.objects.siguiente(self)
        return sig.pk

    def eliminar_cotizacion(self):
        self.status = Quotation.STATUS.CANC
        self.save()

    def eliminar_referencia(self):
        quotation = self
        requirement = quotation.requirement
        detalles = QuotationDetail.objects.filter(quotation=quotation)
        for detalle in detalles:
            requirement_detail = detalle.requirement_detail
            if requirement_detail.quoted_quantity > 0:
                requirement_detail.quoted_quantity = requirement_detail.quoted_quantity - detalle.quantity
            requirement_detail.establecer_estado_cotizado()
            requirement_detail.save()
        requirement.establecer_estado_cotizado()
        requirement.save()
        QuotationDetail.objects.filter(quotation=quotation).delete()

    def establecer_estado_comprado(self):
        total = 0
        total_comprado = 0
        for detalle in QuotationDetail.objects.filter(quotation=self):
            total = total + detalle.quantity
            total_comprado = total_comprado + detalle.purchased_quantity
        caso = classify(total_comprado, total)
        if caso == EMPTY:
            estado = Quotation.STATUS.DESC
        elif caso == PARTIAL:
            estado = Quotation.STATUS.ELEG_PARC
        else:
            estado = Quotation.STATUS.ELEG
        self.status = estado
        return self.status

    class Meta:
        unique_together = (('supplier', 'requirement'),)
        permissions = (('ver_detalle_cotizacion', 'Puede ver detalle de Cotización'),
                       ('ver_tabla_cotizaciones', 'Puede ver tabla Cotizaciones'),
                       ('ver_reporte_cotizaciones_excel', 'Puede ver Reporte de Cotizaciones en excel'),
                       ('puede_hacer_transferencia_cotizacion', 'Puede hacer transferencia de Cotización'),)

    def save(self, *args, **kwargs):
        if self.code == '':
            anio = self.date.year
            mov_ant = Quotation.objects.filter(date__year=anio).aggregate(Max('code'))
            id_ant = mov_ant['code__max']
            if id_ant is None:
                aux = 1
            else:
                aux = int(id_ant[-6:]) + 1
            correlativo = str(aux).zfill(6)
            self.code = 'CO' + str(anio) + correlativo
        super(Quotation, self).save()

    def __str__(self):
        return self.code


class QuotationDetail(TimeStampedModel):
    objects = QuotationDetailManager()
    line_number = models.IntegerField()
    quotation = models.ForeignKey(Quotation, on_delete=models.CASCADE, related_name='details')
    requirement_detail = models.ForeignKey(RequirementDetail, on_delete=models.CASCADE, related_name='quotation_details', null=True)
    quantity = models.DecimalField(max_digits=15, decimal_places=5)
    purchased_quantity = models.DecimalField(max_digits=15, decimal_places=5, default=0)
    STATUS = Choices(('PEND', _('PENDIENTE')),
                     ('ELEG', _('ELEGIDA')),
                     ('ELEG_PARC', _('ELEGIDA PARCIALMENTE')),
                     ('DESC', _('DESCARTADA')),
                     ('CANC', _('CANCELADO')), )
    status = models.CharField(choices=STATUS, default=STATUS.PEND, max_length=20)
    history = HistoricalRecords()

    def establecer_estado_comprado(self):
        caso = classify(self.purchased_quantity, self.quantity)
        if caso == EMPTY:
            estado = QuotationDetail.STATUS.PEND
        elif caso == PARTIAL:
            estado = QuotationDetail.STATUS.ELEG_PARC
        else:
            estado = QuotationDetail.STATUS.ELEG
        self.status = estado
        return self.status

    class Meta:
        permissions = (('can_view', 'Can view Detalle Orden de Compra'),)


class PurchaseOrder(TimeStampedModel):
    code = models.CharField(unique=True, max_length=12)
    quotation = models.ForeignKey(Quotation, on_delete=models.CASCADE, related_name='purchase_orders', null=True)
    supplier = models.ForeignKey(Supplier, on_delete=models.CASCADE, related_name='purchase_orders', null=True)
    date = models.DateField()
    payment_method = models.ForeignKey(PaymentMethod, on_delete=models.CASCADE, related_name='purchase_orders')
    notes = models.TextField(default='')
    STATUS = Choices(('PEND', _('PENDIENTE')),
                     ('ING', _('INGRESADA')),
                     ('ING_PARC', _('INGRESADA PARCIALMENTE')),
                     ('CANC', _('CANCELADA')),
                     )
    with_tax = models.BooleanField(default=False)
    in_dollars = models.BooleanField(default=False)
    status = models.CharField(choices=STATUS, default=STATUS.PEND, max_length=20)
    objects = NavigableQuerySet.as_manager()
    history = HistoricalRecords()

    def anterior(self):
        ant = PurchaseOrder.objects.anterior(self)
        return ant.pk

    def siguiente(self):
        sig = PurchaseOrder.objects.siguiente(self)
        return sig.pk

    def eliminar_referencia(self):
        quotation = self.quotation
        requirement = quotation.requirement
        detalles = PurchaseOrderDetail.objects.filter(order=self)
        for detalle in detalles:
            quotation_detail = detalle.quotation_detail
            quotation_detail.purchased_quantity = quotation_detail.purchased_quantity - detalle.quantity
            quotation_detail.establecer_estado_comprado()
            quotation_detail.save()
            requirement_detail = quotation_detail.requirement_detail
            requirement_detail.purchased_quantity = requirement_detail.purchased_quantity - detalle.quantity
            requirement_detail.establecer_estado_comprado()
            requirement_detail.save()
        quotation.establecer_estado_comprado()
        requirement.establecer_estado_comprado()
        quotation.save()

    def establecer_estado(self):
        total = 0
        total_ingresado = 0
        for detalle in PurchaseOrderDetail.objects.filter(order=self):
            total = total + detalle.quantity
            total_ingresado = total_ingresado + detalle.received_quantity
        caso = classify(total_ingresado, total)
        if caso == EMPTY:
            estado = PurchaseOrder.STATUS.PEND
        elif caso == PARTIAL:
            estado = PurchaseOrder.STATUS.ING_PARC
        else:
            estado = PurchaseOrder.STATUS.ING
        self.status = estado
        return self.status

    @property
    def total(self):
        total = self.subtotal + self.impuesto
        return total

    @property
    def impuesto(self):
        """Se memoriza: `total` y `total_in_words` la encadenan, y las plantillas
        las invocan mas de una vez en la misma pagina.

        No se convierte en agregado SQL a proposito: suma una propiedad que
        redondea fila a fila, y SUM(...) redondearia una sola vez al final, lo
        que cambia los ultimos decimales del importe.
        """
        if not hasattr(self, '_impuesto_calculado'):
            imp = 0
            for detalle in self.details.all():
                imp = imp + detalle.impuesto
            self._impuesto_calculado = imp
        return self._impuesto_calculado

    @property
    def subtotal(self):
        if not hasattr(self, '_subtotal_calculado'):
            subtotal = 0
            for detalle in self.details.all():
                subtotal = subtotal + detalle.valor_sin_igv
            self._subtotal_calculado = subtotal
        return self._subtotal_calculado

    @property
    def total_in_words(self):
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
            mov_ant = PurchaseOrder.objects.filter(date__year=anio).aggregate(Max('code'))
            id_ant = mov_ant['code__max']
            if id_ant is None:
                aux = 1
            else:
                aux = int(id_ant[-6:]) + 1
            correlativo = str(aux).zfill(6)
            self.code = 'OC' + str(anio) + correlativo
        super(PurchaseOrder, self).save()

    def __str__(self):
        return self.code


class PurchaseOrderDetail(TimeStampedModel):
    objects = DetalleOrdenManager()
    line_number = models.IntegerField()
    order = models.ForeignKey(PurchaseOrder, on_delete=models.CASCADE, related_name='details')
    quotation_detail = models.ForeignKey(QuotationDetail, on_delete=models.CASCADE, related_name='purchase_order_details', null=True)
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='purchase_order_details', null=True)
    quantity = models.DecimalField(max_digits=25, decimal_places=8)
    received_quantity = models.DecimalField(max_digits=25, decimal_places=8, default=0)
    price = models.DecimalField(max_digits=25, decimal_places=8)
    STATUS = Choices(('PEND', _('PENDIENTE')),
                     ('ING', _('INGRESADO')),
                     ('ING_PARC', _('INGRESADO PARCIALMENTE')),
                     ('CANC', _('CANCELADO')),
                     )
    status = models.CharField(choices=STATUS, default=STATUS.PEND, max_length=20)
    history = HistoricalRecords()

    @property
    def precio_con_igv(self):
        if self.order.with_tax:
            precio_con_igv = self.price
        else:
            monto_impuesto = configuration().purchase_tax.amount
            precio_con_igv = round(self.price * (monto_impuesto + 1), 5)
        return precio_con_igv

    @property
    def precio_sin_igv(self):
        if self.order.with_tax:
            monto_impuesto = configuration().purchase_tax.amount
            precio_sin_igv = round(self.price / (monto_impuesto + 1), 5)
        else:
            precio_sin_igv = self.price
        return precio_sin_igv

    @property
    def valor_sin_igv(self):
        if self.order.with_tax:
            monto_impuesto = configuration().purchase_tax.amount
            valor_sin_igv = (self.price * self.quantity) / (monto_impuesto + 1)
        else:
            valor_sin_igv = self.price * self.quantity
        return round(valor_sin_igv, 5)

    @property
    def valor_con_igv(self):
        if self.order.with_tax:
            valor_con_igv = self.price * self.quantity
        else:
            monto_impuesto = configuration().purchase_tax.amount
            valor_con_igv = (self.price * self.quantity) * (monto_impuesto + 1)
        return round(valor_con_igv, 5)

    @property
    def impuesto(self):
        monto_impuesto = configuration().purchase_tax.amount
        if self.order.with_tax:
            imp = self.price * self.quantity - (self.price * self.quantity) / (monto_impuesto + 1)
        else:
            imp = self.price * self.quantity * monto_impuesto
        return round(imp, 5)

    def establecer_estado(self):
        caso = classify(self.received_quantity, self.quantity)
        if caso == EMPTY:
            estado = PurchaseOrderDetail.STATUS.PEND
        elif caso == PARTIAL:
            estado = PurchaseOrderDetail.STATUS.ING_PARC
        else:
            estado = PurchaseOrderDetail.STATUS.ING
        self.status = estado
        return self.status

    class Meta:
        permissions = (('can_view', 'Can view Detalle Orden de Compra'),)


class ServiceOrder(TimeStampedModel):
    code = models.CharField(unique=True, max_length=12)
    quotation = models.ForeignKey(Quotation, on_delete=models.CASCADE, related_name='service_orders', null=True)
    supplier = models.ForeignKey(Supplier, on_delete=models.CASCADE, related_name='service_orders', null=True)
    payment_method = models.ForeignKey(PaymentMethod, on_delete=models.CASCADE, related_name='service_orders')
    process = models.CharField(max_length=50, default='')
    report_name = models.CharField(max_length=150, default='')
    report = models.FileField(upload_to='informes', null=True)
    date = models.DateField()
    notes = models.TextField(default='')
    STATUS = Choices(('PEND', _('PENDIENTE')),
                     ('CONF', _('CONFORME')),
                     ('CONF_PARC', _('CONFORME PARCIALMENTE')),
                     ('CANC', _('CANCELADA')),
                     )
    status = models.CharField(choices=STATUS, default=STATUS.PEND, max_length=20)
    objects = NavigableQuerySet.as_manager()
    history = HistoricalRecords()

    @property
    def subtotal(self):
        if not hasattr(self, '_subtotal_calculado'):
            self._subtotal_calculado = sum(detalle.amount
                                           for detalle in self.details.all())
        return self._subtotal_calculado

    @property
    def impuesto(self):
        return 0

    @property
    def total(self):
        total = self.subtotal
        return total

    @property
    def total_in_words(self):
        letras = to_word(self.total).upper()
        return letras

    def anterior(self):
        ant = ServiceOrder.objects.anterior(self)
        return ant.pk

    def siguiente(self):
        sig = ServiceOrder.objects.siguiente(self)
        return sig.pk

    def eliminar_referencia(self):
        quotation = self.quotation
        requirement = self.quotation
        detalles = ServiceOrderDetail.objects.filter(order=self)
        for detalle in detalles:
            quotation_detail = detalle.quotation_detail
            quotation_detail.purchased_quantity = quotation_detail.purchased_quantity - detalle.quantity
            quotation_detail.establecer_estado_comprado()
            quotation_detail.save()
            requirement_detail = quotation_detail.requirement_detail
            requirement_detail.purchased_quantity = requirement_detail.purchased_quantity - detalle.quantity
            requirement_detail.establecer_estado_comprado()
            requirement_detail.save()
        quotation.establecer_estado_comprado()
        requirement.establecer_estado_comprado()
        quotation.save()

    def establecer_estado(self):
        total = 0
        total_conforme = 0
        for detalle in ServiceOrderDetail.objects.filter(order=self):
            total = total + detalle.quantity
            total_conforme = total_conforme + detalle.conformed_quantity
        caso = classify(total_conforme, total)
        if caso == EMPTY:
            estado = ServiceOrder.STATUS.PEND
        elif caso == PARTIAL:
            estado = ServiceOrder.STATUS.CONF_PARC
        else:
            estado = ServiceOrder.STATUS.CONF
        self.status = estado
        return self.status

    class Meta:
        permissions = (('ver_detalle_orden_servicios', 'Puede ver detalle de Orden de Servicios'),
                       ('ver_tabla_ordenes_servicios', 'Puede ver tabla de Ordenes de Servicios'),
                       ('ver_reporte_ordenes_servicios_excel', 'Puede ver Reporte de Ordenes de Servicios en excel'),)
        ordering = ('code',)

    def generar_code(self):
        anio = self.date.year
        mov_ant = ServiceOrder.objects.filter(date__year=anio).aggregate(Max('code'))
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
        super(ServiceOrder, self).save()

    def __str__(self):
        return self.code


class ServiceOrderDetail(TimeStampedModel):
    objects = DetalleOrdenManager()
    line_number = models.IntegerField()
    order = models.ForeignKey(ServiceOrder, on_delete=models.CASCADE, related_name='details')
    quotation_detail = models.ForeignKey(QuotationDetail, on_delete=models.CASCADE, related_name='service_order_details', null=True)
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='service_order_details', null=True)
    quantity = models.DecimalField(max_digits=15, decimal_places=5)
    conformed_quantity = models.DecimalField(max_digits=15, decimal_places=5, default=0)
    price = models.DecimalField(max_digits=15, decimal_places=5)
    STATUS = Choices(('PEND', _('PENDIENTE')),
                     ('CONF', _('CONFORME')),
                     ('CONF_PARC', _('CONFORME PARCIALMENTE')),
                     ('CANC', _('CANCELADA')),
                     )
    status = models.CharField(choices=STATUS, default=STATUS.PEND, max_length=20)
    history = HistoricalRecords()

    @property
    def amount(self):
        return round(self.price * self.quantity, 5)

    @property
    def impuesto(self):
        return 0

    class Meta:
        permissions = (('ver_detalle_orden_servicios', 'Puede ver Detalle Orden de Servicios'),)
        ordering = ['line_number']

    def establecer_estado_atendido(self):
        caso = classify(self.conformed_quantity, self.quantity)
        if caso == EMPTY:
            estado = ServiceOrderDetail.STATUS.PEND
        elif caso == PARTIAL:
            estado = ServiceOrderDetail.STATUS.CONF_PARC
        else:
            estado = ServiceOrderDetail.STATUS.CONF
        self.status = estado
        return self.status


class ServiceConformity(TimeStampedModel):
    code = models.CharField(unique=True, max_length=12)
    service_order = models.ForeignKey(ServiceOrder, on_delete=models.CASCADE, related_name='conformities')
    supporting_document = models.CharField(max_length=50)
    file = models.FileField(upload_to='informes', null=True)
    date = models.DateField()
    total = models.DecimalField(max_digits=15, decimal_places=5)
    total_in_words = models.CharField(max_length=150)
    is_active = models.BooleanField(default=True)
    objects = NavigableQuerySet.as_manager()
    history = HistoricalRecords()

    class Meta:
        permissions = (('ver_detalle_conformidad_servicio', 'Puede ver detalle de Conformidad de Servicio'),
                       ('ver_tabla_conformidades_servicio', 'Puede ver tabla de Conformidades de Servicio'),
                       ('ver_reporte_conformidades_servicio_excel',
                        'Puede ver Reporte de Conformidades de Servicio en excel'),)

    def anterior(self):
        ant = ServiceConformity.objects.anterior(self)
        return ant.pk

    def siguiente(self):
        sig = ServiceConformity.objects.siguiente(self)
        return sig.pk

    def eliminar_referencia(self):
        order = self.service_order
        quotation = order.quotation
        requirement = quotation.requirement
        detalles = ServiceConformityDetail.objects.filter(conformity=self)
        for detalle in detalles:
            detalle_orden = detalle.service_order_detail
            detalle_orden.conformed_quantity = detalle_orden.conformed_quantity - detalle.quantity
            detalle_orden.establecer_estado_atendido()
            detalle_orden.save()
            requirement_detail = detalle_orden.quotation_detail.requirement_detail
            requirement_detail.served_quantity = requirement_detail.served_quantity - detalle.quantity
            requirement_detail.establecer_estado_atendido()
            requirement_detail.save()
        order.establecer_estado()
        order.save()
        requirement.establecer_estado_atendido()
        requirement.save()

    def save(self, *args, **kwargs):
        if self.code == '':
            anio = self.date.year
            conf_ant = ServiceConformity.objects.filter(date__year=anio).aggregate(Max('code'))
            id_ant = conf_ant['code__max']
            if id_ant is None:
                aux = 1
            else:
                aux = int(id_ant[-6:]) + 1
            correlativo = str(aux).zfill(6)
            self.code = 'CS' + str(anio) + correlativo
        super(ServiceConformity, self).save()

    def __str__(self):
        return self.code


class ServiceConformityDetail(TimeStampedModel):
    objects = ServiceConformityDetailManager()
    line_number = models.IntegerField()
    conformity = models.ForeignKey(ServiceConformity, on_delete=models.CASCADE, related_name='details')
    service_order_detail = models.ForeignKey(ServiceOrderDetail, on_delete=models.CASCADE, related_name='conformity_details', null=True)
    quantity = models.DecimalField(max_digits=15, decimal_places=5, default=0)
    history = HistoricalRecords()
