# -*- coding: utf-8 -*- 
from django.contrib import admin
from contabilidad.models import Company, StockType
from import_export import resources
from import_export.admin import ImportExportModelAdmin


class EmpresaResource(resources.ModelResource):
    class Meta:
        model = Company


class EmpresaAdmin(ImportExportModelAdmin, admin.ModelAdmin):
    search_fields = ['business_name', 'tax_id', 'province']
    list_display = ('business_name', 'tax_id', 'place', 'district', 'province')
    resource_class = EmpresaResource


class TipoExistenciaResource(resources.ModelResource):
    class Meta:
        model = StockType


class TipoExistenciaAdmin(ImportExportModelAdmin, admin.ModelAdmin):
    search_fields = ['sunat_code', 'description']
    list_display = ('sunat_code', 'description')
    resource_class = TipoExistenciaResource


# Register your models here.
admin.site.register(Company, EmpresaAdmin)
admin.site.register(StockType, TipoExistenciaAdmin)
