from django.urls import re_path
from django.contrib.auth.decorators import login_required
from compras.views import Tablero, ListadoProveedores, CrearProveedor, CrearOrdenCompra, \
    BusquedaProveedoresRazonSocial, CrearDetalleOrdenCompra, \
    TransferenciaOrdenCompra, ObtenerDetalleOrdenCompra, \
    ReporteExcelOrdenesCompraFecha, ListadoOrdenesCompra, DetalleProveedor, \
    ModificarOrdenCompra, ReportePDFOrdenCompra, ReporteXLSOrdenCompra, EliminarOrdenCompra, ModificarProveedor, \
    EliminarProveedor, ReporteExcelProveedores, CrearOrdenServicios, CrearDetalleOrdenServicios, \
    ListadoOrdenesServicios, \
    ModificarOrdenServicios, CargarProveedores, \
    CrearConformidadServicio, TransferenciaOrdenServicios, ObtenerDetalleOrdenServicios, ListadoConformidadesServicio, \
    ReportePDFOrdenServicios, ReportePDFMemorandoConformidadServicio, ModificarConformidadServicio, \
    CrearCotizacion, CrearDetalleCotizacion, ListadoCotizaciones, DetalleOperacionConformidadServicios, \
    ModificarCotizacion, TransferenciaCotizacion, ObtenerDetalleCotizacion, \
    BusquedaCotizacion, DetalleOperacionCotizacion, DetalleOperacionOrdenCompra, DetalleOperacionOrdenServicios, \
    ReportePDFSolicitudCotizacion, ListadoOrdenesCompraPorCotizacion, \
    BusquedaProveedoresRUC, ListadoOrdenesServiciosPorCotizacion, \
    ListadoMovimientosPorOrdenCompra, ListadoConformidadesPorOrdenServicios, \
    ReporteExcelOrdenesServiciosFecha, EliminarCotizacion, \
    EliminarOrdenServicios, EliminarConformidadServicio

app_name = 'compras'

