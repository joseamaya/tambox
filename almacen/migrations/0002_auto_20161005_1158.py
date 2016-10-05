# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('productos', '0003_auto_20161005_1158'),
        ('almacen', '0001_initial'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='almacen',
            options={'ordering': ['codigo'], 'permissions': (('ver_bienvenida', 'Puede ver bienvenida a la aplicaci\xf3n'), ('cargar_almacenes', 'Puede cargar Almacenes desde un archivo externo'), ('ver_detalle_almacen', 'Puede ver detalle Almac\xe9n'), ('ver_tabla_almacenes', 'Puede ver tabla de almacenes'), ('ver_reporte_almacenes_excel', 'Puede ver Reporte Almacenes en excel'))},
        ),
        migrations.AddField(
            model_name='detallepedido',
            name='producto',
            field=models.ForeignKey(to='productos.Producto', null=True),
        ),
    ]
