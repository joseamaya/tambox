# -*- coding: utf-8 -*-
import os
from django.conf import settings
from django.db import models
from django.utils.encoding import smart_str, python_2_unicode_compatible
from model_utils.models import TimeStampedModel
from django.core.files.storage import FileSystemStorage
from model_utils.choices import Choices
from django.utils.translation import gettext as _
from administracion.models import Oficina

class OverwriteStorage(FileSystemStorage):
    
    def get_available_name(self, name):
        if self.exists(name):
            os.remove(os.path.join(settings.MEDIA_ROOT, name))
        return name
    
class SingletonModel(models.Model):
    
    class Meta:
        abstract = True
    
    def save(self, *args, **kwargs):
        self.pk = 1
        super(SingletonModel, self).save(*args, **kwargs)
        
    def delete(self, *args, **kwargs):
        pass
    
    @classmethod
    def load(cls):
        obj, created = cls.objects.get_or_create(pk=1)
        return obj
    
class CuentaContable(TimeStampedModel):
    cuenta = models.CharField(unique=True,max_length=12)
    descripcion = models.CharField(max_length=150)
    depreciacion = models.DecimalField(max_digits=18, decimal_places=2,default=0)
    divisionaria = models.BooleanField(default=False)
    estado = models.BooleanField(default = True)
    
    class Meta:
        permissions = (('cargar_cuentas_contables', 'Puede cargar Cuentas Contables desde un archivo externo'),
                       ('ver_detalle_cuenta_contable', 'Puede ver detalle de Cuenta Contable'),
                       ('ver_tabla_cuentas_contables', 'Puede ver tabla de Cuentas Contables'),
                       ('ver_reporte_cuentas_contables_excel', 'Puede ver Reporte Cuentas Contables en excel'),)
        ordering = ['cuenta']
        
    def anterior(self):
        try:
            sig = CuentaContable.objects.filter(pk__lt=self.pk).order_by('-pk')[0]
        except:
            sig = CuentaContable.objects.all().last()            
        return sig.pk
    
    def siguiente(self):
        try:
            ant = CuentaContable.objects.filter(pk__gt=self.pk).order_by('pk')[0]            
        except:
            ant = CuentaContable.objects.all().first()            
        return ant.pk
    
    def __str__(self):
        return smart_str(self.cuenta)
    
class FormaPago(TimeStampedModel):
    codigo = models.CharField(unique=True, max_length=5)
    descripcion = models.CharField(max_length=50)
    dias_credito = models.IntegerField()
    estado = models.BooleanField(default=True)
    
    class Meta:
        permissions = (('cargar_formas_pago', 'Puede cargar Formas de Pago desde un archivo externo'),
                       ('ver_detalle_forma_pago', 'Puede ver detalle de Forma de Pago'),
                       ('ver_tabla_formas_pago', 'Puede ver tabla Formas de Pago'),
                       ('ver_reporte_formas_pago_excel', 'Puede ver Reporte de Formas de Pago en excel'),)
    
    def anterior(self):
        try:
            sig = FormaPago.objects.filter(pk__lt=self.pk).order_by('-pk')[0]
        except:
            sig = FormaPago.objects.all().last()            
        return sig.pk
    
    def siguiente(self):
        try:
            ant = FormaPago.objects.filter(pk__gt=self.pk).order_by('pk')[0]            
        except:
            ant = FormaPago.objects.all().first()            
        return ant.pk
    
    def __str__(self):
        return smart_str(self.descripcion)

