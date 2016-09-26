# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('contabilidad', '0002_auto_20160926_0848'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='empresa',
            name='direccion',
        ),
        migrations.AddField(
            model_name='direccion',
            name='empresa',
            field=models.ForeignKey(default=1, to='contabilidad.Empresa'),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='direccion',
            name='calle',
            field=models.CharField(default=b'', max_length=150),
        ),
        migrations.AlterField(
            model_name='direccion',
            name='lugar',
            field=models.CharField(default=b'', max_length=150),
        ),
    ]
