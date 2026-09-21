# -*- coding: utf-8 -*-
from django.db import models
from django.utils.encoding import force_str
from django.contrib.auth.models import User
from model_utils.models import TimeStampedModel
from tambox.querysets import NavigableQuerySet
from django.core.exceptions import ValidationError
from simple_history.models import HistoricalRecords


# Create your models here.
class Profession(TimeStampedModel):
    abbreviation = models.CharField(max_length=7)
    description = models.CharField(max_length=30)
    is_active = models.BooleanField(default=True)
    history = HistoricalRecords()
    objects = NavigableQuerySet.as_manager()

    def previous(self):
        ant = Profession.objects.previous(self)
        return ant.pk

    def next(self):
        sig = Profession.objects.next(self)
        return sig.pk

    class Meta:
        permissions = (('ver_detalle_profesion', 'Puede ver detalle de Profesion'),
                       ('cargar_profesiones', 'Puede cargar profesiones desde un archivo externo'),
                       ('ver_tabla_profesiones', 'Puede ver tabla de Profesiones'),
                       ('ver_reporte_profesiones_excel', 'Puede ver Reporte de Profesiones en excel'),)
        ordering = ['description']

    def __str__(self):
        return force_str(self.description)


class Worker(TimeStampedModel):
    dni = models.CharField(max_length=8, unique=True)
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='worker', null=True)
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=120)
    profession = models.ForeignKey(Profession, on_delete=models.CASCADE, related_name='workers', null=True)
    signature = models.ImageField(upload_to='firmas')
    photo = models.ImageField(upload_to='trabajadores', default='trabajadores/sinimagen.png')
    is_active = models.BooleanField(default=True)
    history = HistoricalRecords()
    objects = NavigableQuerySet.as_manager()

    def full_name(self):
        if self.profession is not None:
            return self.profession.abbreviation + ' ' + self.first_name + ' ' + self.last_name
        else:
            return self.first_name + ' ' + self.last_name

    def previous(self):
        ant = Worker.objects.previous(self)
        return ant.pk

    def next(self):
        sig = Worker.objects.next(self)
        return sig.pk

    def previous_full_name(self):
        ant = Worker.objects.previous(self)
        return ant.first_name + " " + ant.last_name

    def next_full_name(self):
        sig = Worker.objects.next(self)
        return sig.first_name + " " + sig.last_name

    @property
    def position(self):
        try:
            position = self.positions.all().filter(is_active=True)[0]
        except IndexError:
            position = None
        return position

    def __str__(self):
        return force_str(self.last_name) + ' ' + force_str(self.first_name)

    class Meta:
        permissions = (('ver_detalle_trabajador', 'Puede ver detalle de Trabajador'),
                       ('cargar_trabajadores', 'Puede cargar trabajadores desde un archivo externo'),
                       ('ver_tabla_trabajadores', 'Puede ver tabla de Trabajadores'),
                       ('ver_reporte_trabajadores_excel', 'Puede ver Reporte de Trabajadores en excel'),)
        ordering = ['last_name']


class Producer(TimeStampedModel):
    dni = models.CharField(max_length=8, unique=True)
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=120)
    is_active = models.BooleanField(default=True)
    history = HistoricalRecords()
    objects = NavigableQuerySet.as_manager()

    def previous(self):
        ant = Producer.objects.previous(self)
        return ant.pk

    def next(self):
        sig = Producer.objects.next(self)
        return sig.pk

    def previous_full_name(self):
        ant = Producer.objects.previous(self)
        return ant.first_name + " " + ant.last_name

    def next_full_name(self):
        sig = Producer.objects.next(self)
        return sig.first_name + " " + sig.last_name

    def full_name(self):
        return self.first_name + ' ' + self.last_name

    def __str__(self):
        return force_str(self.last_name) + ' ' + force_str(self.first_name)

    class Meta:
        permissions = (('ver_detalle_productor', 'Puede ver detalle de Productor'),
                       ('cargar_productores', 'Puede cargar productores desde un archivo externo'),
                       ('ver_tabla_productores', 'Puede ver tabla de productores'),
                       ('ver_reporte_productores_excel', 'Puede ver Reporte de productores en excel'),)
        ordering = ['last_name']


