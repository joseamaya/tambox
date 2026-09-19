from django.urls import re_path
from productos.views import Tablero, ListadoUnidadesMedida, ListadoServicios, \
    ListadoGruposProductos, ListadoProductos, CrearServicio, CrearUnidadMedida, \
    CrearGrupoProductos, CrearProducto, CargarProductos, CargarServicios, \
    ModificarProducto, ModificarGrupoProductos, ModificarUnidadMedida, \
    ModificarServicio, BusquedaProductosDescripcion, BusquedaProductosCodigo, \
    DetalleProducto, DetalleGrupoProductos, DetalleUnidadMedida, DetalleServicio, \
    ReporteExcelProductos, ReporteExcelGruposProductos, \
    ReporteExcelUnidadesMedida, ReporteExcelServicios, EliminarUnidadMedida, \
    EliminarGrupoProductos, EliminarProducto, EliminarServicio, \
    CargarGrupoProductos, ListadoProductosPorGrupo, ConsultaStockProducto

app_name = 'productos'

urlpatterns = [
    re_path(r'^tablero/$', Tablero.as_view(), name="tablero"),
    re_path(r'^unidades_medida/$', ListadoUnidadesMedida.as_view(), name="unidades_medida"),
    re_path(r'^servicios/$', ListadoServicios.as_view(), name="servicios"),
    re_path(r'^grupos_productos/$', ListadoGruposProductos.as_view(), name="grupos_productos"),
    re_path(r'^productos/$', ListadoProductos.as_view(), name="productos"),
    re_path(r'^crear_servicio/$', CrearServicio.as_view(), name="crear_servicio"),
    re_path(r'^crear_unidad_medida/$', CrearUnidadMedida.as_view(), name="crear_unidad_medida"),
    re_path(r'^crear_grupo_productos/$', CrearGrupoProductos.as_view(), name="crear_grupo_productos"),
    re_path(r'^crear_producto/$', CrearProducto.as_view(), name="crear_producto"),
    re_path(r'^cargar_grupo_productos/$', CargarGrupoProductos.as_view(), name="cargar_grupo_productos"),
    re_path(r'^cargar_productos/$', CargarProductos.as_view(), name="cargar_productos"),
    re_path(r'^cargar_servicios/$', CargarServicios.as_view(), name="cargar_servicios"),
    re_path(r'^consulta_stock_producto/$', ConsultaStockProducto.as_view(), name="consulta_stock_producto"),
    re_path(r'^modificar_producto/(?P<pk>\d+)/$', ModificarProducto.as_view(), name="modificar_producto"),
    re_path(r'^modificar_grupo_productos/(?P<pk>\d+)/$', ModificarGrupoProductos.as_view(),
        name="modificar_grupo_productos"),
    re_path(r'^modificar_unidad_medida/(?P<pk>\d+)/$', ModificarUnidadMedida.as_view(),
        name="modificar_unidad_medida"),
    re_path(r'^modificar_servicio/(?P<pk>.+)/$', ModificarServicio.as_view(), name="modificar_servicio"),
    re_path(r'^busqueda_productos_descripcion/$', BusquedaProductosDescripcion.as_view(),
        name="busqueda_productos_descripcion"),
    re_path(r'^busqueda_productos_codigo/$', BusquedaProductosCodigo.as_view(),
        name="busqueda_productos_codigo"),
    re_path(r'^detalle_producto/(?P<pk>\d+)/$', DetalleProducto.as_view(), name="detalle_producto"),
    re_path(r'^detalle_grupo_productos/(?P<pk>\d+)/$', DetalleGrupoProductos.as_view(),
        name="detalle_grupo_productos"),
    re_path(r'^detalle_unidad_medida/(?P<pk>\d+)/$', DetalleUnidadMedida.as_view(),
        name="detalle_unidad_medida"),
    re_path(r'^detalle_servicio/(?P<pk>.+)/$', DetalleServicio.as_view(), name="detalle_servicio"),
    re_path(r'^listado_productos_grupo/(?P<grupo>.+)/$', ListadoProductosPorGrupo.as_view(),
        name="listado_productos_grupo"),
    re_path(r'^maestro_productos_excel/$', ReporteExcelProductos.as_view(), name="maestro_productos_excel"),
    re_path(r'^maestro_grupos_productos_excel/$', ReporteExcelGruposProductos.as_view(),
        name="maestro_grupos_productos_excel"),
    re_path(r'^maestro_unidades_medida_excel/$', ReporteExcelUnidadesMedida.as_view(),
        name="maestro_unidades_medida_excel"),
    re_path(r'^maestro_servicios_excel/$', ReporteExcelServicios.as_view(), name="maestro_servicios_excel"),
    re_path(r'^eliminar_unidad_medida/$', EliminarUnidadMedida.as_view(), name="eliminar_unidad_medida"),
    re_path(r'^eliminar_grupo_productos/$', EliminarGrupoProductos.as_view(),
        name="eliminar_grupo_productos"),
    re_path(r'^eliminar_producto/$', EliminarProducto.as_view(), name="eliminar_producto"),
    re_path(r'^eliminar_servicio/$', EliminarServicio.as_view(), name="eliminar_servicio"),
]
