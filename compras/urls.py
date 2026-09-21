from django.urls import re_path
from compras.views import Dashboard, SupplierList, SupplierCreate, PurchaseOrderCreate, \
    SupplierNameSearch, PurchaseOrderDetailCreate, \
    PurchaseOrderTransfer, PurchaseOrderDetailFetch, \
    PurchaseOrderExcelReportByDate, PurchaseOrderList, SupplierDetail, \
    PurchaseOrderUpdate, PurchaseOrderPdfReport, PurchaseOrderXlsReport, PurchaseOrderDelete, SupplierUpdate, \
    SupplierDelete, SupplierExcelReport, ServiceOrderCreate, ServiceOrderDetailCreate, \
    ServiceOrderList, \
    ServiceOrderUpdate, SupplierImport, \
    ServiceConformityCreate, ServiceOrderTransfer, ServiceOrderDetailFetch, ServiceConformityList, \
    ServiceOrderPdfReport, ServiceConformityMemoPdfReport, ServiceConformityUpdate, \
    QuotationCreate, QuotationList, ServiceConformityDetailView, \
    QuotationUpdate, QuotationTransfer, QuotationDetailFetch, \
    QuotationSearch, QuotationDetailView, PurchaseOrderDetailView, ServiceOrderDetailView, \
    QuotationRequestPdfReport, PurchaseOrderListByQuotation, \
    SupplierTaxIdSearch, ServiceOrderListByQuotation, \
    MovementListByPurchaseOrder, ServiceConformityListByServiceOrder, \
    ServiceOrderExcelReportByDate, QuotationDelete, \
    ServiceOrderDelete, ServiceConformityDelete

app_name = 'compras'

