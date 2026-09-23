from django.urls import re_path
from administration.views import OfficeCreate, OfficeList, Dashboard,\
    OfficeDetail, OfficeUpdate, WorkerList, WorkerCreate,\
    WorkerDetail, WorkerUpdate, PositionList, PositionCreate,\
    PositionDetail, PositionUpdate, OfficeImport, WorkerImport,\
    OfficeExcelReport, WorkerExcelReport, PositionImport, ApprovalLevelUpdate,\
    ProfessionList, ProfessionCreate, ProfessionDetail, ProfessionUpdate,\
    PositionExcelReport, ProfessionExcelReport, ApprovalLevelCreate, ApprovalLevelList,\
    ApprovalLevelDetail, ReceiverDniSearch,\
    ProducerUpdate, ProducerDetail, ProducerCreate, ProducerList, ReceiverNameSearch, ProducerImport

app_name = 'administration'

urlpatterns = [
    re_path(r'^dashboard/$', Dashboard.as_view(), name="dashboard"),
    re_path(r'^office_list/$', OfficeList.as_view(), name="office_list"),
    re_path(r'^office_import/$', OfficeImport.as_view(), name="office_import"),
    re_path(r'^worker_import/$', WorkerImport.as_view(), name="worker_import"),
    re_path(r'^position_import/$', PositionImport.as_view(), name="position_import"),
    re_path(r'^producer_import/$', ProducerImport.as_view(), name="producer_import"),
    re_path(r'^office_excel_report/$', OfficeExcelReport.as_view(), name="office_excel_report"),
    re_path(r'^worker_excel_report/$', WorkerExcelReport.as_view(),
        name="worker_excel_report"),
    re_path(r'^position_excel_report/$', PositionExcelReport.as_view(), name="position_excel_report"),
    re_path(r'^profession_excel_report/$', ProfessionExcelReport.as_view(),
        name="profession_excel_report"),
    re_path(r'^office_create/$', OfficeCreate.as_view(), name="office_create"),
    re_path(r'^approval_level_create/$', ApprovalLevelCreate.as_view(), name="approval_level_create"),
    re_path(r'^office_detail/(?P<pk>.+)/$', OfficeDetail.as_view(), name="office_detail"),
    re_path(r'^office_update/(?P<pk>.+)/$', OfficeUpdate.as_view(), name="office_update"),
    re_path(r'^worker_list/$', WorkerList.as_view(), name="worker_list"),
    re_path(r'^worker_create/$', WorkerCreate.as_view(), name="worker_create"),
    re_path(r'^worker_detail/(?P<pk>.+)/$', WorkerDetail.as_view(), name="worker_detail"),
    re_path(r'^worker_update/(?P<pk>.+)/$', WorkerUpdate.as_view(),
        name="worker_update"),
    re_path(r'^producer_create/$', ProducerCreate.as_view(), name="producer_create"),
    re_path(r'^producer_detail/(?P<pk>.+)/$', ProducerDetail.as_view(), name="producer_detail"),
    re_path(r'^producer_update/(?P<pk>.+)/$', ProducerUpdate.as_view(), name="producer_update"),
    re_path(r'^producer_list/$', ProducerList.as_view(), name="producer_list"),
    re_path(r'^position_list/$', PositionList.as_view(), name="position_list"),
    re_path(r'^receiver_dni_search/$', ReceiverDniSearch.as_view(), name="receiver_dni_search"),
    re_path(r'^receiver_name_search/$', ReceiverNameSearch.as_view(),
        name="receiver_name_search"),
    re_path(r'^position_create/$', PositionCreate.as_view(), name="position_create"),
    re_path(r'^position_detail/(?P<pk>.+)/$', PositionDetail.as_view(), name="position_detail"),
    re_path(r'^position_update/(?P<pk>.+)/$', PositionUpdate.as_view(), name="position_update"),
    re_path(r'^profession_list/$', ProfessionList.as_view(), name="profession_list"),
    re_path(r'^profession_create/$', ProfessionCreate.as_view(), name="profession_create"),
    re_path(r'^profession_detail/(?P<pk>.+)/$', ProfessionDetail.as_view(), name="profession_detail"),
    re_path(r'^profession_update/(?P<pk>.+)/$', ProfessionUpdate.as_view(), name="profession_update"),
    re_path(r'^approval_level_list/$', ApprovalLevelList.as_view(),
        name="approval_level_list"),
    re_path(r'^approval_level_detail/(?P<pk>.+)/$', ApprovalLevelDetail.as_view(),
        name="approval_level_detail"),
    re_path(r'^approval_level_update/(?P<pk>.+)/$', ApprovalLevelUpdate.as_view(),
        name="approval_level_update"),
]
