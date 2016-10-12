# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import django.utils.timezone
import model_utils.fields


class Migration(migrations.Migration):

    dependencies = [
        ('productos', '0001_initial'),
        ('administracion', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='DetalleRequerimiento',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', model_utils.fields.AutoCreatedField(default=django.utils.timezone.now, verbose_name='created', editable=False)),
                ('modified', model_utils.fields.AutoLastModifiedField(default=django.utils.timezone.now, verbose_name='modified', editable=False)),
                ('nro_detalle', models.IntegerField()),
                ('otro', models.CharField(max_length=150, null=True)),
                ('unidad', models.CharField(max_length=20, null=True)),
                ('uso', models.CharField(max_length=50, null=True)),
                ('cantidad', models.DecimalField(max_digits=15, decimal_places=5)),
                ('cantidad_comprada', models.DecimalField(default=0, max_digits=15, decimal_places=5)),
                ('cantidad_atendida', models.DecimalField(default=0, max_digits=15, decimal_places=5)),
                ('estado', models.CharField(default=b'PEND', max_length=20, choices=[(b'PEND', b'PENDIENTE'), (b'COTIZ', b'COTIZADO'), (b'COTIZ_PARC', b'COTIZADO PARCIALMENTE'), (b'PED', b'PEDIDO'), (b'PED_PARC', b'PEDIDO PARCIALMENTE'), (b'ATEN', b'ATENDIDO'), (b'ATEN_PARC', b'ATENDIDO PARCIALMENTE'), (b'CANC', b'CANCELADO')])),
                ('producto', models.ForeignKey(to='productos.Producto', null=True)),
            ],
            options={
                'ordering': ['nro_detalle'],
                'permissions': (('can_view', 'Can view Detalle Requerimiento'),),
            },
        ),
        migrations.CreateModel(
            name='Requerimiento',
            fields=[
                ('created', model_utils.fields.AutoCreatedField(default=django.utils.timezone.now, verbose_name='created', editable=False)),
                ('modified', model_utils.fields.AutoLastModifiedField(default=django.utils.timezone.now, verbose_name='modified', editable=False)),
                ('codigo', models.CharField(max_length=12, serialize=False, primary_key=True)),
                ('motivo', models.CharField(max_length=100)),
                ('mes', models.IntegerField(choices=[(1, b'ENERO'), (2, b'FEBRERO'), (3, b'MARZO'), (4, b'ABRIL'), (5, b'MAYO'), (6, b'JUNIO'), (7, b'JULIO'), (8, b'AGOSTO'), (9, b'SETIEMBRE'), (10, b'OCTUBRE'), (11, b'NOVIEMBRE'), (12, b'DICIEMBRE')])),
                ('observaciones', models.TextField()),
                ('informe', models.FileField(null=True, upload_to=b'informes')),
                ('entrega_directa_solicitante', models.BooleanField(default=False)),
                ('estado', models.CharField(default=b'PEND', max_length=20, choices=[(b'PEND', b'PENDIENTE'), (b'COTIZ', b'COTIZADO'), (b'COTIZ_PARC', b'COTIZADO PARCIALMENTE'), (b'PED', b'PEDIDO'), (b'PED_PARC', b'PEDIDO PARCIALMENTE'), (b'ATEN', b'ATENDIDO'), (b'ATEN_PARC', b'ATENDIDO PARCIALMENTE'), (b'CANC', b'CANCELADO')])),
            ],
            options={
                'permissions': (('ver_bienvenida', 'Puede ver bienvenida a la aplicaci\xf3n'), ('ver_detalle_requerimiento', 'Puede ver detalle de Requerimiento'), ('ver_tabla_requerimientos', 'Puede ver tabla de Requerimientos'), ('ver_reporte_requerimientos_excel', 'Puede ver Reporte de Requerimientos en excel'), ('puede_hacer_transferencia_requerimiento', 'Puede hacer transferencia de Requerimiento')),
            },
        ),
        migrations.CreateModel(
            name='AprobacionRequerimiento',
            fields=[
                ('created', model_utils.fields.AutoCreatedField(default=django.utils.timezone.now, verbose_name='created', editable=False)),
                ('modified', model_utils.fields.AutoLastModifiedField(default=django.utils.timezone.now, verbose_name='modified', editable=False)),
                ('requerimiento', models.OneToOneField(primary_key=True, serialize=False, to='requerimientos.Requerimiento')),
                ('estado', models.CharField(default=b'PEND', max_length=20, choices=[(b'PEND', b'PENDIENTE'), (b'APROB_JEF', b'APROBADO JEFATURA'), (b'DESAP_JEF', b'DESAPROBADO JEFATURA'), (b'APROB_GER_INM', b'APROBADO GERENCIA INMEDIATA'), (b'DESAP_GER_INM', b'DESAPROBADO GERENCIA INMEDIATA'), (b'APROB_GER_ADM', b'APROBADO GERENCIA ADMINISTRACION'), (b'DESAP_GER_ADM', b'DESAPROBADO GERENCIA ADMINISTRACION'), (b'APROB_LOG', b'APROBADO LOGISTICA'), (b'DESAP_LOG', b'DESAPROBADO LOGISTICA'), (b'APROB_PRES', b'APROBADO PRESUPUESTO'), (b'DESAP_PRES', b'DESAPROBADO PRESUPUESTO')])),
                ('motivo_desaprobacion', models.TextField(default=b'')),
            ],
            options={
                'permissions': (('ver_tabla_aprobacion_requerimientos', 'Puede ver tabla de Aprobaci\xf3n de Requerimientos'), ('ver_reporte_aprobacion_requerimientos_excel', 'Puede ver Reporte de Aprobaci\xf3n de Requerimientos en excel')),
            },
        ),
        migrations.AddField(
            model_name='requerimiento',
            name='oficina',
            field=models.ForeignKey(to='administracion.Oficina'),
        ),
        migrations.AddField(
            model_name='requerimiento',
            name='solicitante',
            field=models.ForeignKey(to='administracion.Trabajador'),
        ),
        migrations.AddField(
            model_name='detallerequerimiento',
            name='requerimiento',
            field=models.ForeignKey(to='requerimientos.Requerimiento'),
        ),
    ]
