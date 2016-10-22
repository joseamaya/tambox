# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.utils.timezone
import model_utils.fields


class Migration(migrations.Migration):

    dependencies = [
        ('contabilidad', '0002_auto_20161018_1225'),
    ]

    operations = [
        migrations.CreateModel(
            name='TipoExistencia',
            fields=[
                ('created', model_utils.fields.AutoCreatedField(default=django.utils.timezone.now, verbose_name='created', editable=False)),
                ('modified', model_utils.fields.AutoLastModifiedField(default=django.utils.timezone.now, verbose_name='modified', editable=False)),
                ('codigo_sunat', models.CharField(max_length=2, serialize=False, primary_key=True)),
                ('descripcion', models.CharField(max_length=2)),
            ],
            options={
                'abstract': False,
            },
        ),
    ]
