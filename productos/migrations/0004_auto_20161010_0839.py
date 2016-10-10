# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('productos', '0003_auto_20161005_1158'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='grupoproductos',
            options={'permissions': (('cargar_grupo_productos', 'Puede cargar Grupos de Productos desde un archivo externo'), ('ver_detalle_grupo_productos', 'Puede ver detalle Grupo de Productos'), ('ver_tabla_grupos_productos', 'Puede ver tabla Grupos de Productos'), ('ver_reporte_grupo_productos_excel', 'Puede ver Reporte de grupo de productos en excel'))},
        ),
    ]
