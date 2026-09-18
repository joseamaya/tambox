from django.urls import re_path
from django.contrib.auth.decorators import login_required
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
    re_path(r'^tablero/$', login_required(Tablero.as_view()), name="tablero"),
    re_path(r'^unidades_medida/$', login_required(ListadoUnidadesMedida.as_view()), name="unidades_medida"),
    re_path(r'^servicios/$', login_required(ListadoServicios.as_view()), name="servicios"),
    re_path(r'^grupos_productos/$', login_required(ListadoGruposProductos.as_view()), name="grupos_productos"),
    re_path(r'^productos/$', login_required(ListadoProductos.as_view()), name="productos"),
    re_path(r'^crear_servicio/$', login_required(CrearServicio.as_view()), name="crear_servicio"),
    re_path(r'^crear_unidad_medida/$', login_required(CrearUnidadMedida.as_view()), name="crear_unidad_medida"),
    re_path(r'^crear_grupo_productos/$', login_required(CrearGrupoProductos.as_view()), name="crear_grupo_productos"),
    re_path(r'^crear_producto/$', login_required(CrearProducto.as_view()), name="crear_producto"),
    re_path(r'^cargar_grupo_productos/$', login_required(CargarGrupoProductos.as_view()), name="cargar_grupo_productos"),
    re_path(r'^cargar_productos/$', login_required(CargarProductos.as_view()), name="cargar_productos"),
    re_path(r'^cargar_servicios/$', login_required(CargarServicios.as_view()), name="cargar_servicios"),
    re_path(r'^consulta_stock_producto/$', login_required(ConsultaStockProducto.as_view()), name="consulta_stock_producto"),
    re_path(r'^modificar_producto/(?P<pk>\d+)/$', login_required(ModificarProducto.as_view()), name="modificar_producto"),
    re_path(r'^modificar_grupo_productos/(?P<pk>\d+)/$', login_required(ModificarGrupoProductos.as_view()),
        name="modificar_grupo_productos"),
    re_path(r'^modificar_unidad_medida/(?P<pk>\d+)/$', login_required(ModificarUnidadMedida.as_view()),
        name="modificar_unidad_medida"),
    re_path(r'^modificar_servicio/(?P<pk>.+)/$', login_required(ModificarServicio.as_view()), name="modificar_servicio"),
    re_path(r'^busqueda_productos_descripcion/$', login_required(BusquedaProductosDescripcion.as_view()),
        name="busqueda_productos_descripcion"),
    re_path(r'^busqueda_productos_codigo/$', login_required(BusquedaProductosCodigo.as_view()),
        name="busqueda_productos_codigo"),
    re_path(r'^detalle_producto/(?P<pk>\d+)/$', login_required(DetalleProducto.as_view()), name="detalle_producto"),
    re_path(r'^detalle_grupo_productos/(?P<pk>\d+)/$', login_required(DetalleGrupoProductos.as_view()),
        name="detalle_grupo_productos"),
    re_path(r'^detalle_unidad_medida/(?P<pk>\d+)/$', login_required(DetalleUnidadMedida.as_view()),
        name="detalle_unidad_medida"),
    re_path(r'^detalle_servicio/(?P<pk>.+)/$', login_required(DetalleServicio.as_view()), name="detalle_servicio"),
    re_path(r'^listado_productos_grupo/(?P<grupo>.+)/$', login_required(ListadoProductosPorGrupo.as_view()),
        name="listado_productos_grupo"),
    re_path(r'^maestro_productos_excel/$', login_required(ReporteExcelProductos.as_view()), name="maestro_productos_excel"),
    re_path(r'^maestro_grupos_productos_excel/$', login_required(ReporteExcelGruposProductos.as_view()),
        name="maestro_grupos_productos_excel"),
    re_path(r'^maestro_unidades_medida_excel/$', login_required(ReporteExcelUnidadesMedida.as_view()),
        name="maestro_unidades_medida_excel"),
    re_path(r'^maestro_servicios_excel/$', login_required(ReporteExcelServicios.as_view()), name="maestro_servicios_excel"),
    re_path(r'^eliminar_unidad_medida/$', login_required(EliminarUnidadMedida.as_view()), name="eliminar_unidad_medida"),
    re_path(r'^eliminar_grupo_productos/$', login_required(EliminarGrupoProductos.as_view()),
        name="eliminar_grupo_productos"),
    re_path(r'^eliminar_producto/$', login_required(EliminarProducto.as_view()), name="eliminar_producto"),
    re_path(r'^eliminar_servicio/$', login_required(EliminarServicio.as_view()), name="eliminar_servicio"),
]
