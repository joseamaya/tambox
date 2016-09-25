# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('almacen', '0001_initial'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='detallepedido',
            name='producto',
        ),
        migrations.AlterField(
            model_name='controlproductoalmacen',
            name='producto',
            field=models.ForeignKey(to='productos.Producto'),
        ),
        migrations.AlterField(
            model_name='detallemovimiento',
            name='producto',
            field=models.ForeignKey(to='productos.Producto'),
        ),
        migrations.AlterField(
            model_name='kardex',
            name='producto',
            field=models.ForeignKey(to='productos.Producto'),
        ),
    ]
