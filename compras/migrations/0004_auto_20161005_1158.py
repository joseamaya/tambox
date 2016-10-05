# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('compras', '0003_ordencompra_proveedor'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='ordencompra',
            options={'permissions': (('ver_bienvenida', 'Puede ver bienvenida a la aplicaci\xf3n'), ('ver_detalle_orden_compra', 'Puede ver detalle de Orden de Compra'), ('ver_tabla_ordenes_compra', 'Puede ver tabla Ordenes de Compra'), ('ver_reporte_ordenes_compra_excel', 'Puede ver Reporte de Ordenes de Compra en excel'), ('puede_hacer_transferencia_orden_compra', 'Puede hacer transferencia de Orden de Compra'))},
        ),
    ]
