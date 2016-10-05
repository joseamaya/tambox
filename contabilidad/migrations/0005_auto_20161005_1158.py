# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('contabilidad', '0004_auto_20160926_0924'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='cuentacontable',
            options={'ordering': ['cuenta'], 'permissions': (('ver_bienvenida', 'Puede ver bienvenida a la aplicaci\xf3n'), ('cargar_cuentas_contables', 'Puede cargar Cuentas Contables desde un archivo externo'), ('ver_detalle_cuenta_contable', 'Puede ver detalle de Cuenta Contable'), ('ver_tabla_cuentas_contables', 'Puede ver tabla de Cuentas Contables'), ('ver_reporte_cuentas_contables_excel', 'Puede ver Reporte Cuentas Contables en excel'))},
        ),
    ]
