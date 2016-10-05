# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('administracion', '0001_initial'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='oficina',
            options={'ordering': ['nombre'], 'permissions': (('ver_bienvenida', 'Puede ver bienvenida a la aplicaci\xf3n'), ('ver_detalle_oficina', 'Puede ver detalle de Oficina'), ('ver_tabla_oficinas', 'Puede ver tabla de Oficinas'), ('ver_reporte_oficinas_excel', 'Puede ver Reporte de Oficinas en excel'))},
        ),
    ]
