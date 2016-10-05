# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('productos', '0002_grupoproductos_son_productos'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='producto',
            options={'permissions': (('ver_bienvenida', 'Puede ver bienvenida a la aplicaci\xf3n'), ('cargar_productos', 'Puede cargar Productos desde un archivo externo'), ('ver_detalle_producto', 'Puede ver detalle de Productos'), ('ver_tabla_productos', 'Puede ver tabla Productos'), ('ver_reporte_productos_excel', 'Puede ver Reporte de Productos en excel'), ('puede_hacer_busqueda_producto', 'Puede hacer busqueda Producto'))},
        ),
    ]
