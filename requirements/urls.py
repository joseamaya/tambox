from django.urls import re_path
from requirements.views import RequirementApprove, RequirementList,\
    QuotationListByRequirement, RequirementApprovalList,\
    Dashboard, RequirementCreate, RequirementDetailRow,\
    RequirementUpdate, RequirementTransfer,\
    RequirementDetailFetch, RequirementDetailView,\
    RequirementPdfReport, RequirementDelete, RequirementExcelReport

app_name = 'requirements'

urlpatterns = [
    re_path(r'^dashboard/$', Dashboard.as_view(), name="dashboard"),
    re_path(r'^requirement_approve/(?P<pk>.+)/$', RequirementApprove.as_view(),
        name="requirement_approve"),
    re_path(r'^requirement_list/$', RequirementList.as_view(), name="requirement_list"),
    re_path(r'^quotation_list_by_requirement/(?P<requirement>.+)/$',
        QuotationListByRequirement.as_view(), name="quotation_list_by_requirement"),
    re_path(r'^requirement_approval_list/$', RequirementApprovalList.as_view(),
        name="requirement_approval_list"),
    re_path(r'^requirement_create/$', RequirementCreate.as_view(), name="requirement_create"),
    re_path(r'^requirement_detail_row/$', RequirementDetailRow.as_view(),
        name="requirement_detail_row"),
    re_path(r'^requirement_update/(?P<pk>.+)/$', RequirementUpdate.as_view(),
        name="requirement_update"),
    re_path(r'^requirement_transfer/$', RequirementTransfer.as_view(),
        name="requirement_transfer"),
    re_path(r'^requirement_detail_fetch/$', RequirementDetailFetch.as_view(),
        name="requirement_detail_fetch"),
    re_path(r'^requirement_detail/(?P<code>.+)/$', RequirementDetailView.as_view(),
        name="requirement_detail"),
    re_path(r'^requirement_pdf/(?P<code>.+)/$', RequirementPdfReport.as_view(),
        name="requirement_pdf"),
    re_path(r'^requirement_delete/$', RequirementDelete.as_view(), name="requirement_delete"),
    re_path(r'^requirement_excel_report/$', RequirementExcelReport.as_view(),
        name="requirement_excel_report"),
]
