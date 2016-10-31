from django.conf.urls import url
from django.contrib.auth.decorators import login_required
from compras.views import Tablero, ListadoProveedores, CrearProveedor, CrearOrdenCompra, \
    BusquedaProveedoresRazonSocial, CrearDetalleOrdenCompra, \
    TransferenciaOrdenCompra, ObtenerDetalleOrdenCompra, \
    ReporteExcelOrdenesCompraFecha, ListadoOrdenesCompra, DetalleProveedor, \
    ModificarOrdenCompra, ReportePDFOrdenCompra, EliminarOrdenCompra, ModificarProveedor, \
    EliminarProveedor, ReporteExcelProveedores, CrearOrdenServicios, CrearDetalleOrdenServicio, ListadoOrdenesServicios, \
    ModificarOrdenServicios, CargarProveedores, \
    CrearConformidadServicio, TransferenciaOrdenServicios, ObtenerDetalleOrdenServicios, ListadoConformidadesServicio, \
    ReportePDFOrdenServicios, ReportePDFMemorandoConformidadServicio, ModificarConformidadServicio, \
    CrearCotizacion, CrearDetalleCotizacion, ListadoCotizaciones, DetalleOperacionConformidadServicios, \
    ModificarCotizacion, TransferenciaCotizacion, ObtenerDetalleCotizacion, \
    BusquedaCotizacion, DetalleOperacionCotizacion, DetalleOperacionOrdenCompra, DetalleOperacionOrdenServicios, \
    ReportePDFSolicitudCotizacion, ListadoOrdenesCompraPorCotizacion, \
    BusquedaProveedoresRUC

