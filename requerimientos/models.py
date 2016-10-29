# -*- coding: utf-8 -*-
from django.db import models
from django.db.models import Max
from model_utils.models import TimeStampedModel
from model_utils import Choices
from django.utils.translation import gettext as _
from administracion.models import Trabajador, Oficina
from productos.models import Producto
from requerimientos.querysets import NavegableQuerySet, RequerimientoQuerySet

# Create your models here.
class Requerimiento(TimeStampedModel):
    codigo = models.CharField(primary_key=True,max_length=12)
    solicitante = models.ForeignKey(Trabajador)
    oficina = models.ForeignKey(Oficina)
    motivo = models.CharField(max_length=100)
    MESES = Choices((1, _('ENERO')),
                     (2, _('FEBRERO')),
                     (3, _('MARZO')),
                     (4, _('ABRIL')),
                     (5, _('MAYO')),
                     (6, _('JUNIO')),
                     (7, _('JULIO')),
                     (8, _('AGOSTO')),
                     (9, _('SETIEMBRE')),
                     (10, _('OCTUBRE')),
                     (11, _('NOVIEMBRE')),
                     (12, _('DICIEMBRE')),
                     )
    mes = models.IntegerField(choices=MESES)
    observaciones = models.TextField()
    informe = models.FileField(upload_to='informes', null=True)
    entrega_directa_solicitante = models.BooleanField(default=False)
    STATUS = Choices(('PEND', _('PENDIENTE')),
                     ('COTIZ', _('COTIZADO')),
                     ('COTIZ_PARC', _('COTIZADO PARCIALMENTE')),
                     ('PED', _('PEDIDO')),
                     ('PED_PARC', _('PEDIDO PARCIALMENTE')),
                     ('ATEN', _('ATENDIDO')),
                     ('ATEN_PARC', _('ATENDIDO PARCIALMENTE')),
                     ('CANC', _('CANCELADO')),
                     )
    estado = models.CharField(choices=STATUS, default=STATUS.PEND, max_length=20)
    objects = RequerimientoQuerySet.as_manager()
    
    class Meta:
        permissions = (('ver_bienvenida', 'Puede ver bienvenida a la aplicación'),
                       ('ver_detalle_requerimiento', 'Puede ver detalle de Requerimiento'),
                       ('ver_tabla_requerimientos', 'Puede ver tabla de Requerimientos'),
                       ('ver_reporte_requerimientos_excel', 'Puede ver Reporte de Requerimientos en excel'),
                       ('puede_hacer_transferencia_requerimiento', 'Puede hacer transferencia de Requerimiento'),)
    
    def anterior(self):
        ant = Requerimiento.objects.anterior(self)
        return ant.pk
    
    def siguiente(self):
        sig = Requerimiento.objects.siguiente(self)            
        return sig.pk
    
    def __str__(self):
        return self.codigo
    
    def establecer_estado_cotizado(self):
        estado_requerimiento = Requerimiento.STATUS.COTIZ
        detalles_requerimiento = DetalleRequerimiento.objects.filter(requerimiento = self)
        for detalle in detalles_requerimiento:
            if detalle.estado == DetalleRequerimiento.STATUS.COTIZ_PARC or detalle.estado == DetalleRequerimiento.STATUS.PEND:
                estado_requerimiento = Requerimiento.STATUS.COTIZ_PARC
                break
        self.estado = estado_requerimiento
        self.save()
    
    def establecer_estado(self):
        estado_requerimiento = Requerimiento.STATUS.PED
        detalles_requerimiento = DetalleRequerimiento.objects.filter(requerimiento = self)
        for detalle in detalles_requerimiento:
            if detalle.estado == DetalleRequerimiento.STATUS.PED_PARC or detalle.estado == DetalleRequerimiento.STATUS.COTIZ:
                estado_requerimiento = Requerimiento.STATUS.PED_PARC
                break
        self.estado = estado_requerimiento
        self.save()
        
    def establecer_estado_atendido(self):
        estado_requerimiento = Requerimiento.STATUS.ATEN
        detalles_requerimiento = DetalleRequerimiento.objects.filter(requerimiento = self)
        for detalle in detalles_requerimiento:
            if detalle.estado == DetalleRequerimiento.STATUS.ATEN_PARC or detalle.estado == DetalleRequerimiento.STATUS.PED or detalle.estado == DetalleRequerimiento.STATUS.PED_PARC:
                estado_requerimiento = Requerimiento.STATUS.ATEN_PARC
                break
        self.estado = estado_requerimiento
        self.save()
        
    def generar_codigo(self):
        anio = self.created.year
        req_ant = Requerimiento.objects.requerimiento_anterior(anio)
        id_ant=req_ant['codigo__max']        
        if id_ant is None:
            aux = 1            
        else:
            aux=int(id_ant[-6:])+1
        correlativo = str(aux).zfill(6)
        codigo = 'RQ'+str(anio)+correlativo
        return codigo    
    
    def save(self, *args, **kwargs):
        if self.codigo == '':
            self.codigo = self.generar_codigo()                        
            super(Requerimiento, self).save()
            AprobacionRequerimiento.objects.create(requerimiento = self)
        else:
            super(Requerimiento, self).save()
            
