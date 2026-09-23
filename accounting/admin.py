# -*- coding: utf-8 -*- 
from django.contrib import admin
from accounting.models import Company, StockType
from import_export import resources
from import_export.admin import ImportExportModelAdmin


class CompanyResource(resources.ModelResource):
    class Meta:
        model = Company


class CompanyAdmin(ImportExportModelAdmin, admin.ModelAdmin):
    search_fields = ['business_name', 'tax_id', 'province']
    list_display = ('business_name', 'tax_id', 'place', 'district', 'province')
    resource_class = CompanyResource


class StockTypeResource(resources.ModelResource):
    class Meta:
        model = StockType


class StockTypeAdmin(ImportExportModelAdmin, admin.ModelAdmin):
    search_fields = ['sunat_code', 'description']
    list_display = ('sunat_code', 'description')
    resource_class = StockTypeResource


# Register your models here.
admin.site.register(Company, CompanyAdmin)
admin.site.register(StockType, StockTypeAdmin)
