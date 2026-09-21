from django.urls import re_path
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
    CrearCotizacion, ListadoCotizaciones, DetalleOperacionConformidadServicios, \
    ModificarCotizacion, TransferenciaCotizacion, ObtenerDetalleCotizacion, \
    BusquedaCotizacion, DetalleOperacionCotizacion, DetalleOperacionOrdenCompra, DetalleOperacionOrdenServicios, \
    ReportePDFSolicitudCotizacion, ListadoOrdenesCompraPorCotizacion, \
    BusquedaProveedoresRUC, ListadoOrdenesServiciosPorCotizacion, \
    ListadoMovimientosPorOrdenCompra, ListadoConformidadesPorOrdenServicios, \
    ReporteExcelOrdenesServiciosFecha, EliminarCotizacion, \
    EliminarOrdenServicios, EliminarConformidadServicio

app_name = 'compras'

urlpatterns = [
    re_path(r'^tablero/$', Tablero.as_view(), name="tablero"),
    re_path(r'^proveedores/$', ListadoProveedores.as_view(), name="proveedores"),
    re_path(r'^ordenes_compra/$', ListadoOrdenesCompra.as_view(), name="ordenes_compra"),
    re_path(r'^ordenes_servicios/$', ListadoOrdenesServicios.as_view(), name="ordenes_servicios"),
    re_path(r'^conformidades_servicio/$', ListadoConformidadesServicio.as_view(),
        name="conformidades_servicio"),
    re_path(r'^listado_cotizaciones/$', ListadoCotizaciones.as_view(), name="listado_cotizaciones"),
    re_path(r'^listado_ordenes_compra_cotizacion/(?P<quotation>.+)/$',
        ListadoOrdenesCompraPorCotizacion.as_view(), name="listado_ordenes_compra_cotizacion"),
    re_path(r'^listado_ordenes_servicios_cotizacion/(?P<quotation>.+)/$',
        ListadoOrdenesServiciosPorCotizacion.as_view(), name="listado_ordenes_servicios_cotizacion"),
    re_path(r'^crear_proveedor/$', CrearProveedor.as_view(), name="crear_proveedor"),
    re_path(r'^crear_orden_compra/$', CrearOrdenCompra.as_view(), name="crear_orden_compra"),
    re_path(r'^crear_orden_servicios/$', CrearOrdenServicios.as_view(), name="crear_orden_servicios"),
    re_path(r'^crear_conformidad_servicio/$', CrearConformidadServicio.as_view(),
        name="crear_conformidad_servicio"),
    re_path(r'^crear_detalle_orden_compra/$', CrearDetalleOrdenCompra.as_view(),
        name="crear_detalle_orden_compra"),
    re_path(r'^crear_detalle_orden_servicios/$', CrearDetalleOrdenServicios.as_view(),
        name="crear_detalle_orden_servicios"),
    re_path(r'^crear_cotizacion/$', CrearCotizacion.as_view(), name="crear_cotizacion"),
    re_path(r'^cargar_proveedores/$', CargarProveedores.as_view(), name="cargar_proveedores"),
    re_path(r'^modificar_proveedor/(?P<pk>.+)/$', ModificarProveedor.as_view(), name="modificar_proveedor"),
    re_path(r'^modificar_orden_compra/(?P<pk>.+)/$', ModificarOrdenCompra.as_view(),
        name="modificar_orden_compra"),
    re_path(r'^modificar_orden_servicios/(?P<pk>.+)/$', ModificarOrdenServicios.as_view(),
        name="modificar_orden_servicios"),
    re_path(r'^modificar_conformidad_servicios/(?P<pk>.+)/$', ModificarConformidadServicio.as_view(),
        name="modificar_conformidad_servicios"),
    re_path(r'^modificar_cotizacion/(?P<pk>.+)/$', ModificarCotizacion.as_view(),
        name="modificar_cotizacion"),
    re_path(r'^busqueda_cotizacion/$', BusquedaCotizacion.as_view(), name="busqueda_cotizacion"),
    re_path(r'^busqueda_proveedores_razon_social/$', BusquedaProveedoresRazonSocial.as_view(),
        name="busqueda_proveedores_razon_social"),
    re_path(r'^busqueda_proveedores_ruc/$', BusquedaProveedoresRUC.as_view(),
        name="busqueda_proveedores_ruc"),
    re_path(r'^transferencia_cotizacion/$', TransferenciaCotizacion.as_view(),
        name="transferencia_cotizacion"),
    re_path(r'^transferencia_orden_compra/$', TransferenciaOrdenCompra.as_view(),
        name="transferencia_orden_compra"),
    re_path(r'^transferencia_orden_servicios/$', TransferenciaOrdenServicios.as_view(),
        name="transferencia_orden_servicios"),
    re_path(r'^obtener_detalle_cotizacion/$', ObtenerDetalleCotizacion.as_view(),
        name="obtener_detalle_cotizacion"),
    re_path(r'^obtener_detalle_orden_compra/$', ObtenerDetalleOrdenCompra.as_view(),
        name="obtener_detalle_orden_compra"),
    re_path(r'^obtener_detalle_orden_servicios/$', ObtenerDetalleOrdenServicios.as_view(),
        name="obtener_detalle_orden_servicios"),
    re_path(r'^detalle_proveedor/(?P<pk>\d+)/$', DetalleProveedor.as_view(), name="detalle_proveedor"),
    re_path(r'^quotation_detail/(?P<pk>.+)/$', DetalleOperacionCotizacion.as_view(),
        name="quotation_detail"),
    re_path(r'^purchase_order_detail/(?P<pk>.+)/$', DetalleOperacionOrdenCompra.as_view(),
        name="purchase_order_detail"),
    re_path(r'^service_order_detail/(?P<pk>.+)/$', DetalleOperacionOrdenServicios.as_view(),
        name="service_order_detail"),
    re_path(r'^detalle_conformidad_servicios/(?P<pk>.+)/$', DetalleOperacionConformidadServicios.as_view(),
        name="detalle_conformidad_servicios"),
    re_path(r'^listado_movimientos_orden_compra/(?P<order>.+)/$',
        ListadoMovimientosPorOrdenCompra.as_view(), name="listado_movimientos_orden_compra"),
    re_path(r'^listado_conformidades_orden_servicios/(?P<order>.+)/$',
        ListadoConformidadesPorOrdenServicios.as_view(), name="listado_conformidades_orden_servicios"),
    re_path(r'^orden_compra_pdf/(?P<pk>.+)/$', ReportePDFOrdenCompra.as_view(), name="orden_compra_pdf"),
    re_path(r'^orden_compra_xls/(?P<pk>.+)/$', ReporteXLSOrdenCompra.as_view(), name="orden_compra_xls"),
    re_path(r'^orden_servicios_pdf/(?P<code>.+)/$', ReportePDFOrdenServicios.as_view(),
        name="orden_servicios_pdf"),
    re_path(r'^ver_memorando_conformidad_servicio/(?P<code>.+)/$',
        ReportePDFMemorandoConformidadServicio.as_view(), name="ver_memorando_conformidad_servicio"),
    re_path(r'^cotizacion_pdf/(?P<code>.+)/$', ReportePDFSolicitudCotizacion.as_view(),
        name="cotizacion_pdf"),
    re_path(r'^maestro_proveedores_excel/$', ReporteExcelProveedores.as_view(),
        name="maestro_proveedores_excel"),
    re_path(r'^reporte_ordenes_compra_date/$', ReporteExcelOrdenesCompraFecha.as_view(),
        name="reporte_ordenes_compra_date"),
    re_path(r'^reporte_ordenes_servicios_date/$', ReporteExcelOrdenesServiciosFecha.as_view(),
        name="reporte_ordenes_servicios_date"),
    re_path(r'^eliminar_orden_compra/$', EliminarOrdenCompra.as_view(), name="eliminar_orden_compra"),
    re_path(r'^eliminar_orden_servicios/$', EliminarOrdenServicios.as_view(),
        name="eliminar_orden_servicios"),
    re_path(r'^eliminar_cotizacion/$', EliminarCotizacion.as_view(), name="eliminar_cotizacion"),
    re_path(r'^eliminar_proveedor/$', EliminarProveedor.as_view(), name="eliminar_proveedor"),
    re_path(r'^eliminar_conformidad_servicio/$', EliminarConformidadServicio.as_view(),
        name="eliminar_conformidad_servicio"),
]
