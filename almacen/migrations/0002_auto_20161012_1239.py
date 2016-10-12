# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('almacen', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='pedido',
            name='observaciones',
            field=models.TextField(default=b''),
        ),
    ]
