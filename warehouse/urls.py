from django.urls import re_path
from warehouse.views import WarehouseCreate, InboundCreate, OutboundCreate,\
    OutboundDetailCreate,\
    MovementTypeCreate, WarehouseList, Dashboard, MovementTypeList,\
    MovementExcelReport, MovementExcelReportByDate, MovementList, InboundDetailCreate,\
    StockQuery, ProductWarehouseSearch, MovementPdfReport, KardexReport, WarehouseDetail,\
    MovementDelete, WarehouseUpdate, WarehouseDelete, MovementTypeDetail, MovementUpdate,\
    WarehouseExcelReport, InboundUpdate, OutboundUpdate, VerifyReferenceRequired,\
    MovementTypeExcelReport, OrderCreate,\
    WarehouseImport, InitialInventoryImport, OrderDetailCreate, OrderUpdate, OrderList, OrderApprove,\
    OrderApprovalList, VerifyStockForOrder,\
    OrderDetailView, MovementDetailView, ProductStock,\
    InboundList, OutboundList, KardexProductReport, MovementListByOrder,\
    PriceReprocess, OrderDelete, MovementListByProduct, ProductStockList, Inventory

app_name = 'warehouse'

urlpatterns = [
    re_path(r'^dashboard/$', Dashboard.as_view(), name="dashboard"),
    re_path(r'^inbound_create/$', InboundCreate.as_view(), name="inbound_create"),
    re_path(r'^outbound_create/$', OutboundCreate.as_view(), name="outbound_create"),
    re_path(r'^order_create/$', OrderCreate.as_view(), name="order_create"),
    re_path(r'^order_detail_create/$', OrderDetailCreate.as_view(), name="order_detail_create"),
    re_path(r'^movement_type_create/$', MovementTypeCreate.as_view(), name="movement_type_create"),
    re_path(r'^outbound_detail_create/$', OutboundDetailCreate.as_view(), name="outbound_detail_create"),
    re_path(r'^inbound_detail_create/$', InboundDetailCreate.as_view(), name="inbound_detail_create"),
    re_path(r'^warehouse_create/$', WarehouseCreate.as_view(), name="warehouse_create"),
    re_path(r'^warehouse_list/$', WarehouseList.as_view(), name="warehouse_list"),
    re_path(r'^movement_list/$', MovementList.as_view(), name="movement_list"),
    re_path(r'^inbound_list/$', InboundList.as_view(), name="inbound_list"),
    re_path(r'^outbound_list/$', OutboundList.as_view(), name="outbound_list"),
    re_path(r'^order_list/$', OrderList.as_view(), name="order_list"),
    re_path(r'^movement_type_list/$', MovementTypeList.as_view(), name="movement_type_list"),
    re_path(r'^warehouse_update/(?P<pk>.+)/$', WarehouseUpdate.as_view(), name="warehouse_update"),
    re_path(r'^movement_update/(?P<pk>.+)/$', MovementUpdate.as_view(),
        name="movement_update"),
    re_path(r'^inbound_update/(?P<pk>.+)/$', InboundUpdate.as_view(),
        name="inbound_update"),
    re_path(r'^outbound_update/(?P<pk>.+)/$', OutboundUpdate.as_view(),
        name="outbound_update"),
    re_path(r'^order_update/(?P<pk>.+)/$', OrderUpdate.as_view(), name="order_update"),
    re_path(r'^order_approve/(?P<code>.+)/$', OrderApprove.as_view(), name="order_approve"),
    re_path(r'^verify_reference_required/$', VerifyReferenceRequired.as_view(),
        name="verify_reference_required"),
    re_path(r'^kardex_product_report/$', KardexProductReport.as_view(), name="kardex_product_report"),
    re_path(r'^movement_report/$', MovementExcelReport.as_view(), name="movement_report"),
    re_path(r'^stock_query/$', StockQuery.as_view(), name="stock_query"),
    re_path(r'^product_warehouse_search/$', ProductWarehouseSearch.as_view(),
        name="product_warehouse_search"),
    re_path(
        r'^movement_excel_report_by_date/(?P<start_date>\d{2}/\d{2}/\d{4})/(?P<end_date>\d{2}/\d{2}/\d{4})/(?P<warehouse>.+)/(?P<movement_type>.+)/$',
        MovementExcelReportByDate.as_view(), name="movement_excel_report_by_date"),
    re_path(r'^movement_pdf/(?P<movement_id>.+)/$', MovementPdfReport.as_view(),
        name="movement_pdf"),
    re_path(r'^kardex_report/$', KardexReport.as_view(), name="kardex_report"),
    re_path(r'^movement_delete/$', MovementDelete.as_view(), name="movement_delete"),
    re_path(r'^warehouse_delete/$', WarehouseDelete.as_view(), name="warehouse_delete"),
    re_path(r'^warehouse_detail/(?P<pk>.+)/$', WarehouseDetail.as_view(), name="warehouse_detail"),
    re_path(r'^movement_type_detail/(?P<pk>.+)/$', MovementTypeDetail.as_view(),
        name="movement_type_detail"),
    re_path(r'^order_detail/(?P<pk>.+)/$', OrderDetailView.as_view(), name="order_detail"),
    re_path(r'^movement_detail_view/(?P<pk>.+)/$', MovementDetailView.as_view(),
        name="movement_detail_view"),
    re_path(r'^warehouse_excel_report/$', WarehouseExcelReport.as_view(), name="warehouse_excel_report"),
    re_path(r'^movement_type_excel_report/$', MovementTypeExcelReport.as_view(),
        name="movement_type_excel_report"),
    re_path(r'^warehouse_import/$', WarehouseImport.as_view(), name="warehouse_import"),
    re_path(r'^initial_inventory_import/$', InitialInventoryImport.as_view(),
        name="initial_inventory_import"),
    re_path(r'^order_approval_list/$', OrderApprovalList.as_view(),
        name="order_approval_list"),
    re_path(r'^verify_stock_for_order/$', VerifyStockForOrder.as_view(),
        name="verify_stock_for_order"),
    re_path(r'^product_stock/$', ProductStock.as_view(), name="product_stock"),
    re_path(r'^movement_list_by_order/(?P<order>.+)/$', MovementListByOrder.as_view(),
        name="movement_list_by_order"),
    re_path(r'^price_reprocess/$', PriceReprocess.as_view(), name="price_reprocess"),
    re_path(r'^movement_list_by_product/$', MovementListByProduct.as_view(),
        name="movement_list_by_product"),
    re_path(r'^order_delete/$', OrderDelete.as_view(), name="order_delete"),
    re_path(r'^product_stock_list/$', ProductStockList.as_view(), name="product_stock_list"),
    re_path(r'^inventory/$', Inventory.as_view(), name="inventory"),

]