class Office(TimeStampedModel):
    code = models.CharField(max_length=4, unique=True)
    name = models.CharField(max_length=50)
    is_management = models.BooleanField(default=False)
    dependency = models.ForeignKey('self', on_delete=models.CASCADE, related_name='superior', null=True)
    is_active = models.BooleanField(default=True)
    history = HistoricalRecords()
    objects = NavigableQuerySet.as_manager()

    class Meta:
        permissions = (('ver_bienvenida', 'Puede ver bienvenida a la aplicación'),
                       ('cargar_oficinas', 'Puede cargar oficinas desde un archivo externo'),
                       ('ver_detalle_oficina', 'Puede ver detalle de Oficina'),
                       ('ver_tabla_oficinas', 'Puede ver tabla de Oficinas'),
                       ('ver_reporte_oficinas_excel', 'Puede ver Reporte de Oficinas en excel'),)
        ordering = ['name']

    @property
    def management(self):
        oficina_superior = self.dependency
        if oficina_superior.is_management:
            return oficina_superior
        else:
            return oficina_superior.management

    def previous(self):
        ant = Office.objects.previous(self)
        return ant

    def next(self):
        sig = Office.objects.next(self)
        return sig

    def __str__(self):
        return force_str(self.name)


class Position(TimeStampedModel):
    name = models.CharField(max_length=100)
    office = models.ForeignKey(Office, on_delete=models.CASCADE, related_name='positions')
    worker = models.ForeignKey(Worker, on_delete=models.CASCADE, related_name='positions')
    start_date = models.DateField()
    end_date = models.DateField(null=True)
    is_leadership = models.BooleanField(default=False)
    is_assistant = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    history = HistoricalRecords()
    objects = NavigableQuerySet.as_manager()

    def previous(self):
        ant = Position.objects.previous(self)
        return ant.pk

    def next(self):
        sig = Position.objects.next(self)
        return sig.pk

    @property
    def superior_position(self):
        puestos_superiores = Position.objects.filter(office=self.office,
                                                   is_leadership=True,
                                                   is_active=True)
        if puestos_superiores.count() > 0:
            superior_position = puestos_superiores[0]
        else:
            superior_position = None
        return superior_position

    def set_level(self, oficina_requerimiento):
        from tambox.config import logistics
        description = "LOGISTICA" if (self.office == logistics() and self.is_leadership) else "USUARIO"
        try:
            return ApprovalLevel.objects.get(description=description)
        except ApprovalLevel.DoesNotExist:
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
        super(Position, self).save()


class ApprovalLevel(TimeStampedModel):
    description = models.CharField(max_length=100)
    superior_level = models.ForeignKey('self', on_delete=models.CASCADE, related_name='superior', null=True)
    history = HistoricalRecords()
    objects = NavigableQuerySet.as_manager()

    def __str__(self):
        return force_str(self.description)

    def previous(self):
        ant = ApprovalLevel.objects.previous(self)
        return ant.pk

    def next(self):
        sig = ApprovalLevel.objects.next(self)
        return sig.pk

    class Meta:
        permissions = (('ver_detalle_nivel_aprobacion', 'Puede ver detalle de Nivel de Aprobacion'),
                       ('cargar_niveles_aprobacion', 'Puede cargar niveles de aprobacion desde un archivo externo'),
                       ('ver_tabla_niveles_aprobacion', 'Puede ver tabla de Puestos'),
                       ('ver_reporte_niveles_aprobacion_excel', 'Puede ver Reporte de niveles de aprobacion en excel'),)
        ordering = ['description']
