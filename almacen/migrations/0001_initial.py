# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.utils.timezone
import model_utils.fields


class Migration(migrations.Migration):

    dependencies = [
        ('productos', '0001_initial'),
        ('compras', '0001_initial'),
        ('contabilidad', '0001_initial'),
        ('administracion', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Almacen',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', model_utils.fields.AutoCreatedField(default=django.utils.timezone.now, verbose_name='created', editable=False)),
                ('modified', model_utils.fields.AutoLastModifiedField(default=django.utils.timezone.now, verbose_name='modified', editable=False)),
                ('codigo', models.CharField(unique=True, max_length=5)),
                ('descripcion', models.CharField(max_length=30)),
                ('estado', models.BooleanField(default=True)),
            ],
            options={
                'ordering': ['codigo'],
                'permissions': (('ver_bienvenida', 'Puede ver bienvenida a la aplicaci\xf3n'), ('cargar_almacenes', 'Puede cargar Almacenes desde un archivo externo'), ('ver_detalle_almacen', 'Puede ver detalle Almac\xe9n'), ('ver_tabla_almacenes', 'Puede ver tabla de almacenes'), ('ver_reporte_almacenes_excel', 'Puede ver Reporte Almacenes en excel')),
            },
        ),
        migrations.CreateModel(
            name='ControlProductoAlmacen',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', model_utils.fields.AutoCreatedField(default=django.utils.timezone.now, verbose_name='created', editable=False)),
                ('modified', model_utils.fields.AutoLastModifiedField(default=django.utils.timezone.now, verbose_name='modified', editable=False)),
                ('stock', models.DecimalField(default=0, max_digits=15, decimal_places=5)),
                ('precio', models.DecimalField(default=0, max_digits=15, decimal_places=5)),
                ('almacen', models.ForeignKey(to='almacen.Almacen')),
                ('producto', models.ForeignKey(to='productos.Producto')),
            ],
            options={
                'permissions': (('ver_reporte_stock_excel', 'Puede ver Reporte de Stock'),),
            },
        ),
        migrations.CreateModel(
            name='DetalleMovimiento',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', model_utils.fields.AutoCreatedField(default=django.utils.timezone.now, verbose_name='created', editable=False)),
                ('modified', model_utils.fields.AutoLastModifiedField(default=django.utils.timezone.now, verbose_name='modified', editable=False)),
                ('nro_detalle', models.IntegerField()),
                ('cantidad', models.DecimalField(max_digits=15, decimal_places=5)),
                ('precio', models.DecimalField(max_digits=15, decimal_places=5)),
                ('valor', models.DecimalField(null=True, max_digits=15, decimal_places=5, blank=True)),
                ('detalle_orden_compra', models.ForeignKey(to='compras.DetalleOrdenCompra', null=True)),
            ],
        ),
        migrations.CreateModel(
            name='DetallePedido',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', model_utils.fields.AutoCreatedField(default=django.utils.timezone.now, verbose_name='created', editable=False)),
                ('modified', model_utils.fields.AutoLastModifiedField(default=django.utils.timezone.now, verbose_name='modified', editable=False)),
                ('nro_detalle', models.IntegerField()),
                ('cantidad', models.DecimalField(max_digits=15, decimal_places=5)),
                ('cantidad_atendida', models.DecimalField(default=0, max_digits=15, decimal_places=5)),
                ('estado', models.CharField(default=b'PEND', max_length=20, choices=[(b'PEND', b'PENDIENTE'), (b'APROB', b'APROBADO'), (b'DESAP', b'DESAPROBADO'), (b'ATEN', b'ATENDIDO'), (b'ATEN_PARC', b'ATENDIDO PARCIALMENTE'), (b'CANC', b'CANCELADO')])),
            ],
            options={
                'ordering': ['nro_detalle'],
                'permissions': (('can_view', 'Can view Detalle Pedido'),),
            },
        ),
        migrations.CreateModel(
            name='Kardex',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', model_utils.fields.AutoCreatedField(default=django.utils.timezone.now, verbose_name='created', editable=False)),
                ('modified', model_utils.fields.AutoLastModifiedField(default=django.utils.timezone.now, verbose_name='modified', editable=False)),
                ('nro_detalle_movimiento', models.IntegerField()),
                ('fecha_operacion', models.DateTimeField()),
                ('cantidad_ingreso', models.DecimalField(max_digits=15, decimal_places=5)),
                ('precio_ingreso', models.DecimalField(max_digits=15, decimal_places=5)),
                ('valor_ingreso', models.DecimalField(max_digits=15, decimal_places=5)),
                ('cantidad_salida', models.DecimalField(max_digits=15, decimal_places=5)),
                ('precio_salida', models.DecimalField(max_digits=15, decimal_places=5)),
                ('valor_salida', models.DecimalField(max_digits=15, decimal_places=5)),
                ('cantidad_total', models.DecimalField(max_digits=15, decimal_places=5)),
                ('precio_total', models.DecimalField(max_digits=15, decimal_places=5)),
                ('valor_total', models.DecimalField(max_digits=15, decimal_places=5)),
                ('almacen', models.ForeignKey(to='almacen.Almacen')),
            ],
            options={
                'ordering': ['movimiento', 'nro_detalle_movimiento'],
                'permissions': (('ver_detalle_kardex', 'Puede ver detalle de Kardex'), ('ver_tabla_kardex', 'Puede ver tabla de Kardex'), ('ver_reporte_kardex_excel', 'Puede ver Reporte de Kardex en excel')),
            },
        ),
        migrations.CreateModel(
            name='Movimiento',
            fields=[
                ('created', model_utils.fields.AutoCreatedField(default=django.utils.timezone.now, verbose_name='created', editable=False)),
                ('modified', model_utils.fields.AutoLastModifiedField(default=django.utils.timezone.now, verbose_name='modified', editable=False)),
                ('id_movimiento', models.CharField(max_length=16, serialize=False, primary_key=True)),
                ('serie', models.CharField(max_length=15, null=True)),
                ('numero', models.CharField(max_length=10, null=True)),
                ('fecha_operacion', models.DateTimeField()),
                ('total', models.DecimalField(max_digits=15, decimal_places=5)),
                ('observaciones', models.TextField(default=b'')),
                ('estado', models.CharField(default=b'ACT', max_length=20, choices=[(b'ACT', b'ACTIVO'), (b'CANC', b'CANCELADA')])),
                ('almacen', models.ForeignKey(to='almacen.Almacen')),
                ('oficina', models.ForeignKey(to='administracion.Oficina', null=True)),
                ('referencia', models.ForeignKey(to='compras.OrdenCompra', null=True)),
                ('tipo_documento', models.ForeignKey(to='contabilidad.TipoDocumento', null=True)),
            ],
            options={
                'ordering': ['id_movimiento'],
                'permissions': (('ver_detalle_movimiento', 'Puede ver detalle de Movimiento'), ('ver_tabla_movimientos', 'Puede ver tabla de Movimientos'), ('ver_reporte_movimientos_excel', 'Puede ver Reporte de Movimientos en excel')),
            },
        ),
        migrations.CreateModel(
            name='Pedido',
            fields=[
                ('created', model_utils.fields.AutoCreatedField(default=django.utils.timezone.now, verbose_name='created', editable=False)),
                ('modified', model_utils.fields.AutoLastModifiedField(default=django.utils.timezone.now, verbose_name='modified', editable=False)),
                ('codigo', models.CharField(max_length=12, serialize=False, primary_key=True)),
                ('fecha', models.DateField()),
                ('observaciones', models.TextField(null=True)),
                ('estado', models.CharField(default=b'PEND', max_length=20, choices=[(b'PEND', b'PENDIENTE'), (b'APROB', b'APROBADO'), (b'DESAP', b'DESAPROBADO'), (b'ATEN', b'ATENDIDO'), (b'ATEN_PARC', b'ATENDIDO PARCIALMENTE'), (b'CANC', b'CANCELADO')])),
                ('oficina', models.ForeignKey(to='administracion.Oficina')),
                ('solicitante', models.ForeignKey(to='administracion.Trabajador')),
            ],
            options={
                'permissions': (('aprobar_pedido', 'Puede aprobar Pedido'), ('ver_detalle_pedido', 'Puede ver detalle de Pedido'), ('ver_tabla_aprobacion_pedidos', 'Puede ver tabla de Aprobaci\xf3n de Pedidos'), ('ver_tabla_pedidos', 'Puede ver tabla de Pedidos'), ('ver_reporte_pedidos_excel', 'Puede ver Reporte de Pedidos en excel')),
            },
        ),
        migrations.CreateModel(
            name='TipoMovimiento',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', model_utils.fields.AutoCreatedField(default=django.utils.timezone.now, verbose_name='created', editable=False)),
                ('modified', model_utils.fields.AutoLastModifiedField(default=django.utils.timezone.now, verbose_name='modified', editable=False)),
                ('codigo', models.CharField(unique=True, max_length=10)),
                ('codigo_sunat', models.CharField(max_length=2)),
                ('descripcion', models.CharField(max_length=25)),
                ('incrementa', models.BooleanField()),
                ('pide_referencia', models.BooleanField(default=False)),
                ('estado', models.BooleanField(default=True)),
            ],
            options={
                'ordering': ['codigo'],
                'permissions': (('ver_detalle_tipo_movimiento', 'Puede ver detalle Tipo de Movimiento'), ('ver_tabla_tipos_movimientos', 'Puede ver tabla de Tipos de Movimientos'), ('ver_reporte_tipos_movimientos_excel', 'Puede ver Reporte Tipos de Movimientos en excel')),
            },
        ),
        migrations.AddField(
            model_name='movimiento',
            name='tipo_movimiento',
            field=models.ForeignKey(to='almacen.TipoMovimiento'),
        ),
        migrations.AddField(
            model_name='kardex',
            name='movimiento',
            field=models.ForeignKey(to='almacen.Movimiento'),
        ),
        migrations.AddField(
            model_name='kardex',
            name='producto',
            field=models.ForeignKey(to='productos.Producto'),
        ),
        migrations.AddField(
            model_name='detallepedido',
            name='pedido',
            field=models.ForeignKey(to='almacen.Pedido'),
        ),
        migrations.AddField(
            model_name='detallepedido',
            name='producto',
            field=models.ForeignKey(to='productos.Producto', null=True),
        ),
        migrations.AddField(
            model_name='detallemovimiento',
            name='detalle_pedido',
            field=models.ForeignKey(to='almacen.DetallePedido', null=True),
        ),
        migrations.AddField(
            model_name='detallemovimiento',
            name='movimiento',
            field=models.ForeignKey(to='almacen.Movimiento'),
        ),
        migrations.AddField(
            model_name='detallemovimiento',
            name='producto',
            field=models.ForeignKey(to='productos.Producto'),
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
