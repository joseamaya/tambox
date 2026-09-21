# -*- coding: utf-8 -*-
from django.db import models
from django.utils.encoding import force_str
from django.contrib.auth.models import User
from model_utils.models import TimeStampedModel
from tambox.querysets import NavegableQuerySet
from django.core.exceptions import ValidationError
from simple_history.models import HistoricalRecords


# Create your models here.
class Profesion(TimeStampedModel):
    abbreviation = models.CharField(max_length=7)
    description = models.CharField(max_length=30)
    is_active = models.BooleanField(default=True)
    history = HistoricalRecords()
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
        ordering = ['description']

    def __str__(self):
        return force_str(self.description)


class Trabajador(TimeStampedModel):
    dni = models.CharField(max_length=8, unique=True)
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='worker', null=True)
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=120)
    profesion = models.ForeignKey(Profesion, on_delete=models.CASCADE, related_name='workers', null=True)
    firma = models.ImageField(upload_to='firmas')
    foto = models.ImageField(upload_to='trabajadores', default='trabajadores/sinimagen.png')
    is_active = models.BooleanField(default=True)
    history = HistoricalRecords()
    objects = NavegableQuerySet.as_manager()

    def nombre_completo(self):
        if self.profesion is not None:
            return self.profesion.abbreviation + ' ' + self.first_name + ' ' + self.last_name
        else:
            return self.first_name + ' ' + self.last_name

    def anterior(self):
        ant = Trabajador.objects.anterior(self)
        return ant.pk

    def siguiente(self):
        sig = Trabajador.objects.siguiente(self)
        return sig.pk

    def anterior_nombres_apellidos(self):
        ant = Trabajador.objects.anterior(self)
        return ant.first_name + " " + ant.last_name

    def siguiente_nombres_apellidos(self):
        sig = Trabajador.objects.siguiente(self)
        return sig.first_name + " " + sig.last_name

    @property
    def puesto(self):
        try:
            puesto = self.positions.all().filter(is_active=True)[0]
        except IndexError:
            puesto = None
        return puesto

    def __str__(self):
        return force_str(self.last_name) + ' ' + force_str(self.first_name)

    class Meta:
        permissions = (('ver_detalle_trabajador', 'Puede ver detalle de Trabajador'),
                       ('cargar_trabajadores', 'Puede cargar trabajadores desde un archivo externo'),
                       ('ver_tabla_trabajadores', 'Puede ver tabla de Trabajadores'),
                       ('ver_reporte_trabajadores_excel', 'Puede ver Reporte de Trabajadores en excel'),)
        ordering = ['last_name']


class Productor(TimeStampedModel):
    dni = models.CharField(max_length=8, unique=True)
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=120)
    is_active = models.BooleanField(default=True)
    history = HistoricalRecords()
    objects = NavegableQuerySet.as_manager()

    def anterior(self):
        ant = Productor.objects.anterior(self)
        return ant.pk

    def siguiente(self):
        sig = Productor.objects.siguiente(self)
        return sig.pk

    def anterior_nombres_apellidos(self):
        ant = Productor.objects.anterior(self)
        return ant.first_name + " " + ant.last_name

    def siguiente_nombres_apellidos(self):
        sig = Productor.objects.siguiente(self)
        return sig.first_name + " " + sig.last_name

    def nombre_completo(self):
        return self.first_name + ' ' + self.last_name

    def __str__(self):
        return force_str(self.last_name) + ' ' + force_str(self.first_name)

    class Meta:
        permissions = (('ver_detalle_productor', 'Puede ver detalle de Productor'),
                       ('cargar_productores', 'Puede cargar productores desde un archivo externo'),
                       ('ver_tabla_productores', 'Puede ver tabla de productores'),
                       ('ver_reporte_productores_excel', 'Puede ver Reporte de productores en excel'),)
        ordering = ['last_name']


class Oficina(TimeStampedModel):
    code = models.CharField(max_length=4, unique=True)
    name = models.CharField(max_length=50)
    is_management = models.BooleanField(default=False)
    dependencia = models.ForeignKey('self', on_delete=models.CASCADE, related_name='superior', null=True)
    is_active = models.BooleanField(default=True)
    history = HistoricalRecords()
    objects = NavegableQuerySet.as_manager()

    class Meta:
        permissions = (('ver_bienvenida', 'Puede ver bienvenida a la aplicación'),
                       ('cargar_oficinas', 'Puede cargar oficinas desde un archivo externo'),
                       ('ver_detalle_oficina', 'Puede ver detalle de Oficina'),
                       ('ver_tabla_oficinas', 'Puede ver tabla de Oficinas'),
                       ('ver_reporte_oficinas_excel', 'Puede ver Reporte de Oficinas en excel'),)
        ordering = ['name']

    @property
    def gerencia(self):
        oficina_superior = self.dependencia
        if oficina_superior.is_management:
            return oficina_superior
        else:
            return oficina_superior.gerencia

    def anterior(self):
        ant = Oficina.objects.anterior(self)
        return ant

    def siguiente(self):
        sig = Oficina.objects.siguiente(self)
        return sig

    def __str__(self):
        return force_str(self.name)


class Puesto(TimeStampedModel):
    name = models.CharField(max_length=100)
    oficina = models.ForeignKey(Oficina, on_delete=models.CASCADE, related_name='positions')
    trabajador = models.ForeignKey(Trabajador, on_delete=models.CASCADE, related_name='positions')
    start_date = models.DateField()
    end_date = models.DateField(null=True)
    is_leadership = models.BooleanField(default=False)
    is_assistant = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    history = HistoricalRecords()
    objects = NavegableQuerySet.as_manager()

    def anterior(self):
        ant = Puesto.objects.anterior(self)
        return ant.pk

    def siguiente(self):
        sig = Puesto.objects.siguiente(self)
        return sig.pk

    @property
    def puesto_superior(self):
        puestos_superiores = Puesto.objects.filter(oficina=self.oficina,
                                                   is_leadership=True,
                                                   is_active=True)
        if puestos_superiores.count() > 0:
            puesto_superior = puestos_superiores[0]
        else:
            puesto_superior = None
        return puesto_superior

    def establecer_nivel(self, oficina_requerimiento):
        from tambox.configuracion import logistica
        description = "LOGISTICA" if (self.oficina == logistica() and self.is_leadership) else "USUARIO"
        try:
            return NivelAprobacion.objects.get(description=description)
        except NivelAprobacion.DoesNotExist:
            raise ValidationError(
                'Falta el nivel de aprobacion "%s". Cargalo en Administracion antes de registrar requerimientos.'
                % description)

    class Meta:
        permissions = (('ver_detalle_puesto', 'Puede ver detalle de Puesto'),
                       ('cargar_puestos', 'Puede cargar puestos desde un archivo externo'),
                       ('ver_tabla_puestos', 'Puede ver tabla de Puestos'),
                       ('ver_reporte_puestos_excel', 'Puede ver Reporte de Puestos en excel'),)
        ordering = ['name']

    def save(self, *args, **kwargs):
        if self.end_date is not None:
            self.is_active = False
        super(Puesto, self).save()


class NivelAprobacion(TimeStampedModel):
    description = models.CharField(max_length=100)
    superior_level = models.ForeignKey('self', on_delete=models.CASCADE, related_name='superior', null=True)
    history = HistoricalRecords()
    objects = NavegableQuerySet.as_manager()

    def __str__(self):
        return force_str(self.description)

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
        ordering = ['description']
