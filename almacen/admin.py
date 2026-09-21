from django.contrib import admin
from almacen.models import Warehouse, MovementType, WarehouseProductControl, \
    Kardex, Movement, MovementDetail
from productos.models import Product
from import_export import resources
from import_export.admin import ImportExportModelAdmin


class KardexRowAdmin(admin.TabularInline):
    model = Kardex


class ProductRowAdmin(admin.TabularInline):
    model = WarehouseProductControl


class MovementDetailRowAdmin(admin.TabularInline):
    model = MovementDetail


class WarehouseResources(resources.ModelResource):
    class Meta:
        model = Warehouse


class WarehouseProductsAdmin(ImportExportModelAdmin, admin.ModelAdmin):
    inlines = [ProductRowAdmin]
    list_display = ('code', 'description')
    search_fields = ['code', 'description']
    resource_class = WarehouseResources


class KardexResources(resources.ModelResource):
    class Meta:
        model = Kardex


class KardexAdmin(ImportExportModelAdmin, admin.ModelAdmin):
    resource_class = KardexResources


class ProductResources(resources.ModelResource):
    class Meta:
        model = Product


class KardexProductAdmin(ImportExportModelAdmin, admin.ModelAdmin):
    inlines = [KardexRowAdmin]
    list_display = ('code', 'product_group', 'description', 'is_service', 'unit_of_measure')
    resource_class = ProductResources


class MovementResources(resources.ModelResource):
    class Meta:
        model = Movement


class MovementDetailsAdmin(ImportExportModelAdmin, admin.ModelAdmin):
    inlines = [MovementDetailRowAdmin]
    list_display = ('movement_id', 'movement_type', 'reference', 'order', 'series', 'office')
    resource_class = MovementResources


admin.site.register(Movement, MovementDetailsAdmin)
admin.site.register(MovementType)
admin.site.register(Warehouse, WarehouseProductsAdmin)
admin.site.register(Product, KardexProductAdmin)
admin.site.register(Kardex, KardexAdmin)
