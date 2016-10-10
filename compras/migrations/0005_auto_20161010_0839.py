# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('compras', '0004_auto_20161005_1158'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='proveedor',
            options={'ordering': ['ruc'], 'permissions': (('cargar_proveedores', 'Puede cargar Proveedores desde un archivo externo'), ('ver_detalle_proveedor', 'Puede ver detalle Proveedor'), ('ver_tabla_proveedores', 'Puede ver tabla de Proveedores'), ('ver_reporte_proveedores_excel', 'Puede ver Reporte Proveedores en excel'))},
        ),
    ]
