from django.contrib import admin

from requerimientos.models import DetalleRequerimiento, Requerimiento,\
    AprobacionRequerimiento

# Register your models here.
class FilaDetalleRequerimientoAdmin(admin.TabularInline):
    model = DetalleRequerimiento

class DetallesRequerimientoAdmin(admin.ModelAdmin):
    inlines = [FilaDetalleRequerimientoAdmin]

admin.site.register(Requerimiento,DetallesRequerimientoAdmin)
admin.site.register(AprobacionRequerimiento)