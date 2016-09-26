# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('contabilidad', '0003_auto_20160926_0907'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='direccion',
            name='empresa',
        ),
        migrations.AddField(
            model_name='empresa',
            name='calle',
            field=models.CharField(default=b'', max_length=150),
        ),
        migrations.AddField(
            model_name='empresa',
            name='departamento',
            field=models.CharField(default='', max_length=100),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='empresa',
            name='distrito',
            field=models.CharField(default='', max_length=100),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='empresa',
            name='lugar',
            field=models.CharField(default=b'', max_length=150),
        ),
        migrations.AddField(
            model_name='empresa',
            name='provincia',
            field=models.CharField(default='', max_length=100),
            preserve_default=False,
        ),
        migrations.DeleteModel(
            name='Direccion',
        ),
    ]
