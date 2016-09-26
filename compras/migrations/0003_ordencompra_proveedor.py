# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('compras', '0002_detalleordencompra_producto'),
    ]

    operations = [
        migrations.AddField(
            model_name='ordencompra',
            name='proveedor',
            field=models.ForeignKey(to='compras.Proveedor', null=True),
        ),
    ]
