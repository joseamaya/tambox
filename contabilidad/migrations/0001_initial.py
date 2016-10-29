# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import contabilidad.helpers
import django.utils.timezone
import model_utils.fields


class Migration(migrations.Migration):

    dependencies = [
        ('administracion', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Configuracion',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', model_utils.fields.AutoCreatedField(default=django.utils.timezone.now, verbose_name='created', editable=False)),
                ('modified', model_utils.fields.AutoLastModifiedField(default=django.utils.timezone.now, verbose_name='modified', editable=False)),
                ('administracion', models.ForeignKey(related_name='administracion', to='administracion.Oficina', null=True)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='CuentaContable',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', model_utils.fields.AutoCreatedField(default=django.utils.timezone.now, verbose_name='created', editable=False)),
                ('modified', model_utils.fields.AutoLastModifiedField(default=django.utils.timezone.now, verbose_name='modified', editable=False)),
                ('cuenta', models.CharField(unique=True, max_length=12)),
                ('descripcion', models.CharField(max_length=150)),
                ('depreciacion', models.DecimalField(default=0, max_digits=18, decimal_places=2)),
                ('divisionaria', models.BooleanField(default=False)),
                ('estado', models.BooleanField(default=True)),
            ],
            options={
                'ordering': ['cuenta'],
                'permissions': (('cargar_cuentas_contables', 'Puede cargar Cuentas Contables desde un archivo externo'), ('ver_detalle_cuenta_contable', 'Puede ver detalle de Cuenta Contable'), ('ver_tabla_cuentas_contables', 'Puede ver tabla de Cuentas Contables'), ('ver_reporte_cuentas_contables_excel', 'Puede ver Reporte Cuentas Contables en excel')),
            },
        ),
        migrations.CreateModel(
            name='Empresa',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('razon_social', models.CharField(max_length=150)),
                ('ruc', models.CharField(max_length=11)),
                ('logo', models.ImageField(upload_to=b'configuracion')),
                ('lugar', models.CharField(default=b'', max_length=150)),
                ('calle', models.CharField(default=b'', max_length=150)),
                ('distrito', models.CharField(max_length=100)),
                ('provincia', models.CharField(max_length=100)),
                ('departamento', models.CharField(max_length=100)),
                ('host_correo', models.CharField(max_length=70)),
                ('puerto_correo', models.IntegerField(default=25)),
                ('usuario', models.EmailField(max_length=254)),
                ('password', models.CharField(max_length=20)),
                ('usa_tls', models.BooleanField(default=True)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='FormaPago',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', model_utils.fields.AutoCreatedField(default=django.utils.timezone.now, verbose_name='created', editable=False)),
                ('modified', model_utils.fields.AutoLastModifiedField(default=django.utils.timezone.now, verbose_name='modified', editable=False)),
                ('codigo', models.CharField(unique=True, max_length=5)),
                ('descripcion', models.CharField(max_length=50)),
                ('dias_credito', models.IntegerField()),
                ('estado', models.BooleanField(default=True)),
            ],
            options={
                'permissions': (('cargar_formas_pago', 'Puede cargar Formas de Pago desde un archivo externo'), ('ver_detalle_forma_pago', 'Puede ver detalle de Forma de Pago'), ('ver_tabla_formas_pago', 'Puede ver tabla Formas de Pago'), ('ver_reporte_formas_pago_excel', 'Puede ver Reporte de Formas de Pago en excel')),
            },
        ),
        migrations.CreateModel(
            name='Impuesto',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', model_utils.fields.AutoCreatedField(default=django.utils.timezone.now, verbose_name='created', editable=False)),
                ('modified', model_utils.fields.AutoLastModifiedField(default=django.utils.timezone.now, verbose_name='modified', editable=False)),
                ('abreviatura', models.CharField(max_length=10)),
                ('descripcion', models.CharField(max_length=50)),
                ('monto', models.DecimalField(max_digits=14, decimal_places=2)),
                ('fecha_inicio', models.DateField()),
                ('fecha_fin', models.DateField(null=True)),
                ('estado', models.BooleanField(default=True)),
                ('tipo_uso', models.CharField(default=b'COM', max_length=20, choices=[(b'COM', b'COMPRA'), (b'VEN', b'VEN')])),
            ],
            options={
                'ordering': ['abreviatura'],
                'permissions': (('ver_detalle_impuesto', 'Puede ver detalle Impuesto'), ('ver_tabla_impuestos', 'Puede ver tabla de Impuestos'), ('ver_reporte_impuestos_excel', 'Puede ver Reporte de Impuestos en excel')),
            },
        ),
        migrations.CreateModel(
            name='Tipo',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', model_utils.fields.AutoCreatedField(default=django.utils.timezone.now, verbose_name='created', editable=False)),
                ('modified', model_utils.fields.AutoLastModifiedField(default=django.utils.timezone.now, verbose_name='modified', editable=False)),
                ('tabla', models.CharField(max_length=25)),
                ('descripcion_campo', models.CharField(max_length=25)),
                ('codigo', models.CharField(max_length=10)),
                ('descripcion_valor', models.CharField(max_length=100)),
                ('cantidad', models.DecimalField(null=True, max_digits=14, decimal_places=2, blank=True)),
            ],
            options={
                'ordering': ['codigo'],
                'permissions': (('ver_detalle_tipo', 'Puede ver detalle Tipo de Documento'), ('ver_tabla_tipos', 'Puede ver tabla de Tipos de Documentos'), ('ver_reporte_tipos_excel', 'Puede ver Reporte de Tipos de Documentos en excel')),
            },
        ),
        migrations.CreateModel(
            name='TipoDocumento',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', model_utils.fields.AutoCreatedField(default=django.utils.timezone.now, verbose_name='created', editable=False)),
                ('modified', model_utils.fields.AutoLastModifiedField(default=django.utils.timezone.now, verbose_name='modified', editable=False)),
                ('codigo_sunat', models.CharField(max_length=10)),
                ('nombre', models.CharField(max_length=100)),
                ('descripcion', models.CharField(max_length=100)),
                ('estado', models.BooleanField(default=True)),
            ],
            options={
                'ordering': ['codigo_sunat'],
                'permissions': (('cargar_tipos_documento', 'Puede cargar Tipos de Documento desde un archivo externo'), ('ver_detalle_tipo_documento', 'Puede ver detalle Tipo de Documento'), ('ver_tabla_tipos_documentos', 'Puede ver tabla de Tipos de Documentos'), ('ver_reporte_tipos_documentos_excel', 'Puede ver Reporte de Tipos de Documentos en excel')),
            },
        ),
        migrations.CreateModel(
            name='Upload',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', model_utils.fields.AutoCreatedField(default=django.utils.timezone.now, verbose_name='created', editable=False)),
                ('modified', model_utils.fields.AutoLastModifiedField(default=django.utils.timezone.now, verbose_name='modified', editable=False)),
                ('archivo', models.FileField(storage=contabilidad.helpers.OverwriteStorage(), upload_to=b'archivos')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.AddField(
            model_name='configuracion',
            name='impuesto_compra',
            field=models.ForeignKey(to='contabilidad.Impuesto'),
        ),
        migrations.AddField(
            model_name='configuracion',
            name='logistica',
            field=models.ForeignKey(related_name='logistica', to='administracion.Oficina', null=True),
        ),
        migrations.AddField(
            model_name='configuracion',
            name='presupuesto',
            field=models.ForeignKey(related_name='presupuesto', to='administracion.Oficina', null=True),
        ),
    ]
