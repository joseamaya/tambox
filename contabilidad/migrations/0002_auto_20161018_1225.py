# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('contabilidad', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='empresa',
            name='host_correo',
            field=models.CharField(default='', max_length=70),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='empresa',
            name='password',
            field=models.CharField(default='', max_length=20),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='empresa',
            name='puerto_correo',
            field=models.IntegerField(default=25),
        ),
        migrations.AddField(
            model_name='empresa',
            name='usa_tls',
            field=models.BooleanField(default=True),
        ),
        migrations.AddField(
            model_name='empresa',
            name='usuario',
            field=models.EmailField(default='', max_length=254),
            preserve_default=False,
        ),
    ]