urlpatterns = [
    url(r'^tablero/$', login_required(Tablero.as_view()), name="tablero"),
    url(r'^proveedores/$', login_required(ListadoProveedores.as_view()), name="proveedores"),
    url(r'^ordenes_compra/$', login_required(ListadoOrdenesCompra.as_view()), name="ordenes_compra"),
    url(r'^ordenes_servicios/$', login_required(ListadoOrdenesServicios.as_view()), name="ordenes_servicios"),
    url(r'^conformidades_servicio/$', login_required(ListadoConformidadesServicio.as_view()),
        name="conformidades_servicio"),
    url(r'^listado_cotizaciones/$', login_required(ListadoCotizaciones.as_view()), name="listado_cotizaciones"),
    url(r'^listado_ordenes_compra_cotizacion/(?P<cotizacion>.+)/$',
        login_required(ListadoOrdenesCompraPorCotizacion.as_view()), name="listado_ordenes_compra_cotizacion"),
    url(r'^crear_proveedor/$', login_required(CrearProveedor.as_view()), name="crear_proveedor"),
    url(r'^crear_orden_compra/$', login_required(CrearOrdenCompra.as_view()), name="crear_orden_compra"),
    url(r'^crear_orden_servicios/$', login_required(CrearOrdenServicios.as_view()), name="crear_orden_servicios"),
    url(r'^crear_conformidad_servicio/$', login_required(CrearConformidadServicio.as_view()),
        name="crear_conformidad_servicio"),
    url(r'^crear_detalle_orden_compra/$', login_required(CrearDetalleOrdenCompra.as_view()),
        name="crear_detalle_orden_compra"),
    url(r'^crear_detalle_orden_servicio/$', login_required(CrearDetalleOrdenServicio.as_view()),
        name="crear_detalle_orden_servicio"),
    url(r'^crear_cotizacion/$', login_required(CrearCotizacion.as_view()), name="crear_cotizacion"),
    url(r'^crear_detalle_cotizacion/$', login_required(CrearDetalleCotizacion.as_view()),
        name="crear_detalle_cotizacion"),
    url(r'^cargar_proveedores/$', login_required(CargarProveedores.as_view()), name="cargar_proveedores"),
    url(r'^modificar_proveedor/(?P<pk>.+)/$', login_required(ModificarProveedor.as_view()), name="modificar_proveedor"),
    url(r'^modificar_orden_compra/(?P<pk>.+)/$', login_required(ModificarOrdenCompra.as_view()),
        name="modificar_orden_compra"),
    url(r'^modificar_orden_servicios/(?P<pk>.+)/$', login_required(ModificarOrdenServicios.as_view()),
        name="modificar_orden_servicios"),
    url(r'^modificar_conformidad_servicios/(?P<pk>.+)/$', login_required(ModificarConformidadServicio.as_view()),
        name="modificar_conformidad_servicios"),
    url(r'^modificar_cotizacion/(?P<pk>.+)/$', login_required(ModificarCotizacion.as_view()),
        name="modificar_cotizacion"),
    url(r'^busqueda_cotizacion/$', login_required(BusquedaCotizacion.as_view()), name="busqueda_cotizacion"),
    url(r'^busqueda_proveedores_razon_social/$', login_required(BusquedaProveedoresRazonSocial.as_view()),
        name="busqueda_proveedores_razon_social"),
    url(r'^busqueda_proveedores_ruc/$', login_required(BusquedaProveedoresRUC.as_view()),
        name="busqueda_proveedores_ruc"),
    url(r'^transferencia_cotizacion/$', login_required(TransferenciaCotizacion.as_view()),
        name="transferencia_cotizacion"),
    url(r'^transferencia_orden_compra/$', login_required(TransferenciaOrdenCompra.as_view()),
        name="transferencia_orden_compra"),
    url(r'^transferencia_orden_servicios/$', login_required(TransferenciaOrdenServicios.as_view()),
        name="transferencia_orden_servicios"),
    url(r'^obtener_detalle_cotizacion/$', login_required(ObtenerDetalleCotizacion.as_view()),
        name="obtener_detalle_cotizacion"),
    url(r'^obtener_detalle_orden_compra/$', login_required(ObtenerDetalleOrdenCompra.as_view()),
        name="obtener_detalle_orden_compra"),
    url(r'^obtener_detalle_orden_servicios/$', login_required(ObtenerDetalleOrdenServicios.as_view()),
        name="obtener_detalle_orden_servicios"),
    url(r'^detalle_proveedor/(?P<pk>\d+)/$', login_required(DetalleProveedor.as_view()), name="detalle_proveedor"),
    url(r'^detalle_cotizacion/(?P<pk>.+)/$', login_required(DetalleOperacionCotizacion.as_view()),
        name="detalle_cotizacion"),
    url(r'^detalle_orden_compra/(?P<pk>.+)/$', login_required(DetalleOperacionOrdenCompra.as_view()),
        name="detalle_orden_compra"),
    url(r'^detalle_orden_servicios/(?P<pk>.+)/$', login_required(DetalleOperacionOrdenServicios.as_view()),
        name="detalle_orden_servicios"),
    url(r'^detalle_conformidad_servicios/(?P<pk>.+)/$', login_required(DetalleOperacionConformidadServicios.as_view()),
        name="detalle_conformidad_servicios"),
    url(r'^orden_compra_pdf/(?P<pk>.+)/$', login_required(ReportePDFOrdenCompra.as_view()), name="orden_compra_pdf"),
    url(r'^orden_servicios_pdf/(?P<codigo>.+)/$', login_required(ReportePDFOrdenServicios.as_view()),
        name="orden_servicios_pdf"),
    url(r'^ver_memorando_conformidad_servicio/(?P<codigo>.+)/$',
        login_required(ReportePDFMemorandoConformidadServicio.as_view()), name="ver_memorando_conformidad_servicio"),
    url(r'^cotizacion_pdf/(?P<codigo>.+)/$', login_required(ReportePDFSolicitudCotizacion.as_view()),
        name="cotizacion_pdf"),
    url(r'^maestro_proveedores_excel/$', login_required(ReporteExcelProveedores.as_view()),
        name="maestro_proveedores_excel"),
    url(r'^reporte_ordenes_compra_fecha/$', login_required(ReporteExcelOrdenesCompraFecha.as_view()),
        name="reporte_ordenes_compra_fecha"),
    url(r'^eliminar_orden_compra/$', login_required(EliminarOrdenCompra.as_view()), name="eliminar_orden_compra"),
    url(r'^eliminar_proveedor/$', login_required(EliminarProveedor.as_view()), name="eliminar_proveedor"),
]
