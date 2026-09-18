from django.urls import re_path
from django.contrib.auth.decorators import login_required
from requerimientos.views import AprobarRequerimiento, ListadoRequerimientos, \
    ListadoCotizacionesPorRequerimiento, ListadoAprobacionRequerimientos, \
    Tablero, CrearRequerimiento, CrearDetalleRequerimiento, \
    ModificarRequerimiento, TransferenciaRequerimiento, \
    ObtenerDetalleRequerimiento, DetalleOperacionRequerimiento, \
    ReportePDFRequerimiento, EliminarRequerimiento, ReporteExcelRequerimientos

app_name = 'requerimientos'

urlpatterns = [
    re_path(r'^tablero/$', login_required(Tablero.as_view()), name="tablero"),
    re_path(r'^aprobar_requerimiento/(?P<pk>.+)/$', login_required(AprobarRequerimiento.as_view()),
        name="aprobar_requerimiento"),
    re_path(r'^requerimientos/$', login_required(ListadoRequerimientos.as_view()), name="requerimientos"),
    re_path(r'^listado_cotizaciones_requerimiento/(?P<requerimiento>.+)/$',
        login_required(ListadoCotizacionesPorRequerimiento.as_view()), name="listado_cotizaciones_requerimiento"),
    re_path(r'^listado_aprobacion_requerimientos/$', login_required(ListadoAprobacionRequerimientos.as_view()),
        name="listado_aprobacion_requerimientos"),
    re_path(r'^crear_requerimiento/$', login_required(CrearRequerimiento.as_view()), name="crear_requerimiento"),
    re_path(r'^crear_detalle_requerimiento/$', login_required(CrearDetalleRequerimiento.as_view()),
        name="crear_detalle_requerimiento"),
    re_path(r'^modificar_requerimiento/(?P<pk>.+)/$', login_required(ModificarRequerimiento.as_view()),
        name="modificar_requerimiento"),
    re_path(r'^transferencia_requerimiento/$', login_required(TransferenciaRequerimiento.as_view()),
        name="transferencia_requerimiento"),
    re_path(r'^obtener_detalle_requerimiento/$', login_required(ObtenerDetalleRequerimiento.as_view()),
        name="obtener_detalle_requerimiento"),
    re_path(r'^detalle_requerimiento/(?P<codigo>.+)/$', login_required(DetalleOperacionRequerimiento.as_view()),
        name="detalle_requerimiento"),
    re_path(r'^requerimiento_pdf/(?P<codigo>.+)/$', login_required(ReportePDFRequerimiento.as_view()),
        name="requerimiento_pdf"),
    re_path(r'^eliminar_requerimiento/$', login_required(EliminarRequerimiento.as_view()), name="eliminar_requerimiento"),
    re_path(r'^maestro_requerimientos_excel/$', login_required(ReporteExcelRequerimientos.as_view()),
        name="maestro_requerimientos_excel"),
]
