# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.utils.timezone
import model_utils.fields


class Migration(migrations.Migration):

    dependencies = [
        ('contabilidad', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='FormaPago',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', model_utils.fields.AutoCreatedField(default=django.utils.timezone.now, verbose_name='created', editable=False)),
                ('modified', model_utils.fields.AutoLastModifiedField(default=django.utils.timezone.now, verbose_name='modified', editable=False)),
                ('codigo', models.CharField(unique=True, max_length=5)),
                ('descripcion', models.CharField(max_length=50)),
                ('dias_credito', models.IntegerField()),
                ('estado', models.BooleanField(default=True)),
            ],
            options={
                'permissions': (('cargar_formas_pago', 'Puede cargar Formas de Pago desde un archivo externo'), ('ver_detalle_forma_pago', 'Puede ver detalle de Forma de Pago'), ('ver_tabla_formas_pago', 'Puede ver tabla Formas de Pago'), ('ver_reporte_formas_pago_excel', 'Puede ver Reporte de Formas de Pago en excel')),
            },
        ),
    ]
