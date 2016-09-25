# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('almacen', '0002_auto_20160925_0121'),
        ('compras', '0001_initial'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='aprobacionrequerimiento',
            name='requerimiento',
        ),
        migrations.RemoveField(
            model_name='detallerequerimiento',
            name='producto',
        ),
        migrations.RemoveField(
            model_name='detallerequerimiento',
            name='requerimiento',
        ),
        migrations.RemoveField(
            model_name='grupoproductos',
            name='ctacontable',
        ),
        migrations.RemoveField(
            model_name='producto',
            name='grupo_productos',
        ),
        migrations.RemoveField(
            model_name='producto',
            name='unidad_medida',
        ),
        migrations.RemoveField(
            model_name='requerimiento',
            name='oficina',
        ),
        migrations.RemoveField(
            model_name='requerimiento',
            name='solicitante',
        ),
        migrations.AlterField(
            model_name='cotizacion',
            name='requerimiento',
            field=models.ForeignKey(to='requerimientos.Requerimiento', null=True),
        ),
        migrations.AlterField(
            model_name='detallecotizacion',
            name='detalle_requerimiento',
            field=models.ForeignKey(to='requerimientos.DetalleRequerimiento', null=True),
        ),
        migrations.AlterField(
            model_name='ordencompra',
            name='forma_pago',
            field=models.ForeignKey(to='contabilidad.FormaPago'),
        ),
        migrations.AlterField(
            model_name='ordenservicios',
            name='forma_pago',
            field=models.ForeignKey(to='contabilidad.FormaPago'),
        ),
        migrations.DeleteModel(
            name='AprobacionRequerimiento',
        ),
        migrations.DeleteModel(
            name='DetalleRequerimiento',
        ),
        migrations.DeleteModel(
            name='FormaPago',
        ),
        migrations.DeleteModel(
            name='GrupoProductos',
        ),
        migrations.DeleteModel(
            name='Producto',
        ),
        migrations.DeleteModel(
            name='Requerimiento',
        ),
        migrations.DeleteModel(
            name='UnidadMedida',
        ),
    ]
