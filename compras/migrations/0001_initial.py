# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.utils.timezone
import model_utils.fields


class Migration(migrations.Migration):

    dependencies = [
        ('productos', '0001_initial'),
        ('requerimientos', '0001_initial'),
        ('contabilidad', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='ConformidadServicio',
            fields=[
                ('created', model_utils.fields.AutoCreatedField(default=django.utils.timezone.now, verbose_name='created', editable=False)),
                ('modified', model_utils.fields.AutoLastModifiedField(default=django.utils.timezone.now, verbose_name='modified', editable=False)),
                ('codigo', models.CharField(max_length=12, serialize=False, primary_key=True)),
                ('doc_sustento', models.CharField(max_length=12)),
                ('fecha', models.DateField()),
                ('total', models.DecimalField(max_digits=15, decimal_places=5)),
                ('total_letras', models.CharField(max_length=150)),
                ('estado', models.BooleanField(default=True)),
            ],
            options={
                'permissions': (('ver_detalle_conformidad_servicio', 'Puede ver detalle de Conformidad de Servicio'), ('ver_tabla_conformidades_servicio', 'Puede ver tabla de Conformidades de Servicio'), ('ver_reporte_conformidades_servicio_excel', 'Puede ver Reporte de Conformidades de Servicio en excel')),
            },
        ),
        migrations.CreateModel(
            name='Cotizacion',
            fields=[
                ('created', model_utils.fields.AutoCreatedField(default=django.utils.timezone.now, verbose_name='created', editable=False)),
                ('modified', model_utils.fields.AutoLastModifiedField(default=django.utils.timezone.now, verbose_name='modified', editable=False)),
                ('codigo', models.CharField(max_length=12, serialize=False, primary_key=True)),
                ('fecha', models.DateField()),
                ('observaciones', models.TextField(blank=True)),
                ('estado', models.CharField(default=b'PEND', max_length=20, choices=[(b'PEND', b'PENDIENTE'), (b'ELEG', b'ELEGIDA'), (b'ELEG_PARC', b'ELEGIDA PARCIALMENTE'), (b'DESC', b'DESCARTADA'), (b'CANC', b'CANCELADO')])),
            ],
            options={
                'permissions': (('ver_detalle_cotizacion', 'Puede ver detalle de Cotizaci\xf3n'), ('ver_tabla_cotizaciones', 'Puede ver tabla Cotizaciones'), ('ver_reporte_cotizaciones_excel', 'Puede ver Reporte de Cotizaciones en excel'), ('puede_hacer_transferencia_cotizacion', 'Puede hacer transferencia de Cotizaci\xf3n')),
            },
        ),
        migrations.CreateModel(
            name='DetalleConformidadServicio',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', model_utils.fields.AutoCreatedField(default=django.utils.timezone.now, verbose_name='created', editable=False)),
                ('modified', model_utils.fields.AutoLastModifiedField(default=django.utils.timezone.now, verbose_name='modified', editable=False)),
                ('nro_detalle', models.IntegerField()),
                ('cantidad', models.DecimalField(default=0, max_digits=15, decimal_places=5)),
                ('conformidad', models.ForeignKey(to='compras.ConformidadServicio')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='DetalleCotizacion',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', model_utils.fields.AutoCreatedField(default=django.utils.timezone.now, verbose_name='created', editable=False)),
                ('modified', model_utils.fields.AutoLastModifiedField(default=django.utils.timezone.now, verbose_name='modified', editable=False)),
                ('status', model_utils.fields.StatusField(default=b'PEND', max_length=100, verbose_name='status', no_check_for_status=True, choices=[(b'PEND', b'PENDIENTE'), (b'ELEG', b'ELEGIDA'), (b'ELEG_PARC', b'ELEGIDA PARCIALMENTE'), (b'DESC', b'DESCARTADA'), (b'CANC', b'CANCELADO')])),
                ('status_changed', model_utils.fields.MonitorField(default=django.utils.timezone.now, verbose_name='status changed', monitor='status')),
                ('nro_detalle', models.IntegerField()),
                ('cantidad', models.DecimalField(max_digits=15, decimal_places=5)),
                ('cantidad_comprada', models.DecimalField(default=0, max_digits=15, decimal_places=5)),
                ('estado', models.CharField(default=b'PEND', max_length=20, choices=[(b'PEND', b'PENDIENTE'), (b'ELEG', b'ELEGIDA'), (b'ELEG_PARC', b'ELEGIDA PARCIALMENTE'), (b'DESC', b'DESCARTADA'), (b'CANC', b'CANCELADO')])),
                ('cotizacion', models.ForeignKey(to='compras.Cotizacion')),
                ('detalle_requerimiento', models.ForeignKey(to='requerimientos.DetalleRequerimiento', null=True)),
            ],
            options={
                'permissions': (('can_view', 'Can view Detalle Orden de Compra'),),
            },
        ),
        migrations.CreateModel(
            name='DetalleOrdenCompra',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', model_utils.fields.AutoCreatedField(default=django.utils.timezone.now, verbose_name='created', editable=False)),
                ('modified', model_utils.fields.AutoLastModifiedField(default=django.utils.timezone.now, verbose_name='modified', editable=False)),
                ('nro_detalle', models.IntegerField()),
                ('cantidad', models.DecimalField(max_digits=15, decimal_places=5)),
                ('cantidad_ingresada', models.DecimalField(default=0, max_digits=15, decimal_places=5)),
                ('precio', models.DecimalField(max_digits=15, decimal_places=5)),
                ('valor', models.DecimalField(null=True, max_digits=15, decimal_places=5, blank=True)),
                ('impuesto', models.DecimalField(null=True, max_digits=15, decimal_places=5, blank=True)),
                ('estado', models.CharField(default=b'PEND', max_length=20, choices=[(b'PEND', b'PENDIENTE'), (b'ING', b'INGRESADO'), (b'ING_PARC', b'INGRESADO PARCIALMENTE'), (b'CANC', b'CANCELADO')])),
                ('detalle_cotizacion', models.ForeignKey(to='compras.DetalleCotizacion', null=True)),
            ],
            options={
                'permissions': (('can_view', 'Can view Detalle Orden de Compra'),),
            },
        ),
        migrations.CreateModel(
            name='DetalleOrdenServicios',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', model_utils.fields.AutoCreatedField(default=django.utils.timezone.now, verbose_name='created', editable=False)),
                ('modified', model_utils.fields.AutoLastModifiedField(default=django.utils.timezone.now, verbose_name='modified', editable=False)),
                ('nro_detalle', models.IntegerField()),
                ('cantidad', models.DecimalField(max_digits=15, decimal_places=5)),
                ('cantidad_conforme', models.DecimalField(default=0, max_digits=15, decimal_places=5)),
                ('precio', models.DecimalField(max_digits=15, decimal_places=5)),
                ('valor', models.DecimalField(null=True, max_digits=15, decimal_places=5, blank=True)),
                ('impuesto', models.DecimalField(default=0, max_digits=15, decimal_places=5)),
                ('estado', models.CharField(default=b'PEND', max_length=20, choices=[(b'PEND', b'PENDIENTE'), (b'CONF', b'CONFORME'), (b'CONF_PARC', b'CONFORME PARCIALMENTE'), (b'CANC', b'CANCELADA')])),
                ('detalle_cotizacion', models.ForeignKey(to='compras.DetalleCotizacion', null=True)),
            ],
            options={
                'ordering': ['nro_detalle'],
                'permissions': (('ver_detalle_orden_servicios', 'Puede ver Detalle Orden de Servicios'),),
            },
        ),
        migrations.CreateModel(
            name='OrdenCompra',
            fields=[
                ('created', model_utils.fields.AutoCreatedField(default=django.utils.timezone.now, verbose_name='created', editable=False)),
                ('modified', model_utils.fields.AutoLastModifiedField(default=django.utils.timezone.now, verbose_name='modified', editable=False)),
                ('codigo', models.CharField(max_length=12, serialize=False, primary_key=True)),
                ('proceso', models.CharField(default=b'', max_length=50)),
                ('fecha', models.DateField()),
                ('subtotal', models.DecimalField(max_digits=15, decimal_places=5)),
                ('igv', models.DecimalField(max_digits=15, decimal_places=5)),
                ('total', models.DecimalField(max_digits=15, decimal_places=5)),
                ('total_letras', models.CharField(max_length=150)),
                ('observaciones', models.TextField(default=b'')),
                ('estado', models.CharField(default=b'PEND', max_length=20, choices=[(b'PEND', b'PENDIENTE'), (b'ING', b'INGRESADA'), (b'ING_PARC', b'INGRESADA PARCIALMENTE'), (b'CANC', b'CANCELADA')])),
                ('cotizacion', models.ForeignKey(to='compras.Cotizacion', null=True)),
                ('forma_pago', models.ForeignKey(to='contabilidad.FormaPago')),
            ],
            options={
                'permissions': (('ver_bienvenida', 'Puede ver bienvenida a la aplicaci\xf3n'), ('ver_detalle_orden_compra', 'Puede ver detalle de Orden de Compra'), ('ver_tabla_ordenes_compra', 'Puede ver tabla Ordenes de Compra'), ('ver_reporte_ordenes_compra_excel', 'Puede ver Reporte de Ordenes de Compra en excel'), ('puede_hacer_transferencia_orden_compra', 'Puede hacer transferencia de Orden de Compra')),
            },
        ),
        migrations.CreateModel(
            name='OrdenServicios',
            fields=[
                ('created', model_utils.fields.AutoCreatedField(default=django.utils.timezone.now, verbose_name='created', editable=False)),
                ('modified', model_utils.fields.AutoLastModifiedField(default=django.utils.timezone.now, verbose_name='modified', editable=False)),
                ('codigo', models.CharField(max_length=12, serialize=False, primary_key=True)),
                ('proceso', models.CharField(default=b'', max_length=50)),
                ('subtotal', models.DecimalField(max_digits=15, decimal_places=5)),
                ('igv', models.DecimalField(default=0, max_digits=15, decimal_places=5)),
                ('total', models.DecimalField(max_digits=15, decimal_places=5)),
                ('total_letras', models.CharField(max_length=150)),
                ('fecha', models.DateField()),
                ('observaciones', models.TextField(default=b'')),
                ('estado', models.CharField(default=b'PEND', max_length=20, choices=[(b'PEND', b'PENDIENTE'), (b'CONF', b'CONFORME'), (b'CONF_PARC', b'CONFORME PARCIALMENTE'), (b'CANC', b'CANCELADA')])),
                ('cotizacion', models.ForeignKey(to='compras.Cotizacion', null=True)),
                ('forma_pago', models.ForeignKey(to='contabilidad.FormaPago')),
            ],
            options={
                'permissions': (('ver_detalle_orden_servicios', 'Puede ver detalle de Orden de Servicios'), ('ver_tabla_ordenes_servicios', 'Puede ver tabla de Ordenes de Servicios'), ('ver_reporte_ordenes_servicios_excel', 'Puede ver Reporte de Ordenes de Servicios en excel')),
            },
        ),
        migrations.CreateModel(
            name='Proveedor',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', model_utils.fields.AutoCreatedField(default=django.utils.timezone.now, verbose_name='created', editable=False)),
                ('modified', model_utils.fields.AutoLastModifiedField(default=django.utils.timezone.now, verbose_name='modified', editable=False)),
                ('ruc', models.CharField(unique=True, max_length=11)),
                ('razon_social', models.CharField(max_length=150)),
                ('direccion', models.CharField(max_length=200)),
                ('telefono', models.CharField(max_length=15, null=True)),
                ('correo', models.EmailField(max_length=254, null=True)),
                ('estado_sunat', models.CharField(max_length=50)),
                ('condicion', models.CharField(max_length=50)),
                ('ciiu', models.CharField(max_length=250)),
                ('fecha_alta', models.DateField()),
                ('estado', models.BooleanField(default=True)),
            ],
            options={
                'ordering': ['ruc'],
                'permissions': (('ver_detalle_proveedor', 'Puede ver detalle Proveedor'), ('ver_tabla_proveedores', 'Puede ver tabla de Proveedores'), ('ver_reporte_proveedores_excel', 'Puede ver Reporte Proveedores en excel')),
            },
        ),
        migrations.CreateModel(
            name='RepresentanteLegal',
            fields=[
                ('created', model_utils.fields.AutoCreatedField(default=django.utils.timezone.now, verbose_name='created', editable=False)),
                ('modified', model_utils.fields.AutoLastModifiedField(default=django.utils.timezone.now, verbose_name='modified', editable=False)),
                ('documento', models.CharField(max_length=11, serialize=False, primary_key=True)),
                ('nombre', models.CharField(max_length=150)),
                ('cargo', models.CharField(max_length=50)),
            ],
            options={
                'permissions': (('can_view', 'Can view Representante Legal'), ('can_view_listado', 'Can view Listado Representante Legal'), ('can_view_excel', 'Can view Representante Legal excel')),
            },
        ),
        migrations.AddField(
            model_name='proveedor',
            name='representantes',
            field=models.ManyToManyField(to='compras.RepresentanteLegal'),
        ),
        migrations.AddField(
            model_name='ordencompra',
            name='proveedor',
            field=models.ForeignKey(to='compras.Proveedor', null=True),
        ),
        migrations.AddField(
            model_name='detalleordenservicios',
            name='orden',
            field=models.ForeignKey(to='compras.OrdenServicios'),
        ),
        migrations.AddField(
            model_name='detalleordencompra',
            name='orden',
            field=models.ForeignKey(to='compras.OrdenCompra'),
        ),
        migrations.AddField(
            model_name='detalleordencompra',
            name='producto',
            field=models.ForeignKey(to='productos.Producto', null=True),
        ),
        migrations.AddField(
            model_name='detalleconformidadservicio',
            name='detalle_orden_servicios',
            field=models.ForeignKey(to='compras.DetalleOrdenServicios', null=True),
        ),
        migrations.AddField(
            model_name='cotizacion',
            name='proveedor',
            field=models.ForeignKey(to='compras.Proveedor'),
        ),
        migrations.AddField(
            model_name='cotizacion',
            name='requerimiento',
            field=models.ForeignKey(to='requerimientos.Requerimiento', null=True),
        ),
        migrations.AddField(
            model_name='conformidadservicio',
            name='orden_servicios',
            field=models.ForeignKey(to='compras.OrdenServicios'),
        ),
        migrations.AlterUniqueTogether(
            name='cotizacion',
            unique_together=set([('proveedor', 'requerimiento')]),
        ),
    ]