class TipoDocumento(TimeStampedModel):
    codigo_sunat = models.CharField(max_length=10)
    nombre = models.CharField(max_length=100)
    descripcion = models.CharField(max_length=100)
    estado = models.BooleanField(default = True)
    
    class Meta:
        permissions = (('cargar_tipos_documento', 'Puede cargar Tipos de Documento desde un archivo externo'),
                       ('ver_detalle_tipo_documento', 'Puede ver detalle Tipo de Documento'),
                       ('ver_tabla_tipos_documentos', 'Puede ver tabla de Tipos de Documentos'),
                       ('ver_reporte_tipos_documentos_excel', 'Puede ver Reporte de Tipos de Documentos en excel'),)
        ordering = ['codigo_sunat']

    def anterior(self):
        try:
            sig = TipoDocumento.objects.filter(pk__lt=self.pk).order_by('-pk')[0]
        except:
            sig = TipoDocumento.objects.all().last()            
        return sig.pk
    
    def siguiente(self):
        try:
            ant = TipoDocumento.objects.filter(pk__gt=self.pk).order_by('pk')[0]            
        except:
            ant = TipoDocumento.objects.all().first()            
        return ant.pk

    def __str__(self):
        return self.nombre
    
class Tipo(TimeStampedModel):
    tabla = models.CharField(max_length=25)
    descripcion_campo = models.CharField(max_length=25)
    codigo = models.CharField(max_length=10)
    descripcion_valor = models.CharField(max_length=100)
    cantidad = models.DecimalField(max_digits=14, decimal_places=2, blank=True, null=True)
    
    class Meta:
        permissions = (('ver_detalle_tipo', 'Puede ver detalle Tipo de Documento'),
                       ('ver_tabla_tipos', 'Puede ver tabla de Tipos de Documentos'),
                       ('ver_reporte_tipos_excel', 'Puede ver Reporte de Tipos de Documentos en excel'),)
        ordering = ['codigo']

    def __str__(self):
        return self.descripcion_valor
    
class Impuesto(TimeStampedModel):
    abreviatura =  models.CharField(max_length=10)
    descripcion = models.CharField(max_length=50)
    monto = models.DecimalField(max_digits=14, decimal_places=2)
    fecha_inicio = models.DateField()
    fecha_fin = models.DateField(null=True)
    estado = models.BooleanField(default=True)
    STATUS = Choices(('COM', _('COMPRA')),
                     ('VEN', _('VEN')),
                     )
    tipo_uso = models.CharField(choices=STATUS, default=STATUS.COM, max_length=20)
    
    class Meta:
        permissions = (('ver_detalle_impuesto', 'Puede ver detalle Impuesto'),
                       ('ver_tabla_impuestos', 'Puede ver tabla de Impuestos'),
                       ('ver_reporte_impuestos_excel', 'Puede ver Reporte de Impuestos en excel'),)
        ordering = ['abreviatura']
        
    def anterior(self):
        try:
            sig = Impuesto.objects.filter(pk__lt=self.pk).order_by('-pk')[0]
        except:
            sig = Impuesto.objects.all().last()            
        return sig.pk
    
    def siguiente(self):
        try:
            ant = Impuesto.objects.filter(pk__gt=self.pk).order_by('pk')[0]            
        except:
            ant = Impuesto.objects.all().first()            
        return ant.pk

    def __str__(self):
        return self.descripcion
    
class Upload(TimeStampedModel):
    archivo = models.FileField(upload_to='archivos', storage=OverwriteStorage())
    
@python_2_unicode_compatible
class Empresa(SingletonModel):
    razon_social = models.CharField(max_length=150)
    ruc = models.CharField(max_length=11)
    logo = models.ImageField(upload_to='configuracion')
    lugar = models.CharField(max_length=150,default='')
    calle = models.CharField(max_length=150,default='')
    distrito = models.CharField(max_length=100)
    provincia = models.CharField(max_length=100)
    departamento = models.CharField(max_length=100)
    
    def __str__(self):
        return u'%s' % self.razon_social
    
class Configuracion(TimeStampedModel):
    impuesto_compra = models.ForeignKey(Impuesto)
    administracion = models.ForeignKey(Oficina, related_name = 'administracion',null=True)
    presupuesto = models.ForeignKey(Oficina, related_name = 'presupuesto',null=True)
    logistica = models.ForeignKey(Oficina, related_name = 'logistica',null=True)