# -*- coding: utf-8 -*- 
from django.db import models
from django.utils.encoding import force_str
from model_utils import Choices
from django.utils.translation import gettext as _
from requirements.models import Requirement, RequirementDetail
from model_utils.models import TimeStampedModel
from django.db.models import Max
from accounting.models import PaymentMethod
from products.models import Product
from tambox.querysets import NavigableQuerySet
from tambox.statuses import classify, PARTIAL, EMPTY
from purchases.settings import QUOTATION_STATUS_CHOICES
from tambox.config import configuration
from purchases.managers import QuotationDetailManager,\
    ServiceConformityDetailManager
from tambox.util import to_word
from simple_history.models import HistoricalRecords


class OrderDetailManager(models.Manager):

    def bulk_create(self, objs, quotation):
        if quotation is not None:
            self.save_details_with_reference(objs, quotation)
        else:
            self.save_details_without_reference(objs)

    def update_quotations(self):
        quotations = Quotation.objects.filter(status=Quotation.STATUS.PEND)
        for cot in quotations:
            cot.set_status_purchased()
            cot.save()

    def update_quotation_details(self, requirement_detail):
        if requirement_detail.status == RequirementDetail.STATUS.COMP:
            QuotationDetail.objects.filter(requirement_detail=requirement_detail,
                                             status=QuotationDetail.STATUS.PEND).update(
                status=QuotationDetail.STATUS.DESC)

    def save_details_with_reference(self, objs, quotation):
        requirement = quotation.requirement
        for detail in objs:
            quotation_detail = detail.quotation_detail
            quotation_detail.purchased_quantity = quotation_detail.purchased_quantity + detail.quantity
            quotation_detail.set_status_purchased()
            quotation_detail.save()
            requirement_detail = quotation_detail.requirement_detail
            requirement_detail.purchased_quantity = requirement_detail.purchased_quantity + quotation_detail.purchased_quantity
            requirement_detail.set_status_purchased()
            requirement_detail.save()
            self.update_quotation_details(requirement_detail)
            detail.save()
        requirement.set_status_purchased()
        requirement.save()
        quotation.set_status_purchased()
        quotation.save()
        self.update_quotations()

    def save_details_without_reference(self, objs):
        for detail in objs:
            detail.save()


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
    representatives = models.ManyToManyField(LegalRepresentative, related_name='suppliers')
    ciiu = models.CharField(max_length=250)
    registration_date = models.DateField()
    is_active = models.BooleanField(default=True)
    objects = NavigableQuerySet.as_manager()
    history = HistoricalRecords()

    class Meta:
        permissions = (('ver_detalle_proveedor', 'Puede ver detail Proveedor'),
                       ('ver_tabla_proveedores', 'Puede ver tabla de Proveedores'),
                       ('ver_reporte_proveedores_excel', 'Puede ver Reporte Proveedores en excel'),)
        ordering = ['tax_id']

    def previous(self):
        previous = Supplier.objects.previous(self)
        return previous.pk

    def next(self):
        following = Supplier.objects.next(self)
        return following.pk

    def __str__(self):
        return force_str(self.business_name)


