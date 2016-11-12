# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.utils.timezone
from django.conf import settings
import model_utils.fields


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Oficina',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', model_utils.fields.AutoCreatedField(default=django.utils.timezone.now, verbose_name='created', editable=False)),
                ('modified', model_utils.fields.AutoLastModifiedField(default=django.utils.timezone.now, verbose_name='modified', editable=False)),
                ('codigo', models.CharField(unique=True, max_length=4)),
                ('nombre', models.CharField(max_length=50)),
                ('estado', models.BooleanField(default=True)),
                ('dependencia', models.ForeignKey(related_name='depende', to='administracion.Oficina', null=True)),
                ('gerencia', models.ForeignKey(related_name='superior', to='administracion.Oficina', null=True)),
            ],
            options={
                'ordering': ['nombre'],
                'permissions': (('ver_bienvenida', 'Puede ver bienvenida a la aplicaci\xf3n'), ('cargar_oficinas', 'Puede cargar oficinas desde un archivo externo'), ('ver_detalle_oficina', 'Puede ver detalle de Oficina'), ('ver_tabla_oficinas', 'Puede ver tabla de Oficinas'), ('ver_reporte_oficinas_excel', 'Puede ver Reporte de Oficinas en excel')),
            },
        ),
        migrations.CreateModel(
            name='Profesion',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', model_utils.fields.AutoCreatedField(default=django.utils.timezone.now, verbose_name='created', editable=False)),
                ('modified', model_utils.fields.AutoLastModifiedField(default=django.utils.timezone.now, verbose_name='modified', editable=False)),
                ('abreviatura', models.CharField(max_length=7)),
                ('descripcion', models.CharField(max_length=30)),
                ('estado', models.BooleanField(default=True)),
            ],
            options={
                'ordering': ['descripcion'],
                'permissions': (('ver_detalle_profesion', 'Puede ver detalle de Profesion'), ('cargar_profesiones', 'Puede cargar profesiones desde un archivo externo'), ('ver_tabla_profesiones', 'Puede ver tabla de Profesiones'), ('ver_reporte_profesiones_excel', 'Puede ver Reporte de Profesiones en excel')),
            },
        ),
        migrations.CreateModel(
            name='Puesto',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', model_utils.fields.AutoCreatedField(default=django.utils.timezone.now, verbose_name='created', editable=False)),
                ('modified', model_utils.fields.AutoLastModifiedField(default=django.utils.timezone.now, verbose_name='modified', editable=False)),
                ('nombre', models.CharField(max_length=100)),
                ('fecha_inicio', models.DateField()),
                ('fecha_fin', models.DateField(null=True)),
                ('es_jefatura', models.BooleanField(default=False)),
                ('es_asistente', models.BooleanField(default=False)),
                ('estado', models.BooleanField(default=True)),
                ('oficina', models.ForeignKey(to='administracion.Oficina')),
            ],
            options={
                'ordering': ['nombre'],
                'permissions': (('ver_detalle_puesto', 'Puede ver detalle de Puesto'), ('cargar_puestos', 'Puede cargar puestos desde un archivo externo'), ('ver_tabla_puestos', 'Puede ver tabla de Puestos'), ('ver_reporte_puestos_excel', 'Puede ver Reporte de Puestos en excel')),
            },
        ),
        migrations.CreateModel(
            name='Trabajador',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', model_utils.fields.AutoCreatedField(default=django.utils.timezone.now, verbose_name='created', editable=False)),
                ('modified', model_utils.fields.AutoLastModifiedField(default=django.utils.timezone.now, verbose_name='modified', editable=False)),
                ('dni', models.CharField(unique=True, max_length=8)),
                ('apellido_paterno', models.CharField(max_length=50)),
                ('apellido_materno', models.CharField(max_length=50)),
                ('nombres', models.CharField(max_length=100)),
                ('firma', models.ImageField(upload_to=b'firmas')),
                ('foto', models.ImageField(default=b'trabajadores/sinimagen.png', upload_to=b'trabajadores')),
                ('estado', models.BooleanField(default=True)),
                ('profesion', models.ForeignKey(to='administracion.Profesion', null=True)),
                ('usuario', models.OneToOneField(to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['apellido_paterno'],
                'permissions': (('ver_detalle_trabajador', 'Puede ver detalle de Trabajador'), ('cargar_trabajadores', 'Puede cargar trabajadores desde un archivo externo'), ('ver_tabla_trabajadores', 'Puede ver tabla de Trabajadores'), ('ver_reporte_trabajadores_excel', 'Puede ver Reporte de Trabajadores en excel')),
            },
        ),
        migrations.CreateModel(
            name='Upload',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', model_utils.fields.AutoCreatedField(default=django.utils.timezone.now, verbose_name='created', editable=False)),
                ('modified', model_utils.fields.AutoLastModifiedField(default=django.utils.timezone.now, verbose_name='modified', editable=False)),
                ('archivo', models.FileField(upload_to=b'archivos')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.AddField(
            model_name='puesto',
            name='trabajador',
            field=models.ForeignKey(to='administracion.Trabajador'),
        ),
    ]
