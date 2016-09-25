# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.utils.timezone
import model_utils.fields


class Migration(migrations.Migration):

    dependencies = [
        ('contabilidad', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='GrupoProductos',
            fields=[
                ('created', model_utils.fields.AutoCreatedField(default=django.utils.timezone.now, verbose_name='created', editable=False)),
                ('modified', model_utils.fields.AutoLastModifiedField(default=django.utils.timezone.now, verbose_name='modified', editable=False)),
                ('codigo', models.CharField(max_length=6, serialize=False, primary_key=True)),
                ('descripcion', models.CharField(max_length=100)),
                ('estado', models.BooleanField(default=True)),
                ('ctacontable', models.ForeignKey(to='contabilidad.CuentaContable')),
            ],
            options={
                'permissions': (('ver_detalle_grupo_productos', 'Puede ver detalle Grupo de Productos'), ('ver_tabla_grupos_productos', 'Puede ver tabla Grupos de Productos'), ('ver_reporte_grupo_productos_excel', 'Puede ver Reporte de grupo de productos en excel')),
            },
        ),
        migrations.CreateModel(
            name='Producto',
            fields=[
                ('created', model_utils.fields.AutoCreatedField(default=django.utils.timezone.now, verbose_name='created', editable=False)),
                ('modified', model_utils.fields.AutoLastModifiedField(default=django.utils.timezone.now, verbose_name='modified', editable=False)),
                ('codigo', models.CharField(max_length=10, serialize=False, primary_key=True)),
                ('descripcion', models.CharField(unique=True, max_length=100)),
                ('desc_abreviada', models.CharField(max_length=40, blank=True)),
                ('es_servicio', models.BooleanField(default=False)),
                ('marca', models.CharField(max_length=40, blank=True)),
                ('modelo', models.CharField(max_length=40, blank=True)),
                ('precio', models.DecimalField(default=0, max_digits=15, decimal_places=5)),
                ('stock', models.DecimalField(default=0, max_digits=15, decimal_places=5)),
                ('stock_minimo', models.DecimalField(default=0, max_digits=15, decimal_places=5)),
                ('imagen', models.ImageField(default=b'productos/sinimagen.png', upload_to=b'productos')),
                ('estado', models.BooleanField(default=True)),
                ('grupo_productos', models.ForeignKey(to='productos.GrupoProductos')),
            ],
            options={
                'permissions': (('cargar_productos', 'Puede cargar Productos desde un archivo externo'), ('ver_detalle_producto', 'Puede ver detalle de Productos'), ('ver_tabla_productos', 'Puede ver tabla Productos'), ('ver_reporte_productos_excel', 'Puede ver Reporte de Productos en excel'), ('puede_hacer_busqueda_producto', 'Puede hacer busqueda Producto')),
            },
        ),
        migrations.CreateModel(
            name='UnidadMedida',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', model_utils.fields.AutoCreatedField(default=django.utils.timezone.now, verbose_name='created', editable=False)),
                ('modified', model_utils.fields.AutoLastModifiedField(default=django.utils.timezone.now, verbose_name='modified', editable=False)),
                ('codigo', models.CharField(unique=True, max_length=5)),
                ('descripcion', models.CharField(max_length=50)),
                ('estado', models.BooleanField(default=True)),
            ],
            options={
                'ordering': ['codigo'],
                'permissions': (('ver_detalle_unidad_medida', 'Puede ver detalle Unidad de Medida'), ('ver_tabla_unidades_medida', 'Puede ver tabla de unidades de medida'), ('ver_reporte_unidades_medida_excel', 'Puede ver Reporte Unidades de Medida en excel')),
            },
        ),
        migrations.AddField(
            model_name='producto',
            name='unidad_medida',
            field=models.ForeignKey(to='productos.UnidadMedida', null=True),
        ),
    ]