class Quotation(TimeStampedModel):
    code = models.CharField(unique=True, max_length=12)
    supplier = models.ForeignKey(Supplier, on_delete=models.CASCADE, related_name='quotations')
    requirement = models.ForeignKey(Requirement, on_delete=models.CASCADE, related_name='quotations', null=True)
    date = models.DateField()
    notes = models.TextField(blank=True)
    STATUS = QUOTATION_STATUS_CHOICES
    status = models.CharField(choices=STATUS, default=STATUS.PEND, max_length=20)
    objects = NavigableQuerySet.as_manager()
    history = HistoricalRecords()

    def previous(self):
        previous = Quotation.objects.previous(self)
        return previous.pk

    def next(self):
        following = Quotation.objects.next(self)
        return following.pk

    def delete_quotation(self):
        self.status = Quotation.STATUS.CANC
        self.save()

    def delete_reference(self):
        quotation = self
        requirement = quotation.requirement
        details = QuotationDetail.objects.filter(quotation=quotation)
        for detail in details:
            requirement_detail = detail.requirement_detail
            if requirement_detail.quoted_quantity > 0:
                requirement_detail.quoted_quantity = requirement_detail.quoted_quantity - detail.quantity
            requirement_detail.set_status_quoted()
            requirement_detail.save()
        requirement.set_status_quoted()
        requirement.save()
        QuotationDetail.objects.filter(quotation=quotation).delete()

    def set_status_purchased(self):
        total = 0
        total_purchased = 0
        for detail in QuotationDetail.objects.filter(quotation=self):
            total = total + detail.quantity
            total_purchased = total_purchased + detail.purchased_quantity
        caso = classify(total_purchased, total)
        if caso == EMPTY:
            status = Quotation.STATUS.DESC
        elif caso == PARTIAL:
            status = Quotation.STATUS.ELEG_PARC
        else:
            status = Quotation.STATUS.ELEG
        self.status = status
        return self.status

    class Meta:
        unique_together = (('supplier', 'requirement'),)
        permissions = (('ver_detalle_cotizacion', 'Puede ver detalle de Cotización'),
                       ('ver_tabla_cotizaciones', 'Puede ver table Cotizaciones'),
                       ('ver_reporte_cotizaciones_excel', 'Puede ver Reporte de Cotizaciones en excel'),
                       ('puede_hacer_transferencia_cotizacion', 'Puede hacer transferencia de Cotización'),)

    def save(self, *args, **kwargs):
        if self.code == '':
            year = self.date.year
            previous_movement = Quotation.objects.filter(date__year=year).aggregate(Max('code'))
            previous_id = previous_movement['code__max']
            if previous_id is None:
                aux = 1
            else:
                aux = int(previous_id[-6:]) + 1
            correlativo = str(aux).zfill(6)
            self.code = 'CO' + str(year) + correlativo
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

    def set_status_purchased(self):
        caso = classify(self.purchased_quantity, self.quantity)
        if caso == EMPTY:
            status = QuotationDetail.STATUS.PEND
        elif caso == PARTIAL:
            status = QuotationDetail.STATUS.ELEG_PARC
        else:
            status = QuotationDetail.STATUS.ELEG
        self.status = status
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

    def previous(self):
        previous = PurchaseOrder.objects.previous(self)
        return previous.pk

    def next(self):
        following = PurchaseOrder.objects.next(self)
        return following.pk

    def delete_reference(self):
        quotation = self.quotation
        requirement = quotation.requirement
        details = PurchaseOrderDetail.objects.filter(order=self)
        for detail in details:
            quotation_detail = detail.quotation_detail
            quotation_detail.purchased_quantity = quotation_detail.purchased_quantity - detail.quantity
            quotation_detail.set_status_purchased()
            quotation_detail.save()
            requirement_detail = quotation_detail.requirement_detail
            requirement_detail.purchased_quantity = requirement_detail.purchased_quantity - detail.quantity
            requirement_detail.set_status_purchased()
            requirement_detail.save()
        quotation.set_status_purchased()
        requirement.set_status_purchased()
        quotation.save()

    def set_status(self):
        total = 0
        total_received = 0
        for detail in PurchaseOrderDetail.objects.filter(order=self):
            total = total + detail.quantity
            total_received = total_received + detail.received_quantity
        caso = classify(total_received, total)
        if caso == EMPTY:
            status = PurchaseOrder.STATUS.PEND
        elif caso == PARTIAL:
            status = PurchaseOrder.STATUS.ING_PARC
        else:
            status = PurchaseOrder.STATUS.ING
        self.status = status
        return self.status

    @property
    def total(self):
        total = self.subtotal + self.tax
        return total

    @property
    def tax(self):
        """Se memoriza: `total` y `total_in_words` la encadenan, y las plantillas
        las invocan mas de una vez en la misma page.

        No se convierte en agregado SQL a proposito: suma una propiedad que
        redondea fila a row, y SUM(...) redondearia una sola vez al final, lo
        que cambia los last_records decimales del importe.
        """
        if not hasattr(self, '_calculated_tax'):
            imp = 0
            for detail in self.details.all():
                imp = imp + detail.tax
            self._calculated_tax = imp
        return self._calculated_tax

    @property
    def subtotal(self):
        if not hasattr(self, '_calculated_subtotal'):
            subtotal = 0
            for detail in self.details.all():
                subtotal = subtotal + detail.amount_without_tax
            self._calculated_subtotal = subtotal
        return self._calculated_subtotal

    @property
    def total_in_words(self):
        letras = to_word(self.total).upper()
        return letras

    class Meta:
        permissions = (('ver_bienvenida', 'Puede ver bienvenida a la aplicación'),
                       ('ver_detalle_orden_compra', 'Puede ver detalle de Orden de Compra'),
                       ('ver_tabla_ordenes_compra', 'Puede ver table Ordenes de Compra'),
                       ('ver_reporte_ordenes_compra_excel', 'Puede ver Reporte de Ordenes de Compra en excel'),
                       ('puede_hacer_transferencia_orden_compra', 'Puede hacer transferencia de Orden de Compra'),)
        ordering = ('code',)

    def save(self, *args, **kwargs):
        if self.code == '':
            year = self.date.year
            previous_movement = PurchaseOrder.objects.filter(date__year=year).aggregate(Max('code'))
            previous_id = previous_movement['code__max']
            if previous_id is None:
                aux = 1
            else:
                aux = int(previous_id[-6:]) + 1
            correlativo = str(aux).zfill(6)
            self.code = 'OC' + str(year) + correlativo
        super(PurchaseOrder, self).save()

    def __str__(self):
        return self.code


