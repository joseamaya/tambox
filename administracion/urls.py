from django.urls import re_path
from administracion.views import OfficeCreate, OfficeList, Dashboard, \
    OfficeDetail, OfficeUpdate, WorkerList, WorkerCreate, \
    WorkerDetail, WorkerUpdate, PositionList, PositionCreate, \
    PositionDetail, PositionUpdate, OfficeImport, WorkerImport, \
    OfficeExcelReport, WorkerExcelReport, PositionImport, ApprovalLevelUpdate, \
    ProfessionList, ProfessionCreate, ProfessionDetail, ProfessionUpdate, \
    PositionExcelReport, ProfessionExcelReport, ApprovalLevelCreate, ApprovalLevelList, \
    ApprovalLevelDetail, ReceiverDniSearch, \
    ProducerUpdate, ProducerDetail, ProducerCreate, ProducerList, ReceiverNameSearch, ProducerImport

app_name = 'administracion'

urlpatterns = [
    re_path(r'^tablero/$', Dashboard.as_view(), name="tablero"),
    re_path(r'^maestro_oficinas/$', OfficeList.as_view(), name="maestro_oficinas"),
    re_path(r'^cargar_oficinas/$', OfficeImport.as_view(), name="cargar_oficinas"),
    re_path(r'^cargar_trabajadores/$', WorkerImport.as_view(), name="cargar_trabajadores"),
    re_path(r'^cargar_puestos/$', PositionImport.as_view(), name="cargar_puestos"),
    re_path(r'^cargar_productores/$', ProducerImport.as_view(), name="cargar_productores"),
    re_path(r'^maestro_oficinas_excel/$', OfficeExcelReport.as_view(), name="maestro_oficinas_excel"),
    re_path(r'^maestro_trabajadores_excel/$', WorkerExcelReport.as_view(),
        name="maestro_trabajadores_excel"),
    re_path(r'^reporte_excel_puestos/$', PositionExcelReport.as_view(), name="reporte_excel_puestos"),
    re_path(r'^reporte_excel_profesiones/$', ProfessionExcelReport.as_view(),
        name="reporte_excel_profesiones"),
    re_path(r'^crear_oficina/$', OfficeCreate.as_view(), name="crear_oficina"),
    re_path(r'^crear_nivel_aprobacion/$', ApprovalLevelCreate.as_view(), name="crear_nivel_aprobacion"),
    re_path(r'^detalle_oficina/(?P<pk>.+)/$', OfficeDetail.as_view(), name="detalle_oficina"),
    re_path(r'^modificar_oficina/(?P<pk>.+)/$', OfficeUpdate.as_view(), name="modificar_oficina"),
    re_path(r'^maestro_trabajadores/$', WorkerList.as_view(), name="maestro_trabajadores"),
    re_path(r'^crear_trabajador/$', WorkerCreate.as_view(), name="crear_trabajador"),
    re_path(r'^detalle_trabajador/(?P<pk>.+)/$', WorkerDetail.as_view(), name="detalle_trabajador"),
    re_path(r'^modificar_trabajador/(?P<pk>.+)/$', WorkerUpdate.as_view(),
        name="modificar_trabajador"),
    re_path(r'^crear_productor/$', ProducerCreate.as_view(), name="crear_productor"),
    re_path(r'^detalle_productor/(?P<pk>.+)/$', ProducerDetail.as_view(), name="detalle_productor"),
    re_path(r'^modificar_productor/(?P<pk>.+)/$', ProducerUpdate.as_view(), name="modificar_productor"),
    re_path(r'^maestro_productores/$', ProducerList.as_view(), name="maestro_productores"),
    re_path(r'^maestro_puestos/$', PositionList.as_view(), name="maestro_puestos"),
    re_path(r'^busqueda_receptor_dni/$', ReceiverDniSearch.as_view(), name="busqueda_receptor_dni"),
    re_path(r'^busqueda_receptor_name/$', ReceiverNameSearch.as_view(),
        name="busqueda_receptor_name"),
    re_path(r'^crear_puesto/$', PositionCreate.as_view(), name="crear_puesto"),
    re_path(r'^detalle_puesto/(?P<pk>.+)/$', PositionDetail.as_view(), name="detalle_puesto"),
    re_path(r'^modificar_puesto/(?P<pk>.+)/$', PositionUpdate.as_view(), name="modificar_puesto"),
    re_path(r'^maestro_profesiones/$', ProfessionList.as_view(), name="maestro_profesiones"),
    re_path(r'^crear_profesion/$', ProfessionCreate.as_view(), name="crear_profesion"),
    re_path(r'^detalle_profesion/(?P<pk>.+)/$', ProfessionDetail.as_view(), name="detalle_profesion"),
    re_path(r'^modificar_profesion/(?P<pk>.+)/$', ProfessionUpdate.as_view(), name="modificar_profesion"),
    re_path(r'^maestro_niveles_aprobacion/$', ApprovalLevelList.as_view(),
        name="maestro_niveles_aprobacion"),
    re_path(r'^detalle_nivel_aprobacion/(?P<pk>.+)/$', ApprovalLevelDetail.as_view(),
        name="detalle_nivel_aprobacion"),
    re_path(r'^modificar_nivel_aprobacion/(?P<pk>.+)/$', ApprovalLevelUpdate.as_view(),
        name="modificar_nivel_aprobacion"),
]
