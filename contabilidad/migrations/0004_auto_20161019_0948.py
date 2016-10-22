# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('contabilidad', '0003_tipoexistencia'),
    ]

    operations = [
        migrations.AlterField(
            model_name='tipoexistencia',
            name='descripcion',
            field=models.CharField(max_length=50),
        ),
    ]