urlpatterns = [
    re_path(r'^tablero/$', login_required(Tablero.as_view()), name="tablero"),
    re_path(r'^proveedores/$', login_required(ListadoProveedores.as_view()), name="proveedores"),
    re_path(r'^ordenes_compra/$', login_required(ListadoOrdenesCompra.as_view()), name="ordenes_compra"),
    re_path(r'^ordenes_servicios/$', login_required(ListadoOrdenesServicios.as_view()), name="ordenes_servicios"),
    re_path(r'^conformidades_servicio/$', login_required(ListadoConformidadesServicio.as_view()),
        name="conformidades_servicio"),
    re_path(r'^listado_cotizaciones/$', login_required(ListadoCotizaciones.as_view()), name="listado_cotizaciones"),
    re_path(r'^listado_ordenes_compra_cotizacion/(?P<cotizacion>.+)/$',
        login_required(ListadoOrdenesCompraPorCotizacion.as_view()), name="listado_ordenes_compra_cotizacion"),
    re_path(r'^listado_ordenes_servicios_cotizacion/(?P<cotizacion>.+)/$',
        login_required(ListadoOrdenesServiciosPorCotizacion.as_view()), name="listado_ordenes_servicios_cotizacion"),
    re_path(r'^crear_proveedor/$', login_required(CrearProveedor.as_view()), name="crear_proveedor"),
    re_path(r'^crear_orden_compra/$', login_required(CrearOrdenCompra.as_view()), name="crear_orden_compra"),
    re_path(r'^crear_orden_servicios/$', login_required(CrearOrdenServicios.as_view()), name="crear_orden_servicios"),
    re_path(r'^crear_conformidad_servicio/$', login_required(CrearConformidadServicio.as_view()),
        name="crear_conformidad_servicio"),
    re_path(r'^crear_detalle_orden_compra/$', login_required(CrearDetalleOrdenCompra.as_view()),
        name="crear_detalle_orden_compra"),
    re_path(r'^crear_detalle_orden_servicios/$', login_required(CrearDetalleOrdenServicios.as_view()),
        name="crear_detalle_orden_servicios"),
    re_path(r'^crear_cotizacion/$', login_required(CrearCotizacion.as_view()), name="crear_cotizacion"),
    re_path(r'^crear_detalle_cotizacion/$', login_required(CrearDetalleCotizacion.as_view()),
        name="crear_detalle_cotizacion"),
    re_path(r'^cargar_proveedores/$', login_required(CargarProveedores.as_view()), name="cargar_proveedores"),
    re_path(r'^modificar_proveedor/(?P<pk>.+)/$', login_required(ModificarProveedor.as_view()), name="modificar_proveedor"),
    re_path(r'^modificar_orden_compra/(?P<pk>.+)/$', login_required(ModificarOrdenCompra.as_view()),
        name="modificar_orden_compra"),
    re_path(r'^modificar_orden_servicios/(?P<pk>.+)/$', login_required(ModificarOrdenServicios.as_view()),
        name="modificar_orden_servicios"),
    re_path(r'^modificar_conformidad_servicios/(?P<pk>.+)/$', login_required(ModificarConformidadServicio.as_view()),
        name="modificar_conformidad_servicios"),
    re_path(r'^modificar_cotizacion/(?P<pk>.+)/$', login_required(ModificarCotizacion.as_view()),
        name="modificar_cotizacion"),
    re_path(r'^busqueda_cotizacion/$', login_required(BusquedaCotizacion.as_view()), name="busqueda_cotizacion"),
    re_path(r'^busqueda_proveedores_razon_social/$', login_required(BusquedaProveedoresRazonSocial.as_view()),
        name="busqueda_proveedores_razon_social"),
    re_path(r'^busqueda_proveedores_ruc/$', login_required(BusquedaProveedoresRUC.as_view()),
        name="busqueda_proveedores_ruc"),
    re_path(r'^transferencia_cotizacion/$', login_required(TransferenciaCotizacion.as_view()),
        name="transferencia_cotizacion"),
    re_path(r'^transferencia_orden_compra/$', login_required(TransferenciaOrdenCompra.as_view()),
        name="transferencia_orden_compra"),
    re_path(r'^transferencia_orden_servicios/$', login_required(TransferenciaOrdenServicios.as_view()),
        name="transferencia_orden_servicios"),
    re_path(r'^obtener_detalle_cotizacion/$', login_required(ObtenerDetalleCotizacion.as_view()),
        name="obtener_detalle_cotizacion"),
    re_path(r'^obtener_detalle_orden_compra/$', login_required(ObtenerDetalleOrdenCompra.as_view()),
        name="obtener_detalle_orden_compra"),
    re_path(r'^obtener_detalle_orden_servicios/$', login_required(ObtenerDetalleOrdenServicios.as_view()),
        name="obtener_detalle_orden_servicios"),
    re_path(r'^detalle_proveedor/(?P<pk>\d+)/$', login_required(DetalleProveedor.as_view()), name="detalle_proveedor"),
    re_path(r'^detalle_cotizacion/(?P<pk>.+)/$', login_required(DetalleOperacionCotizacion.as_view()),
        name="detalle_cotizacion"),
    re_path(r'^detalle_orden_compra/(?P<pk>.+)/$', login_required(DetalleOperacionOrdenCompra.as_view()),
        name="detalle_orden_compra"),
    re_path(r'^detalle_orden_servicios/(?P<pk>.+)/$', login_required(DetalleOperacionOrdenServicios.as_view()),
        name="detalle_orden_servicios"),
    re_path(r'^detalle_conformidad_servicios/(?P<pk>.+)/$', login_required(DetalleOperacionConformidadServicios.as_view()),
        name="detalle_conformidad_servicios"),
    re_path(r'^listado_movimientos_orden_compra/(?P<orden>.+)/$',
        login_required(ListadoMovimientosPorOrdenCompra.as_view()), name="listado_movimientos_orden_compra"),
    re_path(r'^listado_conformidades_orden_servicios/(?P<orden>.+)/$',
        login_required(ListadoConformidadesPorOrdenServicios.as_view()), name="listado_conformidades_orden_servicios"),
    re_path(r'^orden_compra_pdf/(?P<pk>.+)/$', login_required(ReportePDFOrdenCompra.as_view()), name="orden_compra_pdf"),
    re_path(r'^orden_compra_xls/(?P<pk>.+)/$', login_required(ReporteXLSOrdenCompra.as_view()), name="orden_compra_xls"),
    re_path(r'^orden_servicios_pdf/(?P<codigo>.+)/$', login_required(ReportePDFOrdenServicios.as_view()),
        name="orden_servicios_pdf"),
    re_path(r'^ver_memorando_conformidad_servicio/(?P<codigo>.+)/$',
        login_required(ReportePDFMemorandoConformidadServicio.as_view()), name="ver_memorando_conformidad_servicio"),
    re_path(r'^cotizacion_pdf/(?P<codigo>.+)/$', login_required(ReportePDFSolicitudCotizacion.as_view()),
        name="cotizacion_pdf"),
    re_path(r'^maestro_proveedores_excel/$', login_required(ReporteExcelProveedores.as_view()),
        name="maestro_proveedores_excel"),
    re_path(r'^reporte_ordenes_compra_fecha/$', login_required(ReporteExcelOrdenesCompraFecha.as_view()),
        name="reporte_ordenes_compra_fecha"),
    re_path(r'^reporte_ordenes_servicios_fecha/$', login_required(ReporteExcelOrdenesServiciosFecha.as_view()),
        name="reporte_ordenes_servicios_fecha"),
    re_path(r'^eliminar_orden_compra/$', login_required(EliminarOrdenCompra.as_view()), name="eliminar_orden_compra"),
    re_path(r'^eliminar_orden_servicios/$', login_required(EliminarOrdenServicios.as_view()),
        name="eliminar_orden_servicios"),
    re_path(r'^eliminar_cotizacion/$', login_required(EliminarCotizacion.as_view()), name="eliminar_cotizacion"),
    re_path(r'^eliminar_proveedor/$', login_required(EliminarProveedor.as_view()), name="eliminar_proveedor"),
    re_path(r'^eliminar_conformidad_servicio/$', login_required(EliminarConformidadServicio.as_view()),
        name="eliminar_conformidad_servicio"),
]
