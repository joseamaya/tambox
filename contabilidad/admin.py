# -*- coding: utf-8 -*- 
from django.contrib import admin
from contabilidad.models import Empresa, TipoExistencia
from import_export import resources
from import_export.admin import ImportExportModelAdmin

class EmpresaResource(resources.ModelResource):
    class Meta:
        model = Empresa

class EmpresaAdmin(ImportExportModelAdmin,admin.ModelAdmin):
    search_fields = ['razon_social','ruc','provincia']
    list_display = ('razon_social','ruc','lugar','distrito','provincia')
    resource_class = EmpresaResource

class TipoExistenciaResource(resources.ModelResource):
    class Meta:
        model = TipoExistencia

class TipoExistenciaAdmin(ImportExportModelAdmin,admin.ModelAdmin):
    search_fields = ['codigo_sunat','descripcion']
    list_display = ('codigo_sunat','descripcion')
    resource_class = TipoExistenciaResource


# Register your models here.
admin.site.register(Empresa,EmpresaAdmin)
admin.site.register(TipoExistencia,TipoExistenciaAdmin)