from django.contrib import admin

from requerimientos.models import RequirementDetail, Requirement, \
    RequirementApproval


# Register your models here.
class FilaDetalleRequerimientoAdmin(admin.TabularInline):
    model = RequirementDetail


class DetallesRequerimientoAdmin(admin.ModelAdmin):
    inlines = [FilaDetalleRequerimientoAdmin]


admin.site.register(Requirement, DetallesRequerimientoAdmin)
admin.site.register(RequirementApproval)
