from django.urls import re_path
from productos.views import Dashboard, UnitOfMeasureList, ServiceList, \
    ProductGroupList, ProductList, ServiceCreate, UnitOfMeasureCreate, \
    ProductGroupCreate, ProductCreate, ProductImport, ServiceImport, \
    ProductUpdate, ProductGroupUpdate, UnitOfMeasureUpdate, \
    ServiceUpdate, ProductDescriptionSearch, ProductCodeSearch, \
    ProductDetail, ProductGroupDetail, UnitOfMeasureDetail, ServiceDetail, \
    ProductExcelReport, ProductGroupExcelReport, \
    UnitOfMeasureExcelReport, ServiceExcelReport, UnitOfMeasureDelete, \
    ProductGroupDelete, ProductDelete, ServiceDelete, \
    ProductGroupImport, ProductListByGroup, ProductStockQuery

app_name = 'productos'

urlpatterns = [
    re_path(r'^tablero/$', Dashboard.as_view(), name="tablero"),
    re_path(r'^unidades_medida/$', UnitOfMeasureList.as_view(), name="unidades_medida"),
    re_path(r'^servicios/$', ServiceList.as_view(), name="servicios"),
    re_path(r'^grupos_productos/$', ProductGroupList.as_view(), name="grupos_productos"),
    re_path(r'^productos/$', ProductList.as_view(), name="productos"),
    re_path(r'^crear_servicio/$', ServiceCreate.as_view(), name="crear_servicio"),
    re_path(r'^crear_unidad_medida/$', UnitOfMeasureCreate.as_view(), name="crear_unidad_medida"),
    re_path(r'^crear_grupo_productos/$', ProductGroupCreate.as_view(), name="crear_grupo_productos"),
    re_path(r'^crear_producto/$', ProductCreate.as_view(), name="crear_producto"),
    re_path(r'^cargar_grupo_productos/$', ProductGroupImport.as_view(), name="cargar_grupo_productos"),
    re_path(r'^cargar_productos/$', ProductImport.as_view(), name="cargar_productos"),
    re_path(r'^cargar_servicios/$', ServiceImport.as_view(), name="cargar_servicios"),
    re_path(r'^consulta_stock_producto/$', ProductStockQuery.as_view(), name="consulta_stock_producto"),
    re_path(r'^modificar_producto/(?P<pk>.+)/$', ProductUpdate.as_view(), name="modificar_producto"),
    re_path(r'^modificar_grupo_productos/(?P<pk>.+)/$', ProductGroupUpdate.as_view(),
        name="modificar_grupo_productos"),
    re_path(r'^modificar_unidad_medida/(?P<pk>\d+)/$', UnitOfMeasureUpdate.as_view(),
        name="modificar_unidad_medida"),
    re_path(r'^modificar_servicio/(?P<pk>.+)/$', ServiceUpdate.as_view(), name="modificar_servicio"),
    re_path(r'^busqueda_productos_description/$', ProductDescriptionSearch.as_view(),
        name="busqueda_productos_description"),
    re_path(r'^busqueda_productos_code/$', ProductCodeSearch.as_view(),
        name="busqueda_productos_code"),
    re_path(r'^detalle_producto/(?P<pk>.+)/$', ProductDetail.as_view(), name="detalle_producto"),
    re_path(r'^detalle_grupo_productos/(?P<pk>.+)/$', ProductGroupDetail.as_view(),
        name="detalle_grupo_productos"),
    re_path(r'^detalle_unidad_medida/(?P<pk>\d+)/$', UnitOfMeasureDetail.as_view(),
        name="detalle_unidad_medida"),
    re_path(r'^detalle_servicio/(?P<pk>.+)/$', ServiceDetail.as_view(), name="detalle_servicio"),
    re_path(r'^listado_productos_grupo/(?P<grupo>.+)/$', ProductListByGroup.as_view(),
        name="listado_productos_grupo"),
    re_path(r'^maestro_productos_excel/$', ProductExcelReport.as_view(), name="maestro_productos_excel"),
    re_path(r'^maestro_grupos_productos_excel/$', ProductGroupExcelReport.as_view(),
        name="maestro_grupos_productos_excel"),
    re_path(r'^maestro_unidades_medida_excel/$', UnitOfMeasureExcelReport.as_view(),
        name="maestro_unidades_medida_excel"),
    re_path(r'^maestro_servicios_excel/$', ServiceExcelReport.as_view(), name="maestro_servicios_excel"),
    re_path(r'^eliminar_unidad_medida/$', UnitOfMeasureDelete.as_view(), name="eliminar_unidad_medida"),
    re_path(r'^eliminar_grupo_productos/$', ProductGroupDelete.as_view(),
        name="eliminar_grupo_productos"),
    re_path(r'^eliminar_producto/$', ProductDelete.as_view(), name="eliminar_producto"),
    re_path(r'^eliminar_servicio/$', ServiceDelete.as_view(), name="eliminar_servicio"),
]
