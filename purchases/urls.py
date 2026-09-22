from django.urls import re_path
from purchases.views import Dashboard, SupplierList, SupplierCreate, PurchaseOrderCreate,\
    SupplierNameSearch, PurchaseOrderDetailCreate,\
    PurchaseOrderTransfer, PurchaseOrderDetailFetch,\
    PurchaseOrderExcelReportByDate, PurchaseOrderList, SupplierDetail,\
    PurchaseOrderUpdate, PurchaseOrderPdfReport, PurchaseOrderXlsReport, PurchaseOrderDelete, SupplierUpdate,\
    SupplierDelete, SupplierExcelReport, ServiceOrderCreate, ServiceOrderDetailCreate,\
    ServiceOrderList,\
    ServiceOrderUpdate, SupplierImport,\
    ServiceConformityCreate, ServiceOrderTransfer, ServiceOrderDetailFetch, ServiceConformityList,\
    ServiceOrderPdfReport, ServiceConformityMemoPdfReport, ServiceConformityUpdate,\
    QuotationCreate, QuotationList, ServiceConformityDetailView,\
    QuotationUpdate, QuotationTransfer, QuotationDetailFetch, QuotationDetailRows,\
    QuotationSearch, QuotationDetailView, PurchaseOrderDetailView, ServiceOrderDetailView,\
    QuotationRequestPdfReport, PurchaseOrderListByQuotation,\
    SupplierTaxIdSearch, ServiceOrderListByQuotation,\
    MovementListByPurchaseOrder, ServiceConformityListByServiceOrder,\
    ServiceOrderExcelReportByDate, QuotationDelete,\
    ServiceOrderDelete, ServiceConformityDelete

app_name = 'purchases'

