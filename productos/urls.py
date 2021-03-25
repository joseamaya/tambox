from django.conf.urls import url
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

urlpatterns = [
    url(r'^tablero/$', login_required(Tablero.as_view()), name="tablero"),
    url(r'^unidades_medida/$', login_required(ListadoUnidadesMedida.as_view()), name="unidades_medida"),
    url(r'^servicios/$', login_required(ListadoServicios.as_view()), name="servicios"),
    url(r'^grupos_productos/$', login_required(ListadoGruposProductos.as_view()), name="grupos_productos"),
    url(r'^productos/$', login_required(ListadoProductos.as_view()), name="productos"),
    url(r'^crear_servicio/$', login_required(CrearServicio.as_view()), name="crear_servicio"),
    url(r'^crear_unidad_medida/$', login_required(CrearUnidadMedida.as_view()), name="crear_unidad_medida"),
    url(r'^crear_grupo_productos/$', login_required(CrearGrupoProductos.as_view()), name="crear_grupo_productos"),
    url(r'^crear_producto/$', login_required(CrearProducto.as_view()), name="crear_producto"),
    url(r'^cargar_grupo_productos/$', login_required(CargarGrupoProductos.as_view()), name="cargar_grupo_productos"),
    url(r'^cargar_productos/$', login_required(CargarProductos.as_view()), name="cargar_productos"),
    url(r'^cargar_servicios/$', login_required(CargarServicios.as_view()), name="cargar_servicios"),
    url(r'^consulta_stock_producto/$', login_required(ConsultaStockProducto.as_view()), name="consulta_stock_producto"),
    url(r'^modificar_producto/(?P<pk>\d+)/$', login_required(ModificarProducto.as_view()), name="modificar_producto"),
    url(r'^modificar_grupo_productos/(?P<pk>\d+)/$', login_required(ModificarGrupoProductos.as_view()),
        name="modificar_grupo_productos"),
    url(r'^modificar_unidad_medida/(?P<pk>\d+)/$', login_required(ModificarUnidadMedida.as_view()),
        name="modificar_unidad_medida"),
    url(r'^modificar_servicio/(?P<pk>.+)/$', login_required(ModificarServicio.as_view()), name="modificar_servicio"),
    url(r'^busqueda_productos_descripcion/$', login_required(BusquedaProductosDescripcion.as_view()),
        name="busqueda_productos_descripcion"),
    url(r'^busqueda_productos_codigo/$', login_required(BusquedaProductosCodigo.as_view()),
        name="busqueda_productos_codigo"),
    url(r'^detalle_producto/(?P<pk>\d+)/$', login_required(DetalleProducto.as_view()), name="detalle_producto"),
    url(r'^detalle_grupo_productos/(?P<pk>\d+)/$', login_required(DetalleGrupoProductos.as_view()),
        name="detalle_grupo_productos"),
    url(r'^detalle_unidad_medida/(?P<pk>\d+)/$', login_required(DetalleUnidadMedida.as_view()),
        name="detalle_unidad_medida"),
    url(r'^detalle_servicio/(?P<pk>.+)/$', login_required(DetalleServicio.as_view()), name="detalle_servicio"),
    url(r'^listado_productos_grupo/(?P<grupo>.+)/$', login_required(ListadoProductosPorGrupo.as_view()),
        name="listado_productos_grupo"),
    url(r'^maestro_productos_excel/$', login_required(ReporteExcelProductos.as_view()), name="maestro_productos_excel"),
    url(r'^maestro_grupos_productos_excel/$', login_required(ReporteExcelGruposProductos.as_view()),
        name="maestro_grupos_productos_excel"),
    url(r'^maestro_unidades_medida_excel/$', login_required(ReporteExcelUnidadesMedida.as_view()),
        name="maestro_unidades_medida_excel"),
    url(r'^maestro_servicios_excel/$', login_required(ReporteExcelServicios.as_view()), name="maestro_servicios_excel"),
    url(r'^eliminar_unidad_medida/$', login_required(EliminarUnidadMedida.as_view()), name="eliminar_unidad_medida"),
    url(r'^eliminar_grupo_productos/$', login_required(EliminarGrupoProductos.as_view()),
        name="eliminar_grupo_productos"),
    url(r'^eliminar_producto/$', login_required(EliminarProducto.as_view()), name="eliminar_producto"),
    url(r'^eliminar_servicio/$', login_required(EliminarServicio.as_view()), name="eliminar_servicio"),
    # url(r'^descargar_reporte_productos/$', login_required(DownloadProductosReport.as_view()), name="descargar_reporte_productos"),
]