urlpatterns = [
    re_path(r'^tablero/$', Dashboard.as_view(), name="tablero"),
    re_path(r'^proveedores/$', SupplierList.as_view(), name="proveedores"),
    re_path(r'^ordenes_compra/$', PurchaseOrderList.as_view(), name="ordenes_compra"),
    re_path(r'^ordenes_servicios/$', ServiceOrderList.as_view(), name="ordenes_servicios"),
    re_path(r'^conformidades_servicio/$', ServiceConformityList.as_view(),
        name="conformidades_servicio"),
    re_path(r'^listado_cotizaciones/$', QuotationList.as_view(), name="listado_cotizaciones"),
    re_path(r'^listado_ordenes_compra_cotizacion/(?P<quotation>.+)/$',
        PurchaseOrderListByQuotation.as_view(), name="listado_ordenes_compra_cotizacion"),
    re_path(r'^listado_ordenes_servicios_cotizacion/(?P<quotation>.+)/$',
        ServiceOrderListByQuotation.as_view(), name="listado_ordenes_servicios_cotizacion"),
    re_path(r'^crear_proveedor/$', SupplierCreate.as_view(), name="crear_proveedor"),
    re_path(r'^crear_orden_compra/$', PurchaseOrderCreate.as_view(), name="crear_orden_compra"),
    re_path(r'^crear_orden_servicios/$', ServiceOrderCreate.as_view(), name="crear_orden_servicios"),
    re_path(r'^crear_conformidad_servicio/$', ServiceConformityCreate.as_view(),
        name="crear_conformidad_servicio"),
    re_path(r'^crear_detalle_orden_compra/$', PurchaseOrderDetailCreate.as_view(),
        name="crear_detalle_orden_compra"),
    re_path(r'^crear_detalle_orden_servicios/$', ServiceOrderDetailCreate.as_view(),
        name="crear_detalle_orden_servicios"),
    re_path(r'^crear_cotizacion/$', QuotationCreate.as_view(), name="crear_cotizacion"),
    re_path(r'^cargar_proveedores/$', SupplierImport.as_view(), name="cargar_proveedores"),
    re_path(r'^modificar_proveedor/(?P<pk>.+)/$', SupplierUpdate.as_view(), name="modificar_proveedor"),
    re_path(r'^modificar_orden_compra/(?P<pk>.+)/$', PurchaseOrderUpdate.as_view(),
        name="modificar_orden_compra"),
    re_path(r'^modificar_orden_servicios/(?P<pk>.+)/$', ServiceOrderUpdate.as_view(),
        name="modificar_orden_servicios"),
    re_path(r'^modificar_conformidad_servicios/(?P<pk>.+)/$', ServiceConformityUpdate.as_view(),
        name="modificar_conformidad_servicios"),
    re_path(r'^modificar_cotizacion/(?P<pk>.+)/$', QuotationUpdate.as_view(),
        name="modificar_cotizacion"),
    re_path(r'^busqueda_cotizacion/$', QuotationSearch.as_view(), name="busqueda_cotizacion"),
    re_path(r'^busqueda_proveedores_razon_social/$', SupplierNameSearch.as_view(),
        name="busqueda_proveedores_razon_social"),
    re_path(r'^busqueda_proveedores_ruc/$', SupplierTaxIdSearch.as_view(),
        name="busqueda_proveedores_ruc"),
    re_path(r'^transferencia_cotizacion/$', QuotationTransfer.as_view(),
        name="transferencia_cotizacion"),
    re_path(r'^transferencia_orden_compra/$', PurchaseOrderTransfer.as_view(),
        name="transferencia_orden_compra"),
    re_path(r'^transferencia_orden_servicios/$', ServiceOrderTransfer.as_view(),
        name="transferencia_orden_servicios"),
    re_path(r'^obtener_detalle_cotizacion/$', QuotationDetailFetch.as_view(),
        name="obtener_detalle_cotizacion"),
    re_path(r'^obtener_detalle_orden_compra/$', PurchaseOrderDetailFetch.as_view(),
        name="obtener_detalle_orden_compra"),
    re_path(r'^obtener_detalle_orden_servicios/$', ServiceOrderDetailFetch.as_view(),
        name="obtener_detalle_orden_servicios"),
    re_path(r'^detalle_proveedor/(?P<pk>\d+)/$', SupplierDetail.as_view(), name="detalle_proveedor"),
    re_path(r'^quotation_detail/(?P<pk>.+)/$', QuotationDetailView.as_view(),
        name="quotation_detail"),
    re_path(r'^purchase_order_detail/(?P<pk>.+)/$', PurchaseOrderDetailView.as_view(),
        name="purchase_order_detail"),
    re_path(r'^service_order_detail/(?P<pk>.+)/$', ServiceOrderDetailView.as_view(),
        name="service_order_detail"),
    re_path(r'^detalle_conformidad_servicios/(?P<pk>.+)/$', ServiceConformityDetailView.as_view(),
        name="detalle_conformidad_servicios"),
    re_path(r'^listado_movimientos_orden_compra/(?P<order>.+)/$',
        MovementListByPurchaseOrder.as_view(), name="listado_movimientos_orden_compra"),
    re_path(r'^listado_conformidades_orden_servicios/(?P<order>.+)/$',
        ServiceConformityListByServiceOrder.as_view(), name="listado_conformidades_orden_servicios"),
    re_path(r'^orden_compra_pdf/(?P<pk>.+)/$', PurchaseOrderPdfReport.as_view(), name="orden_compra_pdf"),
    re_path(r'^orden_compra_xls/(?P<pk>.+)/$', PurchaseOrderXlsReport.as_view(), name="orden_compra_xls"),
    re_path(r'^orden_servicios_pdf/(?P<code>.+)/$', ServiceOrderPdfReport.as_view(),
        name="orden_servicios_pdf"),
    re_path(r'^ver_memorando_conformidad_servicio/(?P<code>.+)/$',
        ServiceConformityMemoPdfReport.as_view(), name="ver_memorando_conformidad_servicio"),
    re_path(r'^cotizacion_pdf/(?P<code>.+)/$', QuotationRequestPdfReport.as_view(),
        name="cotizacion_pdf"),
    re_path(r'^maestro_proveedores_excel/$', SupplierExcelReport.as_view(),
        name="maestro_proveedores_excel"),
    re_path(r'^reporte_ordenes_compra_date/$', PurchaseOrderExcelReportByDate.as_view(),
        name="reporte_ordenes_compra_date"),
    re_path(r'^reporte_ordenes_servicios_date/$', ServiceOrderExcelReportByDate.as_view(),
        name="reporte_ordenes_servicios_date"),
    re_path(r'^eliminar_orden_compra/$', PurchaseOrderDelete.as_view(), name="eliminar_orden_compra"),
    re_path(r'^eliminar_orden_servicios/$', ServiceOrderDelete.as_view(),
        name="eliminar_orden_servicios"),
    re_path(r'^eliminar_cotizacion/$', QuotationDelete.as_view(), name="eliminar_cotizacion"),
    re_path(r'^eliminar_proveedor/$', SupplierDelete.as_view(), name="eliminar_proveedor"),
    re_path(r'^eliminar_conformidad_servicio/$', ServiceConformityDelete.as_view(),
        name="eliminar_conformidad_servicio"),
]
