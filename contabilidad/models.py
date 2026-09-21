# -*- coding: utf-8 -*-
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils.encoding import force_str
from model_utils.models import TimeStampedModel
from model_utils.choices import Choices
from django.utils.translation import gettext as _
from administracion.models import Oficina
from contabilidad.behaviors import SingletonModel
from tambox.querysets import NavegableQuerySet


class TipoCambio(TimeStampedModel):
    amount = models.DecimalField(max_digits=15, decimal_places=5)
    date = models.DateField(unique=True)
    objects = NavegableQuerySet.as_manager()

    class Meta:
        permissions = (('ver_detalle_tipo_cambio', 'Puede ver detalle de Tipo de Cambio'),
                       ('ver_tabla_tipos_cambio', 'Puede ver tabla de Tipos de Cambio'),
                       ('ver_reporte_tipos_cambio_excel', 'Puede ver Reporte Tipos de Cambio en excel'),)
        ordering = ['date']

    def anterior(self):
        ant = TipoCambio.objects.anterior(self)
        return ant.pk

    def siguiente(self):
        sig = TipoCambio.objects.siguiente(self)
        return sig.pk

    def __str__(self):
        return str(self.date)


class CuentaContable(TimeStampedModel):
    account_number = models.CharField(unique=True, max_length=12)
    description = models.CharField(max_length=150)
    depreciation = models.DecimalField(max_digits=18, decimal_places=2, default=0)
    is_divisional = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    objects = NavegableQuerySet.as_manager()

    class Meta:
        permissions = (('cargar_cuentas_contables', 'Puede cargar Cuentas Contables desde un archivo externo'),
                       ('ver_detalle_cuenta_contable', 'Puede ver detalle de Cuenta Contable'),
                       ('ver_tabla_cuentas_contables', 'Puede ver tabla de Cuentas Contables'),
                       ('ver_reporte_cuentas_contables_excel', 'Puede ver Reporte Cuentas Contables en excel'),)
        ordering = ['account_number']

    def anterior(self):
        ant = CuentaContable.objects.anterior(self)
        return ant.pk

    def siguiente(self):
        sig = CuentaContable.objects.siguiente(self)
        return sig.pk

    def __str__(self):
        return force_str(self.account_number)


class FormaPago(TimeStampedModel):
    code = models.CharField(unique=True, max_length=5)
    description = models.CharField(max_length=50)
    credit_days = models.IntegerField()
    is_active = models.BooleanField(default=True)
    objects = NavegableQuerySet.as_manager()

    class Meta:
        permissions = (('cargar_formas_pago', 'Puede cargar Formas de Pago desde un archivo externo'),
                       ('ver_detalle_forma_pago', 'Puede ver detalle de Forma de Pago'),
                       ('ver_tabla_formas_pago', 'Puede ver tabla Formas de Pago'),
                       ('ver_reporte_formas_pago_excel', 'Puede ver Reporte de Formas de Pago en excel'),)

    def anterior(self):
        ant = FormaPago.objects.anterior(self)
        return ant.pk

    def siguiente(self):
        sig = FormaPago.objects.siguiente(self)
        return sig.pk

    def __str__(self):
        return force_str(self.description)


class TipoDocumento(TimeStampedModel):
    sunat_code = models.CharField(max_length=10)
    name = models.CharField(max_length=100)
    description = models.CharField(max_length=100)
    is_active = models.BooleanField(default=True)
    objects = NavegableQuerySet.as_manager()

    class Meta:
        permissions = (('cargar_tipos_documento', 'Puede cargar Tipos de Documento desde un archivo externo'),
                       ('ver_detalle_tipo_documento', 'Puede ver detalle Tipo de Documento'),
                       ('ver_tabla_tipos_documentos', 'Puede ver tabla de Tipos de Documentos'),
                       ('ver_reporte_tipos_documentos_excel', 'Puede ver Reporte de Tipos de Documentos en excel'),)
        ordering = ['sunat_code']

    def anterior(self):
        ant = TipoDocumento.objects.anterior(self)
        return ant.pk

    def siguiente(self):
        sig = TipoDocumento.objects.siguiente(self)
        return sig.pk

    def __str__(self):
        return self.name


