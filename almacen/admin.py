from django.contrib import admin
from almacen.models import Almacen, TipoMovimiento, ControlProductoAlmacen, \
    Kardex, Movimiento, DetalleMovimiento
from productos.models import Producto
from import_export import resources
from import_export.admin import ImportExportModelAdmin


class FilaKardexAdmin(admin.TabularInline):
    model = Kardex


class FilaProductoAdmin(admin.TabularInline):
    model = ControlProductoAlmacen


class FilaDetalleMovimientoAdmin(admin.TabularInline):
    model = DetalleMovimiento


class AlmacenResources(resources.ModelResource):
    class Meta:
        model = Almacen


class ProductosAlmacenAdmin(ImportExportModelAdmin, admin.ModelAdmin):
    inlines = [FilaProductoAdmin]
    list_display = ('codigo', 'descripcion')
    search_fields = ['codigo', 'descripcion']
    resource_class = AlmacenResources


class KardexResources(resources.ModelResource):
    class Meta:
        model = Kardex


class KardexAdmin(ImportExportModelAdmin, admin.ModelAdmin):
    resource_class = KardexResources


class ProductoResources(resources.ModelResource):
    class Meta:
        model = Producto


class KardexProductoAdmin(ImportExportModelAdmin, admin.ModelAdmin):
    inlines = [FilaKardexAdmin]
    list_display = ('codigo', 'grupo_productos', 'descripcion', 'es_servicio', 'unidad_medida')
    resource_class = ProductoResources


class MovimientoResources(resources.ModelResource):
    class Meta:
        model = Movimiento


class DetallesMovimientoAdmin(ImportExportModelAdmin, admin.ModelAdmin):
    inlines = [FilaDetalleMovimientoAdmin]
    list_display = ('id_movimiento', 'tipo_movimiento', 'referencia', 'pedido', 'serie', 'oficina')
    resource_class = MovimientoResources


admin.site.register(Movimiento, DetallesMovimientoAdmin)
admin.site.register(TipoMovimiento)
admin.site.register(Almacen, ProductosAlmacenAdmin)
admin.site.register(Producto, KardexProductoAdmin)
admin.site.register(Kardex, KardexAdmin)
