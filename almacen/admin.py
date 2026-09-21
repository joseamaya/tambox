from django.contrib import admin
from almacen.models import Warehouse, MovementType, WarehouseProductControl, \
    Kardex, Movement, MovementDetail
from productos.models import Product
from import_export import resources
from import_export.admin import ImportExportModelAdmin


class FilaKardexAdmin(admin.TabularInline):
    model = Kardex


class FilaProductoAdmin(admin.TabularInline):
    model = WarehouseProductControl


class FilaDetalleMovimientoAdmin(admin.TabularInline):
    model = MovementDetail


class AlmacenResources(resources.ModelResource):
    class Meta:
        model = Warehouse


class ProductosAlmacenAdmin(ImportExportModelAdmin, admin.ModelAdmin):
    inlines = [FilaProductoAdmin]
    list_display = ('code', 'description')
    search_fields = ['code', 'description']
    resource_class = AlmacenResources


class KardexResources(resources.ModelResource):
    class Meta:
        model = Kardex


class KardexAdmin(ImportExportModelAdmin, admin.ModelAdmin):
    resource_class = KardexResources


class ProductoResources(resources.ModelResource):
    class Meta:
        model = Product


class KardexProductoAdmin(ImportExportModelAdmin, admin.ModelAdmin):
    inlines = [FilaKardexAdmin]
    list_display = ('code', 'product_group', 'description', 'is_service', 'unit_of_measure')
    resource_class = ProductoResources


class MovimientoResources(resources.ModelResource):
    class Meta:
        model = Movement


class DetallesMovimientoAdmin(ImportExportModelAdmin, admin.ModelAdmin):
    inlines = [FilaDetalleMovimientoAdmin]
    list_display = ('movement_id', 'movement_type', 'reference', 'order', 'series', 'office')
    resource_class = MovimientoResources


admin.site.register(Movement, DetallesMovimientoAdmin)
admin.site.register(MovementType)
admin.site.register(Warehouse, ProductosAlmacenAdmin)
admin.site.register(Product, KardexProductoAdmin)
admin.site.register(Kardex, KardexAdmin)
