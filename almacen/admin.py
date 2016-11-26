from django.contrib import admin
from almacen.models import Almacen, TipoMovimiento, ControlProductoAlmacen, \
    Kardex, Movimiento, DetalleMovimiento
from productos.models import Producto


class FilaKardexAdmin(admin.TabularInline):
    model = Kardex


class FilaProductoAdmin(admin.TabularInline):
    model = ControlProductoAlmacen


class FilaDetalleMovimientoAdmin(admin.TabularInline):
    model = DetalleMovimiento


class ProductosAlmacenAdmin(admin.ModelAdmin):
    inlines = [FilaProductoAdmin]


class KardexProductoAdmin(admin.ModelAdmin):
    inlines = [FilaKardexAdmin]


class DetallesMovimientoAdmin(admin.ModelAdmin):
    inlines = [FilaDetalleMovimientoAdmin]


admin.site.register(Movimiento, DetallesMovimientoAdmin)
admin.site.register(TipoMovimiento)
admin.site.register(Almacen, ProductosAlmacenAdmin)
admin.site.register(Producto, KardexProductoAdmin)
admin.site.register(Kardex)
