# -*- coding: utf-8 -*-
from django.db import models
from model_utils.models import TimeStampedModel
from administracion.models import Trabajador, Oficina
from productos.models import Producto
from requerimientos.querysets import RequerimientoQuerySet, AprobacionRequerimientoQuerySet
from django.core.validators import MaxValueValidator
from datetime import date
from requerimientos.settings import CHOICES_MESES, CHOICES_ESTADO_REQ,\
    CHOICES_ESTADO_APROB_REQ, OFICINA_ADMINISTRACION, PRESUPUESTO, LOGISTICA

class Requerimiento(TimeStampedModel):
    codigo = models.CharField(primary_key=True,max_length=12)
    solicitante = models.ForeignKey(Trabajador)
    oficina = models.ForeignKey(Oficina)
    motivo = models.CharField(max_length=100, blank = True)    
    fecha = models.DateField()
    mes = models.IntegerField(choices=CHOICES_MESES)
    annio = models.PositiveIntegerField(validators=[MaxValueValidator(9999)])
    observaciones = models.TextField()
    informe = models.FileField(upload_to='informes', null=True)
    entrega_directa_solicitante = models.BooleanField(default=False)
    STATUS = CHOICES_ESTADO_REQ
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
        return ant
    
    def siguiente(self):
        sig = Requerimiento.objects.siguiente(self)            
        return sig
    
    def __str__(self):
        return self.codigo
    
    def establecer_estado_cotizado(self):
        estado_requerimiento = Requerimiento.STATUS.COTIZ
        detalles_requerimiento = DetalleRequerimiento.objects.filter(requerimiento = self)
        for detalle in detalles_requerimiento:
            if (detalle.estado == DetalleRequerimiento.STATUS.COTIZ_PARC or 
                detalle.estado == DetalleRequerimiento.STATUS.PEND):                
                estado_requerimiento = Requerimiento.STATUS.COTIZ_PARC
                break
        self.estado = estado_requerimiento        
    
    def establecer_estado_comprado(self):
        estado_requerimiento = Requerimiento.STATUS.COMP
        detalles_requerimiento = DetalleRequerimiento.objects.filter(requerimiento = self)
        for detalle in detalles_requerimiento:
            if detalle.estado == DetalleRequerimiento.STATUS.COMP_PARC or detalle.estado == DetalleRequerimiento.STATUS.COTIZ:
                estado_requerimiento = Requerimiento.STATUS.COMP_PARC
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
    
    def verificar_acceso(self, usuario, oficina_administracion, logistica, presupuesto):
        solicitante = self.solicitante
        trabajador = usuario.trabajador
        puesto_usuario = trabajador.puesto
        oficina_usuario = puesto_usuario.oficina
        if (solicitante == trabajador 
            or (oficina_usuario == self.oficina and puesto_usuario.es_jefatura) 
            or ((oficina_usuario == self.oficina.gerencia
                 or oficina_usuario == oficina_administracion
                 or oficina_usuario == logistica
                 or oficina_usuario == presupuesto) and puesto_usuario.es_jefatura)):
            return True
        else:
            return False
        
    @staticmethod
    def obtener_requerimientos_visibles(self, usuario):
        trabajador = usuario.trabajador
        puesto_usuario = trabajador.puesto
        oficina_usuario = puesto_usuario.oficina
        if (((oficina_usuario == OFICINA_ADMINISTRACION or oficina_usuario == PRESUPUESTO) and puesto_usuario.es_jefatura) or 
            oficina_usuario == LOGISTICA and (puesto_usuario.es_jefatura or puesto_usuario.es_asistente)):
            queryset = Requerimiento.objects.all()
        elif puesto_usuario.es_jefatura: 
            queryset = Requerimiento.objects.requerimientos_oficina_usuario(oficina_usuario)        
        else:
            queryset = Requerimiento.objects.requerimientos_activos_por_usuario(usuario,Requerimiento.STATUS.CANC)
        return queryset
    
        """elif oficina_usuario == self.oficina.gerencia and puesto_usuario.es_jefatura:
            queryset = Requerimiento.objects.requerimientos_gerencia_usuario(oficina_usuario)"""
    
    def save(self, *args, **kwargs):
        if self.codigo == '':
            self.codigo = self.generar_codigo()
            puesto = self.solicitante.puesto
            self.oficina = puesto.oficina
            AprobacionRequerimiento.objects.create(requerimiento = self)
        super(Requerimiento, self).save()
            
