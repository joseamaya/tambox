# -*- coding: utf-8 -*- 
from django.db import models
from django.utils.encoding import smart_str
from django.contrib.auth.models import User
from model_utils.models import TimeStampedModel
from administracion.querysets import NavegableQuerySet

# Create your models here.
class Profesion(TimeStampedModel):
    abreviatura = models.CharField(max_length=7)
    descripcion = models.CharField(max_length=30)
    estado = models.BooleanField(default=True)
    objects = NavegableQuerySet.as_manager()
    
    def anterior(self):
        ant = Profesion.objects.anterior(self)
        return ant.pk
    
    def siguiente(self):
        sig = Profesion.objects.siguiente(self)            
        return sig.pk
    
    class Meta:
        permissions = (('ver_detalle_profesion', 'Puede ver detalle de Profesion'),
                       ('cargar_profesiones', 'Puede cargar profesiones desde un archivo externo'),
                       ('ver_tabla_profesiones', 'Puede ver tabla de Profesiones'),
                       ('ver_reporte_profesiones_excel', 'Puede ver Reporte de Profesiones en excel'),)
        ordering = ['descripcion']
    
    def __str__(self):
        return smart_str(self.descripcion)

class Trabajador(TimeStampedModel):
    dni = models.CharField(max_length=8, unique=True)
    usuario = models.OneToOneField(User)
    apellido_paterno = models.CharField(max_length=50)
    apellido_materno = models.CharField(max_length=50)
    nombres = models.CharField(max_length=100)
    profesion = models.ForeignKey(Profesion,null=True)    
    firma = models.ImageField(upload_to='firmas')
    foto = models.ImageField(upload_to='trabajadores', default='trabajadores/sinimagen.png')
    estado = models.BooleanField(default=True)
    objects = NavegableQuerySet.as_manager()
    
    def nombre_completo(self):
        if self.profesion is not None:
            return self.profesion.abreviatura+' '+self.nombres +' '+ self.apellido_paterno+' '+self.apellido_materno
        else:
            return self.nombres +' '+ self.apellido_paterno+' '+self.apellido_materno
    
    def anterior(self):
        ant = Trabajador.objects.anterior(self)
        return ant.pk
    
    def siguiente(self):
        sig = Trabajador.objects.siguiente(self)            
        return sig.pk
    
    @property
    def puesto(self):
        try:
            puesto = self.puesto_set.all().filter(estado=True)[0]
        except: 
            puesto = None
        return puesto
    
    def __str__(self):
        return smart_str(self.apellido_paterno)+' '+smart_str(self.apellido_materno)+' '+smart_str(self.nombres)
    
    class Meta:
        permissions = (('ver_detalle_trabajador', 'Puede ver detalle de Trabajador'),
                       ('cargar_trabajadores', 'Puede cargar trabajadores desde un archivo externo'),
                       ('ver_tabla_trabajadores', 'Puede ver tabla de Trabajadores'),
                       ('ver_reporte_trabajadores_excel', 'Puede ver Reporte de Trabajadores en excel'),)
        ordering = ['apellido_paterno']
    
class Oficina(TimeStampedModel):
    codigo = models.CharField(max_length=4, unique=True)
    nombre = models.CharField(max_length=50)        
    dependencia = models.ForeignKey('self',related_name='depende',null=True)
    gerencia = models.ForeignKey('self',related_name='superior',null=True)
    estado = models.BooleanField(default=True)
    objects = NavegableQuerySet.as_manager()
    
    class Meta:
        permissions = (('ver_bienvenida', 'Puede ver bienvenida a la aplicación'),
                       ('cargar_oficinas', 'Puede cargar oficinas desde un archivo externo'),
                       ('ver_detalle_oficina', 'Puede ver detalle de Oficina'),
                       ('ver_tabla_oficinas', 'Puede ver tabla de Oficinas'),
                       ('ver_reporte_oficinas_excel', 'Puede ver Reporte de Oficinas en excel'),)
        ordering = ['nombre']

    def anterior(self):
        ant = Oficina.objects.anterior(self)
        return ant.pk
    
    def siguiente(self):
        sig = Oficina.objects.siguiente(self)            
        return sig.pk
    
    def __str__(self):
        return smart_str(self.nombre)
    
class Puesto(TimeStampedModel):
    nombre = models.CharField(max_length=100)
    oficina = models.ForeignKey(Oficina)
    trabajador = models.ForeignKey(Trabajador)
    fecha_inicio = models.DateField()
    fecha_fin = models.DateField(null=True)
    es_jefatura = models.BooleanField(default=False)
    es_asistente = models.BooleanField(default=False)
    estado = models.BooleanField(default=True)
    objects = NavegableQuerySet.as_manager()
    
    def anterior(self):
        ant = Puesto.objects.anterior(self)
        return ant.pk
    
    def siguiente(self):
        sig = Puesto.objects.siguiente(self)            
        return sig.pk
    
    @property
    def puesto_superior(self):
        try:
            puesto_superior = Puesto.objects.get(oficina=self.oficina,es_jefatura=True,estado=True)
        except Puesto.DoesNotExist: 
            puesto_superior = None
        return puesto_superior
    
    class Meta:
        permissions = (('ver_detalle_puesto', 'Puede ver detalle de Puesto'),
                       ('cargar_puestos', 'Puede cargar puestos desde un archivo externo'),
                       ('ver_tabla_puestos', 'Puede ver tabla de Puestos'),
                       ('ver_reporte_puestos_excel', 'Puede ver Reporte de Puestos en excel'),)
        ordering = ['nombre']
    
    def save(self, *args, **kwargs):
        if self.fecha_fin is not None:
            self.estado = False
        super(Puesto, self).save()
        
class NivelAprobacion(TimeStampedModel):    
    descripcion =  models.CharField(max_length=100)
    oficina = models.ForeignKey(Oficina)
    nivel_superior = models.ForeignKey('self',null=True)
    aprobacion = models.BooleanField(default=True)
    objects = NavegableQuerySet.as_manager()
    
    def __str__(self):
        return smart_str(self.descripcion)
    
    def anterior(self):
        ant = NivelAprobacion.objects.anterior(self)
        return ant.pk
    
    def siguiente(self):
        sig = NivelAprobacion.objects.siguiente(self)            
        return sig.pk
    
    class Meta:
        permissions = (('ver_detalle_nivel_aprobacion', 'Puede ver detalle de Nivel de Aprobacion'),
                       ('cargar_niveles_aprobacion', 'Puede cargar niveles de aprobacion desde un archivo externo'),
                       ('ver_tabla_niveles_aprobacion', 'Puede ver tabla de Puestos'),
                       ('ver_reporte_niveles_aprobacion_excel', 'Puede ver Reporte de niveles de aprobacion en excel'),)
        ordering = ['descripcion']
    
    def save(self, *args, **kwargs):
        """if self.aprobacion:
            desc = 'APROBADO' + self.oficina.nombre
        else:
            desc = 'DESAPROBADO' + self.oficina.nombre
        self.descripcion = desc"""
        super(NivelAprobacion, self).save()