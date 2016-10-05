# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('requerimientos', '0001_initial'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='requerimiento',
            options={'permissions': (('ver_bienvenida', 'Puede ver bienvenida a la aplicaci\xf3n'), ('ver_detalle_requerimiento', 'Puede ver detalle de Requerimiento'), ('ver_tabla_requerimientos', 'Puede ver tabla de Requerimientos'), ('ver_reporte_requerimientos_excel', 'Puede ver Reporte de Requerimientos en excel'), ('puede_hacer_transferencia_requerimiento', 'Puede hacer transferencia de Requerimiento'))},
        ),
    ]
