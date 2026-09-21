from django.urls import re_path
from requerimientos.views import RequirementApprove, RequirementList, \
    QuotationListByRequirement, RequirementApprovalList, \
    Dashboard, RequirementCreate, RequirementDetailCreate, \
    RequirementUpdate, RequirementTransfer, \
    RequirementDetailFetch, RequirementDetailView, \
    RequirementPdfReport, RequirementDelete, RequirementExcelReport

app_name = 'requerimientos'

urlpatterns = [
    re_path(r'^tablero/$', Dashboard.as_view(), name="tablero"),
    re_path(r'^aprobar_requerimiento/(?P<pk>.+)/$', RequirementApprove.as_view(),
        name="aprobar_requerimiento"),
    re_path(r'^requerimientos/$', RequirementList.as_view(), name="requerimientos"),
    re_path(r'^listado_cotizaciones_requerimiento/(?P<requirement>.+)/$',
        QuotationListByRequirement.as_view(), name="listado_cotizaciones_requerimiento"),
    re_path(r'^listado_aprobacion_requerimientos/$', RequirementApprovalList.as_view(),
        name="listado_aprobacion_requerimientos"),
    re_path(r'^crear_requerimiento/$', RequirementCreate.as_view(), name="crear_requerimiento"),
    re_path(r'^crear_detalle_requerimiento/$', RequirementDetailCreate.as_view(),
        name="crear_detalle_requerimiento"),
    re_path(r'^modificar_requerimiento/(?P<pk>.+)/$', RequirementUpdate.as_view(),
        name="modificar_requerimiento"),
    re_path(r'^transferencia_requerimiento/$', RequirementTransfer.as_view(),
        name="transferencia_requerimiento"),
    re_path(r'^obtener_detalle_requerimiento/$', RequirementDetailFetch.as_view(),
        name="obtener_detalle_requerimiento"),
    re_path(r'^requirement_detail/(?P<code>.+)/$', RequirementDetailView.as_view(),
        name="requirement_detail"),
    re_path(r'^requerimiento_pdf/(?P<code>.+)/$', RequirementPdfReport.as_view(),
        name="requerimiento_pdf"),
    re_path(r'^eliminar_requerimiento/$', RequirementDelete.as_view(), name="eliminar_requerimiento"),
    re_path(r'^maestro_requerimientos_excel/$', RequirementExcelReport.as_view(),
        name="maestro_requerimientos_excel"),
]
