from django.urls import re_path
from requerimientos.views import AprobarRequerimiento, ListadoRequerimientos, \
    ListadoCotizacionesPorRequerimiento, ListadoAprobacionRequerimientos, \
    Tablero, CrearRequerimiento, CrearDetalleRequerimiento, \
    ModificarRequerimiento, TransferenciaRequerimiento, \
    ObtenerDetalleRequerimiento, DetalleOperacionRequerimiento, \
    ReportePDFRequerimiento, EliminarRequerimiento, ReporteExcelRequerimientos

app_name = 'requerimientos'

urlpatterns = [
    re_path(r'^tablero/$', Tablero.as_view(), name="tablero"),
    re_path(r'^aprobar_requerimiento/(?P<pk>.+)/$', AprobarRequerimiento.as_view(),
        name="aprobar_requerimiento"),
    re_path(r'^requerimientos/$', ListadoRequerimientos.as_view(), name="requerimientos"),
    re_path(r'^listado_cotizaciones_requerimiento/(?P<requirement>.+)/$',
        ListadoCotizacionesPorRequerimiento.as_view(), name="listado_cotizaciones_requerimiento"),
    re_path(r'^listado_aprobacion_requerimientos/$', ListadoAprobacionRequerimientos.as_view(),
        name="listado_aprobacion_requerimientos"),
    re_path(r'^crear_requerimiento/$', CrearRequerimiento.as_view(), name="crear_requerimiento"),
    re_path(r'^crear_detalle_requerimiento/$', CrearDetalleRequerimiento.as_view(),
        name="crear_detalle_requerimiento"),
    re_path(r'^modificar_requerimiento/(?P<pk>.+)/$', ModificarRequerimiento.as_view(),
        name="modificar_requerimiento"),
    re_path(r'^transferencia_requerimiento/$', TransferenciaRequerimiento.as_view(),
        name="transferencia_requerimiento"),
    re_path(r'^obtener_detalle_requerimiento/$', ObtenerDetalleRequerimiento.as_view(),
        name="obtener_detalle_requerimiento"),
    re_path(r'^requirement_detail/(?P<code>.+)/$', DetalleOperacionRequerimiento.as_view(),
        name="requirement_detail"),
    re_path(r'^requerimiento_pdf/(?P<code>.+)/$', ReportePDFRequerimiento.as_view(),
        name="requerimiento_pdf"),
    re_path(r'^eliminar_requerimiento/$', EliminarRequerimiento.as_view(), name="eliminar_requerimiento"),
    re_path(r'^maestro_requerimientos_excel/$', ReporteExcelRequerimientos.as_view(),
        name="maestro_requerimientos_excel"),
]
