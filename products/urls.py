from django.urls import re_path
from products.views import Dashboard, UnitOfMeasureList, ServiceList, \
    ProductGroupList, ProductList, ServiceCreate, UnitOfMeasureCreate, \
    ProductGroupCreate, ProductCreate, ProductImport, ServiceImport, \
    ProductUpdate, ProductGroupUpdate, UnitOfMeasureUpdate, \
    ServiceUpdate, ProductDescriptionSearch, ProductCodeSearch, \
    ProductDetail, ProductGroupDetail, UnitOfMeasureDetail, ServiceDetail, \
    ProductExcelReport, ProductGroupExcelReport, \
    UnitOfMeasureExcelReport, ServiceExcelReport, UnitOfMeasureDelete, \
    ProductGroupDelete, ProductDelete, ServiceDelete, \
    ProductGroupImport, ProductListByGroup, ProductStockQuery

app_name = 'products'

urlpatterns = [
    re_path(r'^dashboard/$', Dashboard.as_view(), name="dashboard"),
    re_path(r'^unit_of_measure_list/$', UnitOfMeasureList.as_view(), name="unit_of_measure_list"),
    re_path(r'^service_list/$', ServiceList.as_view(), name="service_list"),
    re_path(r'^product_group_list/$', ProductGroupList.as_view(), name="product_group_list"),
    re_path(r'^product_list/$', ProductList.as_view(), name="product_list"),
    re_path(r'^service_create/$', ServiceCreate.as_view(), name="service_create"),
    re_path(r'^unit_of_measure_create/$', UnitOfMeasureCreate.as_view(), name="unit_of_measure_create"),
    re_path(r'^product_group_create/$', ProductGroupCreate.as_view(), name="product_group_create"),
    re_path(r'^product_create/$', ProductCreate.as_view(), name="product_create"),
    re_path(r'^product_group_import/$', ProductGroupImport.as_view(), name="product_group_import"),
    re_path(r'^product_import/$', ProductImport.as_view(), name="product_import"),
    re_path(r'^service_import/$', ServiceImport.as_view(), name="service_import"),
    re_path(r'^product_stock_query/$', ProductStockQuery.as_view(), name="product_stock_query"),
    re_path(r'^product_update/(?P<pk>.+)/$', ProductUpdate.as_view(), name="product_update"),
    re_path(r'^product_group_update/(?P<pk>.+)/$', ProductGroupUpdate.as_view(),
        name="product_group_update"),
    re_path(r'^unit_of_measure_update/(?P<pk>\d+)/$', UnitOfMeasureUpdate.as_view(),
        name="unit_of_measure_update"),
    re_path(r'^service_update/(?P<pk>.+)/$', ServiceUpdate.as_view(), name="service_update"),
    re_path(r'^product_description_search/$', ProductDescriptionSearch.as_view(),
        name="product_description_search"),
    re_path(r'^product_code_search/$', ProductCodeSearch.as_view(),
        name="product_code_search"),
    re_path(r'^product_detail/(?P<pk>.+)/$', ProductDetail.as_view(), name="product_detail"),
    re_path(r'^product_group_detail/(?P<pk>.+)/$', ProductGroupDetail.as_view(),
        name="product_group_detail"),
    re_path(r'^unit_of_measure_detail/(?P<pk>\d+)/$', UnitOfMeasureDetail.as_view(),
        name="unit_of_measure_detail"),
    re_path(r'^service_detail/(?P<pk>.+)/$', ServiceDetail.as_view(), name="service_detail"),
    re_path(r'^product_list_by_group/(?P<group>.+)/$', ProductListByGroup.as_view(),
        name="product_list_by_group"),
    re_path(r'^product_excel_report/$', ProductExcelReport.as_view(), name="product_excel_report"),
    re_path(r'^product_group_excel_report/$', ProductGroupExcelReport.as_view(),
        name="product_group_excel_report"),
    re_path(r'^unit_of_measure_excel_report/$', UnitOfMeasureExcelReport.as_view(),
        name="unit_of_measure_excel_report"),
    re_path(r'^service_excel_report/$', ServiceExcelReport.as_view(), name="service_excel_report"),
    re_path(r'^unit_of_measure_delete/$', UnitOfMeasureDelete.as_view(), name="unit_of_measure_delete"),
    re_path(r'^product_group_delete/$', ProductGroupDelete.as_view(),
        name="product_group_delete"),
    re_path(r'^product_delete/$', ProductDelete.as_view(), name="product_delete"),
    re_path(r'^service_delete/$', ServiceDelete.as_view(), name="service_delete"),
]