class PurchaseOrderDetail(TimeStampedModel):
    objects = OrderDetailManager()
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
    def price_with_tax(self):
        if self.order.with_tax:
            price_with_tax = self.price
        else:
            tax_amount = configuration().purchase_tax.amount
            price_with_tax = round(self.price * (tax_amount + 1), 5)
        return price_with_tax

    @property
    def price_without_tax(self):
        if self.order.with_tax:
            tax_amount = configuration().purchase_tax.amount
            price_without_tax = round(self.price / (tax_amount + 1), 5)
        else:
            price_without_tax = self.price
        return price_without_tax

    @property
    def amount_without_tax(self):
        if self.order.with_tax:
            tax_amount = configuration().purchase_tax.amount
            amount_without_tax = (self.price * self.quantity) / (tax_amount + 1)
        else:
            amount_without_tax = self.price * self.quantity
        return round(amount_without_tax, 5)

    @property
    def amount_with_tax(self):
        if self.order.with_tax:
            amount_with_tax = self.price * self.quantity
        else:
            tax_amount = configuration().purchase_tax.amount
            amount_with_tax = (self.price * self.quantity) * (tax_amount + 1)
        return round(amount_with_tax, 5)

    @property
    def tax(self):
        tax_amount = configuration().purchase_tax.amount
        if self.order.with_tax:
            imp = self.price * self.quantity - (self.price * self.quantity) / (tax_amount + 1)
        else:
            imp = self.price * self.quantity * tax_amount
        return round(imp, 5)

    def set_status(self):
        caso = classify(self.received_quantity, self.quantity)
        if caso == EMPTY:
            status = PurchaseOrderDetail.STATUS.PEND
        elif caso == PARTIAL:
            status = PurchaseOrderDetail.STATUS.ING_PARC
        else:
            status = PurchaseOrderDetail.STATUS.ING
        self.status = status
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
        if not hasattr(self, '_calculated_subtotal'):
            self._calculated_subtotal = sum(detail.amount
                                           for detail in self.details.all())
        return self._calculated_subtotal

    @property
    def tax(self):
        return 0

    @property
    def total(self):
        total = self.subtotal
        return total

    @property
    def total_in_words(self):
        letras = to_word(self.total).upper()
        return letras

    def previous(self):
        previous = ServiceOrder.objects.previous(self)
        return previous.pk

    def next(self):
        following = ServiceOrder.objects.next(self)
        return following.pk

    def delete_reference(self):
        quotation = self.quotation
        requirement = self.quotation
        details = ServiceOrderDetail.objects.filter(order=self)
        for detail in details:
            quotation_detail = detail.quotation_detail
            quotation_detail.purchased_quantity = quotation_detail.purchased_quantity - detail.quantity
            quotation_detail.set_status_purchased()
            quotation_detail.save()
            requirement_detail = quotation_detail.requirement_detail
            requirement_detail.purchased_quantity = requirement_detail.purchased_quantity - detail.quantity
            requirement_detail.set_status_purchased()
            requirement_detail.save()
        quotation.set_status_purchased()
        requirement.set_status_purchased()
        quotation.save()

    def set_status(self):
        total = 0
        total_conformed = 0
        for detail in ServiceOrderDetail.objects.filter(order=self):
            total = total + detail.quantity
            total_conformed = total_conformed + detail.conformed_quantity
        caso = classify(total_conformed, total)
        if caso == EMPTY:
            status = ServiceOrder.STATUS.PEND
        elif caso == PARTIAL:
            status = ServiceOrder.STATUS.CONF_PARC
        else:
            status = ServiceOrder.STATUS.CONF
        self.status = status
        return self.status

    class Meta:
        permissions = (('ver_detalle_orden_servicios', 'Puede ver detalle de Orden de Servicios'),
                       ('ver_tabla_ordenes_servicios', 'Puede ver tabla de Ordenes de Servicios'),
                       ('ver_reporte_ordenes_servicios_excel', 'Puede ver Reporte de Ordenes de Servicios en excel'),)
        ordering = ('code',)

    def generate_code(self):
        year = self.date.year
        previous_movement = ServiceOrder.objects.filter(date__year=year).aggregate(Max('code'))
        previous_id = previous_movement['code__max']
        if previous_id is None:
            aux = 1
        else:
            aux = int(previous_id[-6:]) + 1
        correlativo = str(aux).zfill(6)
        code = 'OS' + str(year) + correlativo
        return code

    def save(self, *args, **kwargs):
        if self.code == '':
            self.code = self.generate_code()
        super(ServiceOrder, self).save()

    def __str__(self):
        return self.code


