# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('contabilidad', '0001_initial'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='empresa',
            name='created',
        ),
        migrations.RemoveField(
            model_name='empresa',
            name='modified',
        ),
        migrations.AddField(
            model_name='empresa',
            name='direccion',
            field=models.ForeignKey(default=1, to='contabilidad.Direccion'),
            preserve_default=False,
        ),
    ]
