# -*- coding: utf-8 -*-
# Generated by Django 1.11.20 on 2021-03-25 16:55
from __future__ import unicode_literals

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone
import model_utils.fields
import simple_history.models


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        ('compras', '0001_initial'),
        ('administracion', '0001_initial'),
        ('productos', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('contabilidad', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Almacen',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created', model_utils.fields.AutoCreatedField(default=django.utils.timezone.now, editable=False,
                                                                verbose_name='created')),
                ('modified', model_utils.fields.AutoLastModifiedField(default=django.utils.timezone.now, editable=False,
                                                                      verbose_name='modified')),
                ('codigo', models.CharField(max_length=5, unique=True)),
                ('descripcion', models.CharField(max_length=30)),
                ('estado', models.BooleanField(default=True)),
            ],
            options={
                'verbose_name': 'Almacen',
                'verbose_name_plural': 'Almacenes',
                'ordering': ['codigo'],
                'permissions': (('ver_bienvenida', 'Puede ver bienvenida a la aplicación'),
                                ('cargar_almacenes', 'Puede cargar Almacenes desde un archivo externo'),
                                ('ver_detalle_almacen', 'Puede ver detalle Almacén'),
                                ('ver_tabla_almacenes', 'Puede ver tabla de almacenes'),
                                ('ver_reporte_almacenes_excel', 'Puede ver Reporte Almacenes en excel')),
            },
        ),
        migrations.CreateModel(
            name='ControlProductoAlmacen',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created', model_utils.fields.AutoCreatedField(default=django.utils.timezone.now, editable=False,
                                                                verbose_name='created')),
                ('modified', model_utils.fields.AutoLastModifiedField(default=django.utils.timezone.now, editable=False,
                                                                      verbose_name='modified')),
                ('stock', models.DecimalField(decimal_places=8, default=0, max_digits=25)),
                ('precio', models.DecimalField(decimal_places=8, default=0, max_digits=25)),
                ('almacen', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='almacen.Almacen')),
                ('producto', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='productos.Producto')),
            ],
            options={
                'permissions': (('ver_reporte_stock_excel', 'Puede ver Reporte de Stock'),
                                ('ver_reporte_inventario_excel', 'Puede ver Inventario de Stock')),
            },
        ),
        migrations.CreateModel(
            name='DetalleMovimiento',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created', model_utils.fields.AutoCreatedField(default=django.utils.timezone.now, editable=False,
                                                                verbose_name='created')),
                ('modified', model_utils.fields.AutoLastModifiedField(default=django.utils.timezone.now, editable=False,
                                                                      verbose_name='modified')),
                ('nro_detalle', models.IntegerField()),
                ('cantidad', models.DecimalField(decimal_places=8, max_digits=25)),
                ('precio', models.DecimalField(decimal_places=8, max_digits=25)),
                ('valor', models.DecimalField(decimal_places=8, max_digits=25)),
                ('detalle_orden_compra', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE,
                                                           to='compras.DetalleOrdenCompra')),
            ],
        ),
        migrations.CreateModel(
            name='DetallePedido',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created', model_utils.fields.AutoCreatedField(default=django.utils.timezone.now, editable=False,
                                                                verbose_name='created')),
                ('modified', model_utils.fields.AutoLastModifiedField(default=django.utils.timezone.now, editable=False,
                                                                      verbose_name='modified')),
                ('nro_detalle', models.IntegerField()),
                ('cantidad', models.DecimalField(decimal_places=5, max_digits=15)),
                ('cantidad_atendida', models.DecimalField(decimal_places=5, default=0, max_digits=15)),
                ('estado', models.CharField(
                    choices=[('PEND', 'PENDIENTE'), ('APROB', 'APROBADO'), ('DESAP', 'DESAPROBADO'),
                             ('ATEN', 'ATENDIDO'), ('ATEN_PARC', 'ATENDIDO PARCIALMENTE'), ('CANC', 'CANCELADO')],
                    default='PEND', max_length=20)),
            ],
            options={
                'ordering': ['nro_detalle'],
                'permissions': (('can_view', 'Can view Detalle Pedido'),),
            },
        ),
        migrations.CreateModel(
            name='HistoricalAlmacen',
            fields=[
                ('id', models.IntegerField(auto_created=True, blank=True, db_index=True, verbose_name='ID')),
                ('created', model_utils.fields.AutoCreatedField(default=django.utils.timezone.now, editable=False,
                                                                verbose_name='created')),
                ('modified', model_utils.fields.AutoLastModifiedField(default=django.utils.timezone.now, editable=False,
                                                                      verbose_name='modified')),
                ('codigo', models.CharField(db_index=True, max_length=5)),
                ('descripcion', models.CharField(max_length=30)),
                ('estado', models.BooleanField(default=True)),
                ('history_id', models.AutoField(primary_key=True, serialize=False)),
                ('history_change_reason', models.CharField(max_length=100, null=True)),
                ('history_date', models.DateTimeField()),
                ('history_type',
                 models.CharField(choices=[('+', 'Created'), ('~', 'Changed'), ('-', 'Deleted')], max_length=1)),
                ('history_user',
                 models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='+',
                                   to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'historical Almacen',
                'ordering': ('-history_date', '-history_id'),
                'get_latest_by': 'history_date',
            },
            bases=(simple_history.models.HistoricalChanges, models.Model),
        ),
        migrations.CreateModel(
            name='HistoricalControlProductoAlmacen',
            fields=[
                ('id', models.IntegerField(auto_created=True, blank=True, db_index=True, verbose_name='ID')),
                ('created', model_utils.fields.AutoCreatedField(default=django.utils.timezone.now, editable=False,
                                                                verbose_name='created')),
                ('modified', model_utils.fields.AutoLastModifiedField(default=django.utils.timezone.now, editable=False,
                                                                      verbose_name='modified')),
                ('stock', models.DecimalField(decimal_places=8, default=0, max_digits=25)),
                ('precio', models.DecimalField(decimal_places=8, default=0, max_digits=25)),
                ('history_id', models.AutoField(primary_key=True, serialize=False)),
                ('history_change_reason', models.CharField(max_length=100, null=True)),
                ('history_date', models.DateTimeField()),
                ('history_type',
                 models.CharField(choices=[('+', 'Created'), ('~', 'Changed'), ('-', 'Deleted')], max_length=1)),
                ('almacen', models.ForeignKey(blank=True, db_constraint=False, null=True,
                                              on_delete=django.db.models.deletion.DO_NOTHING, related_name='+',
                                              to='almacen.Almacen')),
                ('history_user',
                 models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='+',
                                   to=settings.AUTH_USER_MODEL)),
                ('producto', models.ForeignKey(blank=True, db_constraint=False, null=True,
                                               on_delete=django.db.models.deletion.DO_NOTHING, related_name='+',
                                               to='productos.Producto')),
            ],
            options={
                'verbose_name': 'historical control producto almacen',
                'ordering': ('-history_date', '-history_id'),
                'get_latest_by': 'history_date',
            },
            bases=(simple_history.models.HistoricalChanges, models.Model),
        ),
        migrations.CreateModel(
            name='HistoricalDetalleMovimiento',
            fields=[
                ('id', models.IntegerField(auto_created=True, blank=True, db_index=True, verbose_name='ID')),
                ('created', model_utils.fields.AutoCreatedField(default=django.utils.timezone.now, editable=False,
                                                                verbose_name='created')),
                ('modified', model_utils.fields.AutoLastModifiedField(default=django.utils.timezone.now, editable=False,
                                                                      verbose_name='modified')),
                ('nro_detalle', models.IntegerField()),
                ('cantidad', models.DecimalField(decimal_places=8, max_digits=25)),
                ('precio', models.DecimalField(decimal_places=8, max_digits=25)),
                ('valor', models.DecimalField(decimal_places=8, max_digits=25)),
                ('history_id', models.AutoField(primary_key=True, serialize=False)),
                ('history_change_reason', models.CharField(max_length=100, null=True)),
                ('history_date', models.DateTimeField()),
                ('history_type',
                 models.CharField(choices=[('+', 'Created'), ('~', 'Changed'), ('-', 'Deleted')], max_length=1)),
                ('detalle_orden_compra', models.ForeignKey(blank=True, db_constraint=False, null=True,
                                                           on_delete=django.db.models.deletion.DO_NOTHING,
                                                           related_name='+', to='compras.DetalleOrdenCompra')),
                ('detalle_pedido', models.ForeignKey(blank=True, db_constraint=False, null=True,
                                                     on_delete=django.db.models.deletion.DO_NOTHING, related_name='+',
                                                     to='almacen.DetallePedido')),
                ('history_user',
                 models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='+',
                                   to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'historical detalle movimiento',
                'ordering': ('-history_date', '-history_id'),
                'get_latest_by': 'history_date',
            },
            bases=(simple_history.models.HistoricalChanges, models.Model),
        ),
        migrations.CreateModel(
            name='HistoricalDetallePedido',
            fields=[
                ('id', models.IntegerField(auto_created=True, blank=True, db_index=True, verbose_name='ID')),
                ('created', model_utils.fields.AutoCreatedField(default=django.utils.timezone.now, editable=False,
                                                                verbose_name='created')),
                ('modified', model_utils.fields.AutoLastModifiedField(default=django.utils.timezone.now, editable=False,
                                                                      verbose_name='modified')),
                ('nro_detalle', models.IntegerField()),
                ('cantidad', models.DecimalField(decimal_places=5, max_digits=15)),
                ('cantidad_atendida', models.DecimalField(decimal_places=5, default=0, max_digits=15)),
                ('estado', models.CharField(
                    choices=[('PEND', 'PENDIENTE'), ('APROB', 'APROBADO'), ('DESAP', 'DESAPROBADO'),
                             ('ATEN', 'ATENDIDO'), ('ATEN_PARC', 'ATENDIDO PARCIALMENTE'), ('CANC', 'CANCELADO')],
                    default='PEND', max_length=20)),
                ('history_id', models.AutoField(primary_key=True, serialize=False)),
                ('history_change_reason', models.CharField(max_length=100, null=True)),
                ('history_date', models.DateTimeField()),
                ('history_type',
                 models.CharField(choices=[('+', 'Created'), ('~', 'Changed'), ('-', 'Deleted')], max_length=1)),
                ('history_user',
                 models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='+',
                                   to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'historical detalle pedido',
                'ordering': ('-history_date', '-history_id'),
                'get_latest_by': 'history_date',
            },
            bases=(simple_history.models.HistoricalChanges, models.Model),
        ),
        migrations.CreateModel(
            name='HistoricalKardex',
            fields=[
                ('id', models.IntegerField(auto_created=True, blank=True, db_index=True, verbose_name='ID')),
                ('created', model_utils.fields.AutoCreatedField(default=django.utils.timezone.now, editable=False,
                                                                verbose_name='created')),
                ('modified', model_utils.fields.AutoLastModifiedField(default=django.utils.timezone.now, editable=False,
                                                                      verbose_name='modified')),
                ('nro_detalle_movimiento', models.IntegerField()),
                ('fecha_operacion', models.DateTimeField()),
                ('cantidad_ingreso', models.DecimalField(decimal_places=8, max_digits=25)),
                ('precio_ingreso', models.DecimalField(decimal_places=8, max_digits=25)),
                ('valor_ingreso', models.DecimalField(decimal_places=8, max_digits=25)),
                ('cantidad_salida', models.DecimalField(decimal_places=8, max_digits=25)),
                ('precio_salida', models.DecimalField(decimal_places=8, max_digits=25)),
                ('valor_salida', models.DecimalField(decimal_places=8, max_digits=25)),
                ('cantidad_total', models.DecimalField(decimal_places=8, max_digits=25)),
                ('precio_total', models.DecimalField(decimal_places=8, max_digits=25)),
                ('valor_total', models.DecimalField(decimal_places=8, max_digits=25)),
                ('history_id', models.AutoField(primary_key=True, serialize=False)),
                ('history_change_reason', models.CharField(max_length=100, null=True)),
                ('history_date', models.DateTimeField()),
                ('history_type',
                 models.CharField(choices=[('+', 'Created'), ('~', 'Changed'), ('-', 'Deleted')], max_length=1)),
                ('almacen', models.ForeignKey(blank=True, db_constraint=False, null=True,
                                              on_delete=django.db.models.deletion.DO_NOTHING, related_name='+',
                                              to='almacen.Almacen')),
                ('history_user',
                 models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='+',
                                   to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'historical Kardex',
                'ordering': ('-history_date', '-history_id'),
                'get_latest_by': 'history_date',
            },
            bases=(simple_history.models.HistoricalChanges, models.Model),
        ),
        migrations.CreateModel(
            name='HistoricalMovimiento',
            fields=[
                ('id', models.IntegerField(auto_created=True, blank=True, db_index=True, verbose_name='ID')),
                ('created', model_utils.fields.AutoCreatedField(default=django.utils.timezone.now, editable=False,
                                                                verbose_name='created')),
                ('modified', model_utils.fields.AutoLastModifiedField(default=django.utils.timezone.now, editable=False,
                                                                      verbose_name='modified')),
                ('id_movimiento', models.CharField(db_index=True, max_length=16)),
                ('serie', models.CharField(max_length=15, null=True)),
                ('numero', models.CharField(max_length=10, null=True)),
                ('fecha_operacion', models.DateTimeField()),
                ('observaciones', models.TextField(default='')),
                ('estado',
                 models.CharField(choices=[('ACT', 'ACTIVO'), ('CANC', 'CANCELADA')], default='ACT', max_length=20)),
                ('history_id', models.AutoField(primary_key=True, serialize=False)),
                ('history_change_reason', models.CharField(max_length=100, null=True)),
                ('history_date', models.DateTimeField()),
                ('history_type',
                 models.CharField(choices=[('+', 'Created'), ('~', 'Changed'), ('-', 'Deleted')], max_length=1)),
                ('almacen', models.ForeignKey(blank=True, db_constraint=False, null=True,
                                              on_delete=django.db.models.deletion.DO_NOTHING, related_name='+',
                                              to='almacen.Almacen')),
                ('history_user',
                 models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='+',
                                   to=settings.AUTH_USER_MODEL)),
                ('oficina', models.ForeignKey(blank=True, db_constraint=False, null=True,
                                              on_delete=django.db.models.deletion.DO_NOTHING, related_name='+',
                                              to='administracion.Oficina')),
            ],
            options={
                'verbose_name': 'historical movimiento',
                'ordering': ('-history_date', '-history_id'),
                'get_latest_by': 'history_date',
            },
            bases=(simple_history.models.HistoricalChanges, models.Model),
        ),
        migrations.CreateModel(
            name='HistoricalPedido',
            fields=[
                ('id', models.IntegerField(auto_created=True, blank=True, db_index=True, verbose_name='ID')),
                ('created', model_utils.fields.AutoCreatedField(default=django.utils.timezone.now, editable=False,
                                                                verbose_name='created')),
                ('modified', model_utils.fields.AutoLastModifiedField(default=django.utils.timezone.now, editable=False,
                                                                      verbose_name='modified')),
                ('codigo', models.CharField(db_index=True, max_length=12)),
                ('fecha', models.DateField()),
                ('observaciones', models.TextField(blank=True)),
                ('estado', models.CharField(
                    choices=[('PEND', 'PENDIENTE'), ('APROB', 'APROBADO'), ('DESAP', 'DESAPROBADO'),
                             ('ATEN', 'ATENDIDO'), ('ATEN_PARC', 'ATENDIDO PARCIALMENTE'), ('CANC', 'CANCELADO')],
                    default='PEND', max_length=20)),
                ('history_id', models.AutoField(primary_key=True, serialize=False)),
                ('history_change_reason', models.CharField(max_length=100, null=True)),
                ('history_date', models.DateTimeField()),
                ('history_type',
                 models.CharField(choices=[('+', 'Created'), ('~', 'Changed'), ('-', 'Deleted')], max_length=1)),
                ('history_user',
                 models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='+',
                                   to=settings.AUTH_USER_MODEL)),
                ('oficina', models.ForeignKey(blank=True, db_constraint=False, null=True,
                                              on_delete=django.db.models.deletion.DO_NOTHING, related_name='+',
                                              to='administracion.Oficina')),
                ('solicitante', models.ForeignKey(blank=True, db_constraint=False, null=True,
                                                  on_delete=django.db.models.deletion.DO_NOTHING, related_name='+',
                                                  to='administracion.Trabajador')),
            ],
            options={
                'verbose_name': 'historical pedido',
                'ordering': ('-history_date', '-history_id'),
                'get_latest_by': 'history_date',
            },
            bases=(simple_history.models.HistoricalChanges, models.Model),
        ),
        migrations.CreateModel(
            name='HistoricalTipoMovimiento',
            fields=[
                ('id', models.IntegerField(auto_created=True, blank=True, db_index=True, verbose_name='ID')),
                ('created', model_utils.fields.AutoCreatedField(default=django.utils.timezone.now, editable=False,
                                                                verbose_name='created')),
                ('modified', model_utils.fields.AutoLastModifiedField(default=django.utils.timezone.now, editable=False,
                                                                      verbose_name='modified')),
                ('codigo', models.CharField(db_index=True, max_length=10)),
                ('codigo_sunat', models.CharField(max_length=2)),
                ('descripcion', models.CharField(max_length=25)),
                ('incrementa', models.BooleanField()),
                ('pide_referencia', models.BooleanField(default=False)),
                ('es_compra', models.BooleanField(default=False)),
                ('es_venta', models.BooleanField(default=False)),
                ('estado', models.BooleanField(default=True)),
                ('history_id', models.AutoField(primary_key=True, serialize=False)),
                ('history_change_reason', models.CharField(max_length=100, null=True)),
                ('history_date', models.DateTimeField()),
                ('history_type',
                 models.CharField(choices=[('+', 'Created'), ('~', 'Changed'), ('-', 'Deleted')], max_length=1)),
                ('history_user',
                 models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='+',
                                   to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'historical tipo movimiento',
                'ordering': ('-history_date', '-history_id'),
                'get_latest_by': 'history_date',
            },
            bases=(simple_history.models.HistoricalChanges, models.Model),
        ),
        migrations.CreateModel(
            name='Kardex',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created', model_utils.fields.AutoCreatedField(default=django.utils.timezone.now, editable=False,
                                                                verbose_name='created')),
                ('modified', model_utils.fields.AutoLastModifiedField(default=django.utils.timezone.now, editable=False,
                                                                      verbose_name='modified')),
                ('nro_detalle_movimiento', models.IntegerField()),
                ('fecha_operacion', models.DateTimeField()),
                ('cantidad_ingreso', models.DecimalField(decimal_places=8, max_digits=25)),
                ('precio_ingreso', models.DecimalField(decimal_places=8, max_digits=25)),
                ('valor_ingreso', models.DecimalField(decimal_places=8, max_digits=25)),
                ('cantidad_salida', models.DecimalField(decimal_places=8, max_digits=25)),
                ('precio_salida', models.DecimalField(decimal_places=8, max_digits=25)),
                ('valor_salida', models.DecimalField(decimal_places=8, max_digits=25)),
                ('cantidad_total', models.DecimalField(decimal_places=8, max_digits=25)),
                ('precio_total', models.DecimalField(decimal_places=8, max_digits=25)),
                ('valor_total', models.DecimalField(decimal_places=8, max_digits=25)),
                ('almacen', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='almacen.Almacen')),
            ],
            options={
                'verbose_name': 'Kardex',
                'verbose_name_plural': 'Kardex',
                'ordering': ['movimiento', 'nro_detalle_movimiento'],
                'permissions': (('ver_detalle_kardex', 'Puede ver detalle de Kardex'),
                                ('ver_tabla_kardex', 'Puede ver tabla de Kardex'),
                                ('ver_reporte_kardex_excel', 'Puede ver Reporte de Kardex en excel')),
            },
        ),
        migrations.CreateModel(
            name='Movimiento',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created', model_utils.fields.AutoCreatedField(default=django.utils.timezone.now, editable=False,
                                                                verbose_name='created')),
                ('modified', model_utils.fields.AutoLastModifiedField(default=django.utils.timezone.now, editable=False,
                                                                      verbose_name='modified')),
                ('id_movimiento', models.CharField(max_length=16, unique=True)),
                ('serie', models.CharField(max_length=15, null=True)),
                ('numero', models.CharField(max_length=10, null=True)),
                ('fecha_operacion', models.DateTimeField()),
                ('observaciones', models.TextField(default='')),
                ('estado',
                 models.CharField(choices=[('ACT', 'ACTIVO'), ('CANC', 'CANCELADA')], default='ACT', max_length=20)),
                ('almacen', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='almacen.Almacen')),
                ('oficina', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE,
                                              to='administracion.Oficina')),
            ],
            options={
                'ordering': ['id_movimiento'],
                'permissions': (('ver_detalle_movimiento', 'Puede ver detalle de Movimiento'),
                                ('ver_tabla_movimientos', 'Puede ver tabla de Movimientos'),
                                ('ver_reporte_movimientos_excel', 'Puede ver Reporte de Movimientos en excel')),
            },
        ),
        migrations.CreateModel(
            name='Pedido',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created', model_utils.fields.AutoCreatedField(default=django.utils.timezone.now, editable=False,
                                                                verbose_name='created')),
                ('modified', model_utils.fields.AutoLastModifiedField(default=django.utils.timezone.now, editable=False,
                                                                      verbose_name='modified')),
                ('codigo', models.CharField(max_length=12, unique=True)),
                ('fecha', models.DateField()),
                ('observaciones', models.TextField(blank=True)),
                ('estado', models.CharField(
                    choices=[('PEND', 'PENDIENTE'), ('APROB', 'APROBADO'), ('DESAP', 'DESAPROBADO'),
                             ('ATEN', 'ATENDIDO'), ('ATEN_PARC', 'ATENDIDO PARCIALMENTE'), ('CANC', 'CANCELADO')],
                    default='PEND', max_length=20)),
                (
                'oficina', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='administracion.Oficina')),
                ('solicitante',
                 models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='administracion.Trabajador')),
            ],
            options={
                'permissions': (
                ('aprobar_pedido', 'Puede aprobar Pedido'), ('ver_detalle_pedido', 'Puede ver detalle de Pedido'),
                ('ver_tabla_aprobacion_pedidos', 'Puede ver tabla de Aprobación de Pedidos'),
                ('ver_tabla_pedidos', 'Puede ver tabla de Pedidos'),
                ('ver_reporte_pedidos_excel', 'Puede ver Reporte de Pedidos en excel')),
            },
        ),
        migrations.CreateModel(
            name='TipoMovimiento',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created', model_utils.fields.AutoCreatedField(default=django.utils.timezone.now, editable=False,
                                                                verbose_name='created')),
                ('modified', model_utils.fields.AutoLastModifiedField(default=django.utils.timezone.now, editable=False,
                                                                      verbose_name='modified')),
                ('codigo', models.CharField(max_length=10, unique=True)),
                ('codigo_sunat', models.CharField(max_length=2)),
                ('descripcion', models.CharField(max_length=25)),
                ('incrementa', models.BooleanField()),
                ('pide_referencia', models.BooleanField(default=False)),
                ('es_compra', models.BooleanField(default=False)),
                ('es_venta', models.BooleanField(default=False)),
                ('estado', models.BooleanField(default=True)),
            ],
            options={
                'ordering': ['codigo'],
                'permissions': (('ver_detalle_tipo_movimiento', 'Puede ver detalle Tipo de Movimiento'),
                                ('ver_tabla_tipos_movimientos', 'Puede ver tabla de Tipos de Movimientos'), (
                                'ver_reporte_tipos_movimientos_excel',
                                'Puede ver Reporte Tipos de Movimientos en excel')),
            },
        ),
        migrations.AddField(
            model_name='movimiento',
            name='pedido',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='almacen.Pedido'),
        ),
        migrations.AddField(
            model_name='movimiento',
            name='productor',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE,
                                    to='administracion.Productor'),
        ),
        migrations.AddField(
            model_name='movimiento',
            name='referencia',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='compras.OrdenCompra'),
        ),
        migrations.AddField(
            model_name='movimiento',
            name='tipo_documento',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE,
                                    to='contabilidad.TipoDocumento'),
        ),
        migrations.AddField(
            model_name='movimiento',
            name='tipo_movimiento',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='almacen.TipoMovimiento'),
        ),
        migrations.AddField(
            model_name='movimiento',
            name='trabajador',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE,
                                    to='administracion.Trabajador'),
        ),
        migrations.AddField(
            model_name='kardex',
            name='movimiento',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='almacen.Movimiento'),
        ),
        migrations.AddField(
            model_name='kardex',
            name='producto',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='productos.Producto'),
        ),
        migrations.AddField(
            model_name='historicalmovimiento',
            name='pedido',
            field=models.ForeignKey(blank=True, db_constraint=False, null=True,
                                    on_delete=django.db.models.deletion.DO_NOTHING, related_name='+',
                                    to='almacen.Pedido'),
        ),
        migrations.AddField(
            model_name='historicalmovimiento',
            name='productor',
            field=models.ForeignKey(blank=True, db_constraint=False, null=True,
                                    on_delete=django.db.models.deletion.DO_NOTHING, related_name='+',
                                    to='administracion.Productor'),
        ),
        migrations.AddField(
            model_name='historicalmovimiento',
            name='referencia',
            field=models.ForeignKey(blank=True, db_constraint=False, null=True,
                                    on_delete=django.db.models.deletion.DO_NOTHING, related_name='+',
                                    to='compras.OrdenCompra'),
        ),
        migrations.AddField(
            model_name='historicalmovimiento',
            name='tipo_documento',
            field=models.ForeignKey(blank=True, db_constraint=False, null=True,
                                    on_delete=django.db.models.deletion.DO_NOTHING, related_name='+',
                                    to='contabilidad.TipoDocumento'),
        ),
        migrations.AddField(
            model_name='historicalmovimiento',
            name='tipo_movimiento',
            field=models.ForeignKey(blank=True, db_constraint=False, null=True,
                                    on_delete=django.db.models.deletion.DO_NOTHING, related_name='+',
                                    to='almacen.TipoMovimiento'),
        ),
        migrations.AddField(
            model_name='historicalmovimiento',
            name='trabajador',
            field=models.ForeignKey(blank=True, db_constraint=False, null=True,
                                    on_delete=django.db.models.deletion.DO_NOTHING, related_name='+',
                                    to='administracion.Trabajador'),
        ),
        migrations.AddField(
            model_name='historicalkardex',
            name='movimiento',
            field=models.ForeignKey(blank=True, db_constraint=False, null=True,
                                    on_delete=django.db.models.deletion.DO_NOTHING, related_name='+',
                                    to='almacen.Movimiento'),
        ),
        migrations.AddField(
            model_name='historicalkardex',
            name='producto',
            field=models.ForeignKey(blank=True, db_constraint=False, null=True,
                                    on_delete=django.db.models.deletion.DO_NOTHING, related_name='+',
                                    to='productos.Producto'),
        ),
        migrations.AddField(
            model_name='historicaldetallepedido',
            name='pedido',
            field=models.ForeignKey(blank=True, db_constraint=False, null=True,
                                    on_delete=django.db.models.deletion.DO_NOTHING, related_name='+',
                                    to='almacen.Pedido'),
        ),
        migrations.AddField(
            model_name='historicaldetallepedido',
            name='producto',
            field=models.ForeignKey(blank=True, db_constraint=False, null=True,
                                    on_delete=django.db.models.deletion.DO_NOTHING, related_name='+',
                                    to='productos.Producto'),
        ),
        migrations.AddField(
            model_name='historicaldetallemovimiento',
            name='movimiento',
            field=models.ForeignKey(blank=True, db_constraint=False, null=True,
                                    on_delete=django.db.models.deletion.DO_NOTHING, related_name='+',
                                    to='almacen.Movimiento'),
        ),
        migrations.AddField(
            model_name='historicaldetallemovimiento',
            name='producto',
            field=models.ForeignKey(blank=True, db_constraint=False, null=True,
                                    on_delete=django.db.models.deletion.DO_NOTHING, related_name='+',
                                    to='productos.Producto'),
        ),
        migrations.AddField(
            model_name='detallepedido',
            name='pedido',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='almacen.Pedido'),
        ),
        migrations.AddField(
            model_name='detallepedido',
            name='producto',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='productos.Producto'),
        ),
        migrations.AddField(
            model_name='detallemovimiento',
            name='detalle_pedido',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='almacen.DetallePedido'),
        ),
        migrations.AddField(
            model_name='detallemovimiento',
            name='movimiento',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='almacen.Movimiento'),
        ),
        migrations.AddField(
            model_name='detallemovimiento',
            name='producto',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='productos.Producto'),
        ),
        migrations.AlterUniqueTogether(
            name='detallemovimiento',
            unique_together=set([('nro_detalle', 'movimiento')]),
        ),
        migrations.AlterUniqueTogether(
            name='controlproductoalmacen',
            unique_together=set([('producto', 'almacen')]),
        ),
    ]