urlpatterns = [
    re_path(r'^dashboard/$', Dashboard.as_view(), name="dashboard"),
    re_path(r'^supplier_list/$', SupplierList.as_view(), name="supplier_list"),
    re_path(r'^purchase_order_list/$', PurchaseOrderList.as_view(), name="purchase_order_list"),
    re_path(r'^service_order_list/$', ServiceOrderList.as_view(), name="service_order_list"),
    re_path(r'^service_conformity_list/$', ServiceConformityList.as_view(),
        name="service_conformity_list"),
    re_path(r'^quotation_list/$', QuotationList.as_view(), name="quotation_list"),
    re_path(r'^purchase_order_list_by_quotation/(?P<quotation>.+)/$',
        PurchaseOrderListByQuotation.as_view(), name="purchase_order_list_by_quotation"),
    re_path(r'^service_order_list_by_quotation/(?P<quotation>.+)/$',
        ServiceOrderListByQuotation.as_view(), name="service_order_list_by_quotation"),
    re_path(r'^supplier_create/$', SupplierCreate.as_view(), name="supplier_create"),
    re_path(r'^purchase_order_create/$', PurchaseOrderCreate.as_view(), name="purchase_order_create"),
    re_path(r'^service_order_create/$', ServiceOrderCreate.as_view(), name="service_order_create"),
    re_path(r'^service_conformity_create/$', ServiceConformityCreate.as_view(),
        name="service_conformity_create"),
    re_path(r'^purchase_order_detail_create/$', PurchaseOrderDetailCreate.as_view(),
        name="purchase_order_detail_create"),
    re_path(r'^service_order_detail_create/$', ServiceOrderDetailCreate.as_view(),
        name="service_order_detail_create"),
    re_path(r'^quotation_create/$', QuotationCreate.as_view(), name="quotation_create"),
    re_path(r'^supplier_import/$', SupplierImport.as_view(), name="supplier_import"),
    re_path(r'^supplier_update/(?P<pk>.+)/$', SupplierUpdate.as_view(), name="supplier_update"),
    re_path(r'^purchase_order_update/(?P<pk>.+)/$', PurchaseOrderUpdate.as_view(),
        name="purchase_order_update"),
    re_path(r'^service_order_update/(?P<pk>.+)/$', ServiceOrderUpdate.as_view(),
        name="service_order_update"),
    re_path(r'^service_conformity_update/(?P<pk>.+)/$', ServiceConformityUpdate.as_view(),
        name="service_conformity_update"),
    re_path(r'^quotation_update/(?P<pk>.+)/$', QuotationUpdate.as_view(),
        name="quotation_update"),
    re_path(r'^quotation_search/$', QuotationSearch.as_view(), name="quotation_search"),
    re_path(r'^supplier_name_search/$', SupplierNameSearch.as_view(),
        name="supplier_name_search"),
    re_path(r'^supplier_tax_id_search/$', SupplierTaxIdSearch.as_view(),
        name="supplier_tax_id_search"),
    re_path(r'^quotation_transfer/$', QuotationTransfer.as_view(),
        name="quotation_transfer"),
    re_path(r'^purchase_order_transfer/$', PurchaseOrderTransfer.as_view(),
        name="purchase_order_transfer"),
    re_path(r'^service_order_transfer/$', ServiceOrderTransfer.as_view(),
        name="service_order_transfer"),
    re_path(r'^quotation_detail_fetch/$', QuotationDetailFetch.as_view(),
        name="quotation_detail_fetch"),
    re_path(r'^quotation_detail_rows/$', QuotationDetailRows.as_view(),
        name="quotation_detail_rows"),
    re_path(r'^purchase_order_detail_fetch/$', PurchaseOrderDetailFetch.as_view(),
        name="purchase_order_detail_fetch"),
    re_path(r'^service_order_detail_fetch/$', ServiceOrderDetailFetch.as_view(),
        name="service_order_detail_fetch"),
    re_path(r'^supplier_detail/(?P<pk>\d+)/$', SupplierDetail.as_view(), name="supplier_detail"),
    re_path(r'^quotation_detail/(?P<pk>.+)/$', QuotationDetailView.as_view(),
        name="quotation_detail"),
    re_path(r'^purchase_order_detail/(?P<pk>.+)/$', PurchaseOrderDetailView.as_view(),
        name="purchase_order_detail"),
    re_path(r'^service_order_detail/(?P<pk>.+)/$', ServiceOrderDetailView.as_view(),
        name="service_order_detail"),
    re_path(r'^service_conformity_detail_view/(?P<pk>.+)/$', ServiceConformityDetailView.as_view(),
        name="service_conformity_detail_view"),
    re_path(r'^movement_list_by_purchase_order/(?P<order>.+)/$',
        MovementListByPurchaseOrder.as_view(), name="movement_list_by_purchase_order"),
    re_path(r'^service_conformity_list_by_service_order/(?P<order>.+)/$',
        ServiceConformityListByServiceOrder.as_view(), name="service_conformity_list_by_service_order"),
    re_path(r'^purchase_order_pdf/(?P<pk>.+)/$', PurchaseOrderPdfReport.as_view(), name="purchase_order_pdf"),
    re_path(r'^purchase_order_xls/(?P<pk>.+)/$', PurchaseOrderXlsReport.as_view(), name="purchase_order_xls"),
    re_path(r'^service_order_pdf/(?P<code>.+)/$', ServiceOrderPdfReport.as_view(),
        name="service_order_pdf"),
    re_path(r'^service_conformity_memo_pdf/(?P<code>.+)/$',
        ServiceConformityMemoPdfReport.as_view(), name="service_conformity_memo_pdf"),
    re_path(r'^quotation_pdf/(?P<code>.+)/$', QuotationRequestPdfReport.as_view(),
        name="quotation_pdf"),
    re_path(r'^supplier_excel_report/$', SupplierExcelReport.as_view(),
        name="supplier_excel_report"),
    re_path(r'^purchase_order_excel_report_by_date/$', PurchaseOrderExcelReportByDate.as_view(),
        name="purchase_order_excel_report_by_date"),
    re_path(r'^service_order_excel_report_by_date/$', ServiceOrderExcelReportByDate.as_view(),
        name="service_order_excel_report_by_date"),
    re_path(r'^purchase_order_delete/$', PurchaseOrderDelete.as_view(), name="purchase_order_delete"),
    re_path(r'^service_order_delete/$', ServiceOrderDelete.as_view(),
        name="service_order_delete"),
    re_path(r'^quotation_delete/$', QuotationDelete.as_view(), name="quotation_delete"),
    re_path(r'^supplier_delete/$', SupplierDelete.as_view(), name="supplier_delete"),
    re_path(r'^service_conformity_delete/$', ServiceConformityDelete.as_view(),
        name="service_conformity_delete"),
]
