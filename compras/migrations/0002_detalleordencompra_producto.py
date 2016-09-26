# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('productos', '0001_initial'),
        ('compras', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='detalleordencompra',
            name='producto',
            field=models.ForeignKey(to='productos.Producto', null=True),
        ),
    ]