class DetalleRequerimiento(TimeStampedModel):
    nro_detalle = models.IntegerField()
    requerimiento = models.ForeignKey(Requerimiento)
    producto = models.ForeignKey(Producto, null=True)    
    uso = models.TextField(null=True)
    cantidad = models.DecimalField(max_digits=15, decimal_places=5)
    cantidad_cotizada = models.DecimalField(max_digits=15, decimal_places=5,default=0)
    cantidad_comprada = models.DecimalField(max_digits=15, decimal_places=5,default=0)
    cantidad_atendida = models.DecimalField(max_digits=15, decimal_places=5,default=0)
    STATUS = CHOICES_ESTADO_REQ
    estado = models.CharField(choices=STATUS, default=STATUS.PEND, max_length=20)
    
    class Meta:
        permissions = (('can_view', 'Can view Detalle Requerimiento'),)
        ordering = ['nro_detalle']
        
    def __str__(self):
        return self.requerimiento.codigo+ ' ' + str(self.nro_detalle)
    
    def establecer_estado_cotizado(self):
        if self.cantidad_cotizada == 0:
            estado = DetalleRequerimiento.STATUS.PEND
        elif self.cantidad_cotizada >= self.cantidad:
            estado = DetalleRequerimiento.STATUS.COTIZ
        elif self.cantidad_cotizada < self.cantidad:
            estado = DetalleRequerimiento.STATUS.COTIZ_PARC                
        self.estado = estado
    
    def establecer_estado_comprado(self):
        if self.cantidad_comprada == 0:
            estado = self.establecer_estado_cotizado()
        elif self.cantidad_comprada >= self.cantidad:
            estado = DetalleRequerimiento.STATUS.COMP
        elif self.cantidad_comprada < self.cantidad:
            estado = DetalleRequerimiento.STATUS.COMP_PARC                
        self.estado = estado
        
    def establecer_estado_atendido(self):
        if self.cantidad_atendida == 0:
            estado = self.establecer_estado_comprado()
        elif self.cantidad_atendida >= self.cantidad:
            estado = DetalleRequerimiento.STATUS.ATEN            
        elif self.cantidad_atendida < self.cantidad:
            estado = DetalleRequerimiento.STATUS.ATEN_PARC                
        self.estado = estado
        
    #def save(self, *args, **kwargs):
        
    
class AprobacionRequerimiento(TimeStampedModel):
    requerimiento = models.OneToOneField(Requerimiento,primary_key=True)
    STATUS = CHOICES_ESTADO_APROB_REQ
    estado = models.CharField(choices=STATUS, default=STATUS.PEND, max_length=20)
    motivo_desaprobacion = models.TextField(default='')
    fecha_recepcion = models.DateField(null=True)
    objects = AprobacionRequerimientoQuerySet.as_manager()
    
    class Meta:
        permissions = (('ver_tabla_aprobacion_requerimientos', 'Puede ver tabla de Aprobación de Requerimientos'),
                       ('ver_reporte_aprobacion_requerimientos_excel', 'Puede ver Reporte de Aprobación de Requerimientos en excel'),)

    def __str__(self):
        return self.pk
    
    def verificar_acceso_aprobacion(self, usuario):
        puesto_usuario = usuario.trabajador.puesto
        oficina_usuario = puesto_usuario.oficina
        oficina_requerimiento = self.requerimiento.oficina        
        if (self.verificar_estado_aprobacion(puesto_usuario,
                                             oficina_usuario,
                                             LOGISTICA,
                                             AprobacionRequerimiento.STATUS.APROB_LOG,
                                             AprobacionRequerimiento.STATUS.DESAP_LOG,
                                             AprobacionRequerimiento.STATUS.PEND)):
            return True
        else:
            return False
    
    def verificar_estado_aprobacion(self, puesto_usuario, oficina_usuario, oficina, aprob_actual,desap_actual=True,aprob_anterior=True,):        
        if oficina_usuario==oficina and puesto_usuario.es_jefatura:
            if (self.estado==aprob_anterior or self.estado==aprob_actual or self.estado==desap_actual):
                return True
            else:
                return False
        else:
            return False
        
    def obtener_oficina_aprobacion_superior(self, estado):
        if estado==AprobacionRequerimiento.STATUS.APROB_PRES:
            oficina = LOGISTICA            
        elif estado==AprobacionRequerimiento.STATUS.APROB_GER_ADM:
            oficina = PRESUPUESTO
        elif estado==AprobacionRequerimiento.STATUS.APROB_GER_INM:
            oficina = OFICINA_ADMINISTRACION                
        elif estado==AprobacionRequerimiento.STATUS.APROB_JEF:
            oficina = self.requerimiento.oficina.gerencia
        else:
            oficina = None
        return oficina
    
    @staticmethod
    def obtener_aprobaciones_pendientes(usuario):        
        puesto_usuario = usuario.trabajador.puesto
        oficina_usuario =  puesto_usuario.oficina
        if oficina_usuario == LOGISTICA and puesto_usuario.es_jefatura:
            queryset = AprobacionRequerimiento.objects.filter(estado = AprobacionRequerimiento.STATUS.PEND)
        else:
            queryset = None
        return queryset
    
    def save(self, *args, **kwargs):
        if self.estado == AprobacionRequerimiento.STATUS.APROB_LOG:
            self.fecha_recepcion = date.today()
        super(AprobacionRequerimiento, self).save()