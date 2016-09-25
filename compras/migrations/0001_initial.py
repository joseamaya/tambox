# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.utils.timezone
import model_utils.fields


class Migration(migrations.Migration):

    dependencies = [
        ('contabilidad', '0001_initial'),
        ('administracion', '0001_initial'),
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
            name='DetalleRequerimiento',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', model_utils.fields.AutoCreatedField(default=django.utils.timezone.now, verbose_name='created', editable=False)),
                ('modified', model_utils.fields.AutoLastModifiedField(default=django.utils.timezone.now, verbose_name='modified', editable=False)),
                ('nro_detalle', models.IntegerField()),
                ('otro', models.CharField(max_length=150, null=True)),
                ('unidad', models.CharField(max_length=20, null=True)),
                ('uso', models.CharField(max_length=50, null=True)),
                ('cantidad', models.DecimalField(max_digits=15, decimal_places=5)),
                ('cantidad_comprada', models.DecimalField(default=0, max_digits=15, decimal_places=5)),
                ('cantidad_atendida', models.DecimalField(default=0, max_digits=15, decimal_places=5)),
                ('estado', models.CharField(default=b'PEND', max_length=20, choices=[(b'PEND', b'PENDIENTE'), (b'COTIZ', b'COTIZADO'), (b'COTIZ_PARC', b'COTIZADO PARCIALMENTE'), (b'PED', b'PEDIDO'), (b'PED_PARC', b'PEDIDO PARCIALMENTE'), (b'ATEN', b'ATENDIDO'), (b'ATEN_PARC', b'ATENDIDO PARCIALMENTE'), (b'CANC', b'CANCELADO')])),
            ],
            options={
                'ordering': ['nro_detalle'],
                'permissions': (('can_view', 'Can view Detalle Requerimiento'),),
            },
        ),
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
        migrations.CreateModel(
            name='GrupoProductos',
            fields=[
                ('created', model_utils.fields.AutoCreatedField(default=django.utils.timezone.now, verbose_name='created', editable=False)),
                ('modified', model_utils.fields.AutoLastModifiedField(default=django.utils.timezone.now, verbose_name='modified', editable=False)),
                ('codigo', models.CharField(max_length=6, serialize=False, primary_key=True)),
                ('descripcion', models.CharField(max_length=100)),
                ('estado', models.BooleanField(default=True)),
                ('ctacontable', models.ForeignKey(to='contabilidad.CuentaContable')),
            ],
            options={
                'permissions': (('ver_detalle_grupo_productos', 'Puede ver detalle Grupo de Productos'), ('ver_tabla_grupos_productos', 'Puede ver tabla Grupos de Productos'), ('ver_reporte_grupo_productos_excel', 'Puede ver Reporte de grupo de productos en excel')),
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
                ('forma_pago', models.ForeignKey(to='compras.FormaPago')),
            ],
            options={
                'permissions': (('ver_detalle_orden_compra', 'Puede ver detalle de Orden de Compra'), ('ver_tabla_ordenes_compra', 'Puede ver tabla Ordenes de Compra'), ('ver_reporte_ordenes_compra_excel', 'Puede ver Reporte de Ordenes de Compra en excel'), ('puede_hacer_transferencia_orden_compra', 'Puede hacer transferencia de Orden de Compra')),
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
                ('forma_pago', models.ForeignKey(to='compras.FormaPago')),
            ],
            options={
                'permissions': (('ver_detalle_orden_servicios', 'Puede ver detalle de Orden de Servicios'), ('ver_tabla_ordenes_servicios', 'Puede ver tabla de Ordenes de Servicios'), ('ver_reporte_ordenes_servicios_excel', 'Puede ver Reporte de Ordenes de Servicios en excel')),
            },
        ),
        migrations.CreateModel(
            name='Producto',
            fields=[
                ('created', model_utils.fields.AutoCreatedField(default=django.utils.timezone.now, verbose_name='created', editable=False)),
                ('modified', model_utils.fields.AutoLastModifiedField(default=django.utils.timezone.now, verbose_name='modified', editable=False)),
                ('codigo', models.CharField(max_length=10, serialize=False, primary_key=True)),
                ('descripcion', models.CharField(unique=True, max_length=100)),
                ('desc_abreviada', models.CharField(max_length=40, blank=True)),
                ('es_servicio', models.BooleanField(default=False)),
                ('marca', models.CharField(max_length=40, blank=True)),
                ('modelo', models.CharField(max_length=40, blank=True)),
                ('precio', models.DecimalField(default=0, max_digits=15, decimal_places=5)),
                ('stock', models.DecimalField(default=0, max_digits=15, decimal_places=5)),
                ('stock_minimo', models.DecimalField(default=0, max_digits=15, decimal_places=5)),
                ('imagen', models.ImageField(default=b'productos/sinimagen.png', upload_to=b'productos')),
                ('estado', models.BooleanField(default=True)),
                ('grupo_productos', models.ForeignKey(to='compras.GrupoProductos')),
            ],
            options={
                'permissions': (('cargar_productos', 'Puede cargar Productos desde un archivo externo'), ('ver_detalle_producto', 'Puede ver detalle de Productos'), ('ver_tabla_productos', 'Puede ver tabla Productos'), ('ver_reporte_productos_excel', 'Puede ver Reporte de Productos en excel'), ('puede_hacer_busqueda_producto', 'Puede hacer busqueda Producto')),
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
        migrations.CreateModel(
            name='Requerimiento',
            fields=[
                ('created', model_utils.fields.AutoCreatedField(default=django.utils.timezone.now, verbose_name='created', editable=False)),
                ('modified', model_utils.fields.AutoLastModifiedField(default=django.utils.timezone.now, verbose_name='modified', editable=False)),
                ('codigo', models.CharField(max_length=12, serialize=False, primary_key=True)),
                ('motivo', models.CharField(max_length=100)),
                ('mes', models.IntegerField(choices=[(1, b'ENERO'), (2, b'FEBRERO'), (3, b'MARZO'), (4, b'ABRIL'), (5, b'MAYO'), (6, b'JUNIO'), (7, b'JULIO'), (8, b'AGOSTO'), (9, b'SETIEMBRE'), (10, b'OCTUBRE'), (11, b'NOVIEMBRE'), (12, b'DICIEMBRE')])),
                ('observaciones', models.TextField()),
                ('informe', models.FileField(null=True, upload_to=b'informes')),
                ('entrega_directa_solicitante', models.BooleanField(default=False)),
                ('estado', models.CharField(default=b'PEND', max_length=20, choices=[(b'PEND', b'PENDIENTE'), (b'COTIZ', b'COTIZADO'), (b'COTIZ_PARC', b'COTIZADO PARCIALMENTE'), (b'PED', b'PEDIDO'), (b'PED_PARC', b'PEDIDO PARCIALMENTE'), (b'ATEN', b'ATENDIDO'), (b'ATEN_PARC', b'ATENDIDO PARCIALMENTE'), (b'CANC', b'CANCELADO')])),
            ],
            options={
                'permissions': (('ver_detalle_requerimiento', 'Puede ver detalle de Requerimiento'), ('ver_tabla_requerimientos', 'Puede ver tabla de Requerimientos'), ('ver_reporte_requerimientos_excel', 'Puede ver Reporte de Requerimientos en excel'), ('puede_hacer_transferencia_requerimiento', 'Puede hacer transferencia de Requerimiento')),
            },
        ),
        migrations.CreateModel(
            name='UnidadMedida',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', model_utils.fields.AutoCreatedField(default=django.utils.timezone.now, verbose_name='created', editable=False)),
                ('modified', model_utils.fields.AutoLastModifiedField(default=django.utils.timezone.now, verbose_name='modified', editable=False)),
                ('codigo', models.CharField(unique=True, max_length=5)),
                ('descripcion', models.CharField(max_length=50)),
                ('estado', models.BooleanField(default=True)),
            ],
            options={
                'ordering': ['codigo'],
                'permissions': (('ver_detalle_unidad_medida', 'Puede ver detalle Unidad de Medida'), ('ver_tabla_unidades_medida', 'Puede ver tabla de unidades de medida'), ('ver_reporte_unidades_medida_excel', 'Puede ver Reporte Unidades de Medida en excel')),
            },
        ),
        migrations.CreateModel(
            name='AprobacionRequerimiento',
            fields=[
                ('created', model_utils.fields.AutoCreatedField(default=django.utils.timezone.now, verbose_name='created', editable=False)),
                ('modified', model_utils.fields.AutoLastModifiedField(default=django.utils.timezone.now, verbose_name='modified', editable=False)),
                ('requerimiento', models.OneToOneField(primary_key=True, serialize=False, to='compras.Requerimiento')),
                ('estado', models.CharField(default=b'PEND', max_length=20, choices=[(b'PEND', b'PENDIENTE'), (b'APROB_JEF', b'APROBADO JEFATURA'), (b'DESAP_JEF', b'DESAPROBADO JEFATURA'), (b'APROB_GER_INM', b'APROBADO GERENCIA INMEDIATA'), (b'DESAP_GER_INM', b'DESAPROBADO GERENCIA INMEDIATA'), (b'APROB_GER_ADM', b'APROBADO GERENCIA ADMINISTRACION'), (b'DESAP_GER_ADM', b'DESAPROBADO GERENCIA ADMINISTRACION'), (b'APROB_LOG', b'APROBADO LOGISTICA'), (b'DESAP_LOG', b'DESAPROBADO LOGISTICA'), (b'APROB_PRES', b'APROBADO PRESUPUESTO'), (b'DESAP_PRES', b'DESAPROBADO PRESUPUESTO')])),
                ('motivo_desaprobacion', models.TextField(default=b'')),
            ],
            options={
                'permissions': (('ver_tabla_aprobacion_requerimientos', 'Puede ver tabla de Aprobaci\xf3n de Requerimientos'), ('ver_reporte_aprobacion_requerimientos_excel', 'Puede ver Reporte de Aprobaci\xf3n de Requerimientos en excel')),
            },
        ),
        migrations.AddField(
            model_name='requerimiento',
            name='oficina',
            field=models.ForeignKey(to='administracion.Oficina'),
        ),
        migrations.AddField(
            model_name='requerimiento',
            name='solicitante',
            field=models.ForeignKey(to='administracion.Trabajador'),
        ),
        migrations.AddField(
            model_name='proveedor',
            name='representantes',
            field=models.ManyToManyField(to='compras.RepresentanteLegal'),
        ),
        migrations.AddField(
            model_name='producto',
            name='unidad_medida',
            field=models.ForeignKey(to='compras.UnidadMedida', null=True),
        ),
        migrations.AddField(
            model_name='detallerequerimiento',
            name='producto',
            field=models.ForeignKey(to='compras.Producto', null=True),
        ),
        migrations.AddField(
            model_name='detallerequerimiento',
            name='requerimiento',
            field=models.ForeignKey(to='compras.Requerimiento'),
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
            model_name='detallecotizacion',
            name='detalle_requerimiento',
            field=models.ForeignKey(to='compras.DetalleRequerimiento', null=True),
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
            field=models.ForeignKey(to='compras.Requerimiento', null=True),
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
