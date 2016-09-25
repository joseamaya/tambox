# -*- coding: utf-8 -*-
from django.db import models
from contabilidad.models import Configuracion
from django.db.models import Max
from model_utils.models import TimeStampedModel
from model_utils import Choices
from django.utils.translation import gettext as _
from administracion.models import Trabajador, Oficina, Puesto
from django.core.mail.message import EmailMessage
from productos.models import Producto

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
    
    class Meta:
        permissions = (('ver_detalle_requerimiento', 'Puede ver detalle de Requerimiento'),
                       ('ver_tabla_requerimientos', 'Puede ver tabla de Requerimientos'),
                       ('ver_reporte_requerimientos_excel', 'Puede ver Reporte de Requerimientos en excel'),
                       ('puede_hacer_transferencia_requerimiento', 'Puede hacer transferencia de Requerimiento'),)
    
    @property
    def asunto(self):
        return u'Tambox - Requerimiento Pendiente de Aprobar'
    
    @property
    def cuerpo(self):
        texto = u'''Tiene un requerimiento pendiente de aprobar:\n
        Nro: %s \n
        Solicitante: %s \n
        Fecha: %s \n
        Por favor ingrese a Tambox para hacer la aprobación correspondiente.\n
        http://IP/tambox \n
        Saludos. 
        ''' % (self.codigo, self.solicitante.nombre_completo(),self.created.strftime('%d/%m/%Y'))
        return texto

    def anterior(self):
        try:
            sig = Requerimiento.objects.filter(pk__lt=self.pk).order_by('-pk')[0]
        except:
            sig = Requerimiento.objects.all().last()            
        return sig.pk
    
    def siguiente(self):
        try:
            ant = Requerimiento.objects.filter(pk__gt=self.pk).order_by('pk')[0]            
        except:
            ant = Requerimiento.objects.all().first()            
        return ant.pk
    
    def __str__(self):
        return self.codigo
    
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
    
    def save(self, *args, **kwargs):
        if self.codigo == '':
            anio = self.created.year
            mov_ant = Requerimiento.objects.filter(created__year=anio).aggregate(Max('codigo'))
            id_ant=mov_ant['codigo__max']        
            if id_ant is None:
                aux = 1            
            else:
                aux=int(id_ant[-6:])+1
            correlativo = str(aux).zfill(6)
            codigo = 'RQ'+str(anio)+correlativo
            self.codigo = codigo
            puesto_jefe = Puesto.objects.get(oficina=self.oficina,es_jefatura=True,estado=True)
            jefe = puesto_jefe.trabajador
            destinatario = [jefe.usuario.email]
            #self.enviar_correo(destinatario)
            super(Requerimiento, self).save()
            AprobacionRequerimiento.objects.create(requerimiento = self)
        else:
            super(Requerimiento, self).save()
        
    def enviar_correo(self, destinatario):
        email = EmailMessage()
        email.from_email = 'correo@dominio'
        email.subject = self.asunto
        email.body = self.cuerpo
        email.to = destinatario
        email.bcc = ['administrador@dominio']
        email.send()
            
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
        if self.cantidad_comprada == self.cantidad:
            self.estado = DetalleRequerimiento.STATUS.PED            
        elif self.cantidad_comprada < self.cantidad:
            self.estado = DetalleRequerimiento.STATUS.PED_PARC                
        self.save()
        
    def establecer_estado_atendido(self):
        if self.cantidad_atendida == self.cantidad:
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

    def save(self, *args, **kwargs):
        configuracion = Configuracion.objects.first()
        oficina_administracion = configuracion.administracion
        presupuesto = configuracion.presupuesto
        logistica = configuracion.logistica
        if self.estado==self.STATUS.APROB_LOG:
            oficina = presupuesto            
        elif self.estado==self.STATUS.APROB_GER_INM:
            oficina = oficina_administracion
        elif self.estado==self.STATUS.APROB_GER_ADM:
            oficina = logistica        
        elif self.estado==self.STATUS.APROB_JEF:
            oficina = self.requerimiento.oficina.gerencia
        else:
            oficina = None
        if oficina is not None:
            puesto_jefe = Puesto.objects.get(oficina=oficina,es_jefatura=True,estado=True)
            jefe = puesto_jefe.trabajador
            destinatario = [jefe.usuario.email]
            self.requerimiento.enviar_correo(destinatario)
        super(AprobacionRequerimiento, self).save()
        
    def __str__(self):
        return self.pk