class DetalleRequerimiento(TimeStampedModel):
    nro_detalle = models.IntegerField()
    requerimiento = models.ForeignKey(Requerimiento)
    producto = models.ForeignKey(Producto, null=True)    
    otro = models.CharField(max_length=150, null=True)
    unidad = models.CharField(max_length=20, null=True)
    uso = models.CharField(max_length=50,null=True)
    cantidad = models.DecimalField(max_digits=15, decimal_places=5)
    cantidad_comprada = models.DecimalField(max_digits=15, decimal_places=5,default=0)
    cantidad_atendida = models.DecimalField(max_digits=15, decimal_places=5,default=0)
    STATUS = Choices(('PEND', _('PENDIENTE')),
                     ('COTIZ', _('COTIZADO')),
                     ('COTIZ_PARC', _('COTIZADO PARCIALMENTE')),
                     ('PED', _('PEDIDO')),
                     ('PED_PARC', _('PEDIDO PARCIALMENTE')),
                     ('ATEN', _('ATENDIDO')),
                     ('ATEN_PARC', _('ATENDIDO PARCIALMENTE')),
                     ('CANC', _('CANCELADO')),
                     )
    estado = models.CharField(choices=STATUS, default=STATUS.PEND, max_length=20)
    
    class Meta:
        permissions = (('can_view', 'Can view Detalle Requerimiento'),)
        ordering = ['nro_detalle']
        
    def __str__(self):
        return self.requerimiento.codigo+ ' ' + str(self.nro_detalle)
    
    def establecer_estado(self):
        if self.cantidad_comprada >= self.cantidad:
            self.estado = DetalleRequerimiento.STATUS.PED            
        elif self.cantidad_comprada < self.cantidad:
            self.estado = DetalleRequerimiento.STATUS.PED_PARC                
        self.save()
        
    def establecer_estado_atendido(self):
        if self.cantidad_atendida >= self.cantidad:
            self.estado = DetalleRequerimiento.STATUS.ATEN            
        elif self.cantidad_atendida < self.cantidad:
            self.estado = DetalleRequerimiento.STATUS.ATEN_PARC                
        self.save()
    
class AprobacionRequerimiento(TimeStampedModel):
    requerimiento = models.OneToOneField(Requerimiento,primary_key=True)
    STATUS = Choices(('PEND', _('PENDIENTE')),
                     ('APROB_JEF', _('APROBADO JEFATURA')),
                     ('DESAP_JEF', _('DESAPROBADO JEFATURA')),
                     ('APROB_GER_INM', _('APROBADO GERENCIA INMEDIATA')),
                     ('DESAP_GER_INM', _('DESAPROBADO GERENCIA INMEDIATA')),
                     ('APROB_GER_ADM', _('APROBADO GERENCIA ADMINISTRACION')),
                     ('DESAP_GER_ADM', _('DESAPROBADO GERENCIA ADMINISTRACION')),
                     ('APROB_LOG', _('APROBADO LOGISTICA')),
                     ('DESAP_LOG', _('DESAPROBADO LOGISTICA')),
                     ('APROB_PRES', _('APROBADO PRESUPUESTO')),
                     ('DESAP_PRES', _('DESAPROBADO PRESUPUESTO')),)
    estado = models.CharField(choices=STATUS, default=STATUS.PEND, max_length=20)
    motivo_desaprobacion = models.TextField(default='')
    
    class Meta:
        permissions = (('ver_tabla_aprobacion_requerimientos', 'Puede ver tabla de Aprobación de Requerimientos'),
                       ('ver_reporte_aprobacion_requerimientos_excel', 'Puede ver Reporte de Aprobación de Requerimientos en excel'),)

    def __str__(self):
        return self.pk