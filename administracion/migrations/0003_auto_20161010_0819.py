# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('administracion', '0002_auto_20161005_1158'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='oficina',
            options={'ordering': ['nombre'], 'permissions': (('ver_bienvenida', 'Puede ver bienvenida a la aplicaci\xf3n'), ('cargar_oficinas', 'Puede cargar oficinas desde un archivo externo'), ('ver_detalle_oficina', 'Puede ver detalle de Oficina'), ('ver_tabla_oficinas', 'Puede ver tabla de Oficinas'), ('ver_reporte_oficinas_excel', 'Puede ver Reporte de Oficinas en excel'))},
        ),
        migrations.AlterModelOptions(
            name='profesion',
            options={'ordering': ['descripcion'], 'permissions': (('ver_detalle_profesion', 'Puede ver detalle de Profesion'), ('cargar_profesiones', 'Puede cargar profesiones desde un archivo externo'), ('ver_tabla_profesiones', 'Puede ver tabla de Profesiones'), ('ver_reporte_profesiones_excel', 'Puede ver Reporte de Profesiones en excel'))},
        ),
        migrations.AlterModelOptions(
            name='puesto',
            options={'ordering': ['nombre'], 'permissions': (('ver_detalle_puesto', 'Puede ver detalle de Puesto'), ('cargar_puestos', 'Puede cargar puestos desde un archivo externo'), ('ver_tabla_puestos', 'Puede ver tabla de Puestos'), ('ver_reporte_puestos_excel', 'Puede ver Reporte de Puestos en excel'))},
        ),
        migrations.AlterModelOptions(
            name='trabajador',
            options={'ordering': ['dni'], 'permissions': (('ver_detalle_trabajador', 'Puede ver detalle de Trabajador'), ('cargar_trabajadores', 'Puede cargar trabajadores desde un archivo externo'), ('ver_tabla_trabajadores', 'Puede ver tabla de Trabajadores'), ('ver_reporte_trabajadores_excel', 'Puede ver Reporte de Trabajadores en excel'))},
        ),
    ]