class ServiceOrderDetail(TimeStampedModel):
    objects = OrderDetailManager()
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
    def tax(self):
        return 0

    class Meta:
        permissions = (('ver_detalle_orden_servicios', 'Puede ver Detalle Orden de Servicios'),)
        ordering = ['line_number']

    def set_status_served(self):
        caso = classify(self.conformed_quantity, self.quantity)
        if caso == EMPTY:
            status = ServiceOrderDetail.STATUS.PEND
        elif caso == PARTIAL:
            status = ServiceOrderDetail.STATUS.CONF_PARC
        else:
            status = ServiceOrderDetail.STATUS.CONF
        self.status = status
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

    def previous(self):
        previous = ServiceConformity.objects.previous(self)
        return previous.pk

    def next(self):
        following = ServiceConformity.objects.next(self)
        return following.pk

    def delete_reference(self):
        order = self.service_order
        quotation = order.quotation
        requirement = quotation.requirement
        details = ServiceConformityDetail.objects.filter(conformity=self)
        for detail in details:
            order_detail = detail.service_order_detail
            order_detail.conformed_quantity = order_detail.conformed_quantity - detail.quantity
            order_detail.set_status_served()
            order_detail.save()
            requirement_detail = order_detail.quotation_detail.requirement_detail
            requirement_detail.served_quantity = requirement_detail.served_quantity - detail.quantity
            requirement_detail.set_status_served()
            requirement_detail.save()
        order.set_status()
        order.save()
        requirement.set_status_served()
        requirement.save()

    def save(self, *args, **kwargs):
        if self.code == '':
            year = self.date.year
            previous_conformity = ServiceConformity.objects.filter(date__year=year).aggregate(Max('code'))
            previous_id = previous_conformity['code__max']
            if previous_id is None:
                aux = 1
            else:
                aux = int(previous_id[-6:]) + 1
            correlativo = str(aux).zfill(6)
            self.code = 'CS' + str(year) + correlativo
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
