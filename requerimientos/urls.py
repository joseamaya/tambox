from django.conf.urls import url
from django.contrib.auth.decorators import login_required
from requerimientos.views import AprobarRequerimiento, ListadoRequerimientos,\
    ListadoCotizacionesPorRequerimiento, ListadoAprobacionRequerimientos,\
    Tablero, CrearRequerimiento, CrearDetalleRequerimiento,\
    ModificarRequerimiento, TransferenciaRequerimiento,\
    ObtenerDetalleRequerimiento, DetalleOperacionRequerimiento,\
    ReportePDFRequerimiento, EliminarRequerimiento, ReporteExcelRequerimientos

urlpatterns = [
    url(r'^tablero/$',login_required(Tablero.as_view()), name="tablero"),
    url(r'^aprobar_requerimiento/(?P<pk>.+)/$',login_required(AprobarRequerimiento.as_view()), name="aprobar_requerimiento"),
    url(r'^requerimientos/$',login_required(ListadoRequerimientos.as_view()), name="requerimientos"),
    url(r'^listado_cotizaciones_requerimiento/(?P<requerimiento>.+)/$',login_required(ListadoCotizacionesPorRequerimiento.as_view()), name="listado_cotizaciones_requerimiento"),
    url(r'^listado_aprobacion_requerimientos/$',login_required(ListadoAprobacionRequerimientos.as_view()), name="listado_aprobacion_requerimientos"),
    url(r'^crear_requerimiento/$',login_required(CrearRequerimiento.as_view()), name="crear_requerimiento"),
    url(r'^crear_detalle_requerimiento/$',login_required(CrearDetalleRequerimiento.as_view()), name="crear_detalle_requerimiento"),
    url(r'^modificar_requerimiento/(?P<pk>.+)/$',login_required(ModificarRequerimiento.as_view()), name="modificar_requerimiento"),
    url(r'^transferencia_requerimiento/$',login_required(TransferenciaRequerimiento.as_view()), name="transferencia_requerimiento"),
    url(r'^obtener_detalle_requerimiento/$',login_required(ObtenerDetalleRequerimiento.as_view()), name="obtener_detalle_requerimiento"),
    url(r'^detalle_requerimiento/(?P<pk>.+)/$', login_required(DetalleOperacionRequerimiento.as_view()), name="detalle_requerimiento"),
    url(r'^requerimiento_pdf/(?P<codigo>.+)/$', login_required(ReportePDFRequerimiento.as_view()), name="requerimiento_pdf"),
    url(r'^eliminar_requerimiento/$',login_required(EliminarRequerimiento.as_view()), name="eliminar_requerimiento"),
    url(r'^maestro_requerimientos_excel/$',login_required(ReporteExcelRequerimientos.as_view()), name="maestro_requerimientos_excel"),
]