class Tipo(TimeStampedModel):
    table = models.CharField(max_length=25)
    field_description = models.CharField(max_length=25)
    code = models.CharField(max_length=10)
    value_description = models.CharField(max_length=100)
    quantity = models.DecimalField(max_digits=14, decimal_places=2, blank=True, null=True)

    class Meta:
        permissions = (('ver_detalle_tipo', 'Puede ver detalle Tipo de Documento'),
                       ('ver_tabla_tipos', 'Puede ver tabla de Tipos de Documentos'),
                       ('ver_reporte_tipos_excel', 'Puede ver Reporte de Tipos de Documentos en excel'),)
        ordering = ['code']

    def __str__(self):
        return self.value_description


class Impuesto(TimeStampedModel):
    abbreviation = models.CharField(max_length=10)
    description = models.CharField(max_length=50)
    amount = models.DecimalField(max_digits=14, decimal_places=2)
    start_date = models.DateField()
    end_date = models.DateField(null=True)
    is_active = models.BooleanField(default=True)
    STATUS = Choices(('COM', _('COMPRA')),
                     ('VEN', _('VEN')),
                     )
    usage_type = models.CharField(choices=STATUS, default=STATUS.COM, max_length=20)
    objects = NavegableQuerySet.as_manager()

    class Meta:
        permissions = (('ver_detalle_impuesto', 'Puede ver detalle Impuesto'),
                       ('ver_tabla_impuestos', 'Puede ver tabla de Impuestos'),
                       ('ver_reporte_impuestos_excel', 'Puede ver Reporte de Impuestos en excel'),)
        ordering = ['abbreviation']

    def anterior(self):
        ant = Impuesto.objects.anterior(self)
        return ant.pk

    def siguiente(self):
        sig = Impuesto.objects.siguiente(self)
        return sig.pk

    def __str__(self):
        return self.description


class Upload(TimeStampedModel):
    file = models.FileField(upload_to='archivos')


class Empresa(SingletonModel):
    business_name = models.CharField(max_length=150)
    tax_id = models.CharField(max_length=11)
    logo = models.ImageField(upload_to='configuracion')
    place = models.CharField(max_length=150, default='')
    street = models.CharField(max_length=150, default='')
    district = models.CharField(max_length=100)
    province = models.CharField(max_length=100)
    department = models.CharField(max_length=100)
    mail_host = models.CharField(max_length=70)
    mail_port = models.IntegerField(default=25)
    username = models.EmailField()
    password = models.CharField(max_length=20)
    uses_tls = models.BooleanField(default=True)

    def __str__(self):
        return u'%s' % self.business_name

    def address(self):
        return self.place + ' ' + self.street + ' ' + self.district

    class Meta:
        verbose_name = 'Empresa'
        verbose_name_plural = 'Empresas'


class Configuracion(TimeStampedModel):
    purchase_tax = models.ForeignKey(Impuesto, on_delete=models.CASCADE, related_name='configurations')
    operaciones = models.ForeignKey(Oficina, on_delete=models.CASCADE, related_name='operaciones', null=True)
    administracion = models.ForeignKey(Oficina, on_delete=models.CASCADE, related_name='administracion', null=True)
    presupuesto = models.ForeignKey(Oficina, on_delete=models.CASCADE, related_name='presupuesto', null=True)
    logistica = models.ForeignKey(Oficina, on_delete=models.CASCADE, related_name='logistica', null=True)


class TipoExistencia(TimeStampedModel):
    sunat_code = models.CharField(primary_key=True, max_length=2)
    description = models.CharField(max_length=50, verbose_name='Descripción')

    def __str__(self):
        return u'%s' % self.description

    class Meta:
        permissions = (('ver_tabla_tipos_existencias', 'Puede ver tabla de Tipos de Existencias'),)
        verbose_name = 'Tipo de Existencia'
        verbose_name_plural = 'Tipos de Existencias'


@receiver(post_save, sender=Configuracion)
@receiver(post_save, sender=Empresa)
def invalidar_cache_configuracion(sender, **kwargs):
    """La configuracion y la empresa se leen con cache; al guardarlas se invalida."""
    from tambox.configuracion import limpiar_cache
    limpiar_cache()
