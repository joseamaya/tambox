from django.urls import re_path
from almacen.views import WarehouseCreate, InboundCreate, OutboundCreate, \
    OutboundDetailCreate, \
    ProductPdfReport, MovementTypeCreate, WarehouseList, Dashboard, MovementTypeList, VerifyDocumentRequired, \
    MovementExcelReport, MovementExcelReportByDate, MovementList, InboundDetailCreate, \
    StockQuery, ProductWarehouseSearch, MovementPdfReport, KardexReport, WarehouseDetail, \
    MovementDelete, WarehouseUpdate, WarehouseDelete, MovementTypeDetail, MovementUpdate, \
    WarehouseExcelReport, InboundUpdate, OutboundUpdate, VerifyReferenceRequired, \
    MovementTypeExcelReport, OrderCreate, \
    WarehouseImport, InitialInventoryImport, OrderDetailCreate, OrderUpdate, OrderList, OrderApprove, \
    OrderApprovalList, VerifyStockForOrder, \
    OrderDetailView, MovementDetailView, ProductStock, \
    InboundList, OutboundList, KardexProductReport, MovementListByOrder, \
    PriceReprocess, OrderDelete, MovementListByProduct, ProductStockList, Inventory

app_name = 'almacen'

urlpatterns = [
    re_path(r'^tablero/$', Dashboard.as_view(), name="tablero"),
    re_path(r'^registrar_ingreso/$', InboundCreate.as_view(), name="registrar_ingreso"),
    re_path(r'^registrar_salida/$', OutboundCreate.as_view(), name="registrar_salida"),
    re_path(r'^crear_pedido/$', OrderCreate.as_view(), name="crear_pedido"),
    re_path(r'^crear_detalle_pedido/$', OrderDetailCreate.as_view(), name="crear_detalle_pedido"),
    re_path(r'^crear_tipo_movimiento/$', MovementTypeCreate.as_view(), name="crear_tipo_movimiento"),
    re_path(r'^crear_detalle_salida/$', OutboundDetailCreate.as_view(), name="crear_detalle_salida"),
    re_path(r'^crear_detalle_ingreso/$', InboundDetailCreate.as_view(), name="crear_detalle_ingreso"),
    re_path(r'^crear_almacen/$', WarehouseCreate.as_view(), name="crear_almacen"),
    re_path(r'^almacenes/$', WarehouseList.as_view(), name="almacenes"),
    re_path(r'^movimientos/$', MovementList.as_view(), name="movimientos"),
    re_path(r'^listado_ingresos/$', InboundList.as_view(), name="listado_ingresos"),
    re_path(r'^listado_salidas/$', OutboundList.as_view(), name="listado_salidas"),
    re_path(r'^pedidos/$', OrderList.as_view(), name="pedidos"),
    re_path(r'^tipos_movimientos/$', MovementTypeList.as_view(), name="tipos_movimientos"),
    re_path(r'^modificar_almacen/(?P<pk>.+)/$', WarehouseUpdate.as_view(), name="modificar_almacen"),
    re_path(r'^modificar_movimiento/(?P<pk>.+)/$', MovementUpdate.as_view(),
        name="modificar_movimiento"),
    re_path(r'^modificar_ingreso_almacen/(?P<pk>.+)/$', InboundUpdate.as_view(),
        name="modificar_ingreso_almacen"),
    re_path(r'^modificar_salida_almacen/(?P<pk>.+)/$', OutboundUpdate.as_view(),
        name="modificar_salida_almacen"),
    re_path(r'^modificar_pedido/(?P<pk>.+)/$', OrderUpdate.as_view(), name="modificar_pedido"),
    re_path(r'^aprobar_pedido/(?P<code>.+)/$', OrderApprove.as_view(), name="aprobar_pedido"),
    re_path(r'^verificar_solicita_documento/$', VerifyDocumentRequired.as_view(),
        name="verificar_solicita_documento"),
    re_path(r'^verificar_pide_referencia/$', VerifyReferenceRequired.as_view(),
        name="verificar_pide_referencia"),
    re_path(r'^reporte_kardex_producto/$', KardexProductReport.as_view(), name="reporte_kardex_producto"),
    re_path(r'^reporte_productos/$', ProductPdfReport.as_view(), name="reporte_productos"),
    re_path(r'^reporte_movimientos/$', MovementExcelReport.as_view(), name="reporte_movimientos"),
    re_path(r'^consulta_stock/$', StockQuery.as_view(), name="consulta_stock"),
    re_path(r'^busqueda_productos_almacen/$', ProductWarehouseSearch.as_view(),
        name="busqueda_productos_almacen"),
    re_path(
        r'^movimientos_date/(?P<start_date>\d{2}/\d{2}/\d{4})/(?P<end_date>\d{2}/\d{2}/\d{4})/(?P<warehouse>.+)/(?P<movement_type>.+)/$',
        MovementExcelReportByDate.as_view(), name="movimientos_date"),
    re_path(r'^movimiento_pdf/(?P<movement_id>.+)/$', MovementPdfReport.as_view(),
        name="movimiento_pdf"),
    re_path(r'^reporte_kardex/$', KardexReport.as_view(), name="reporte_kardex"),
    re_path(r'^eliminar_movimiento/$', MovementDelete.as_view(), name="eliminar_movimiento"),
    re_path(r'^eliminar_almacen/$', WarehouseDelete.as_view(), name="eliminar_almacen"),
    re_path(r'^detalle_almacen/(?P<pk>.+)/$', WarehouseDetail.as_view(), name="detalle_almacen"),
    re_path(r'^detalle_tipo_movimiento/(?P<pk>.+)/$', MovementTypeDetail.as_view(),
        name="detalle_tipo_movimiento"),
    re_path(r'^order_detail/(?P<pk>.+)/$', OrderDetailView.as_view(), name="order_detail"),
    re_path(r'^detalle_movimiento/(?P<pk>.+)/$', MovementDetailView.as_view(),
        name="detalle_movimiento"),
    re_path(r'^maestro_almacenes_excel/$', WarehouseExcelReport.as_view(), name="maestro_almacenes_excel"),
    re_path(r'^maestro_tipos_movimientos_excel/$', MovementTypeExcelReport.as_view(),
        name="maestro_tipos_movimientos_excel"),
    re_path(r'^cargar_almacenes/$', WarehouseImport.as_view(), name="cargar_almacenes"),
    re_path(r'^cargar_inventario_inicial/$', InitialInventoryImport.as_view(),
        name="cargar_inventario_inicial"),
    re_path(r'^listado_aprobacion_pedidos/$', OrderApprovalList.as_view(),
        name="listado_aprobacion_pedidos"),
    re_path(r'^verificar_stock_para_pedido/$', VerifyStockForOrder.as_view(),
        name="verificar_stock_para_pedido"),
    re_path(r'^stock_productos/$', ProductStock.as_view(), name="stock_productos"),
    re_path(r'^listado_movimientos_pedido/(?P<order>.+)/$', MovementListByOrder.as_view(),
        name="listado_movimientos_pedido"),
    re_path(r'^reproceso_precio/$', PriceReprocess.as_view(), name="reproceso_precio"),
    re_path(r'^movimientos_por_producto/$', MovementListByProduct.as_view(),
        name="movimientos_por_producto"),
    re_path(r'^eliminar_pedido/$', OrderDelete.as_view(), name="eliminar_pedido"),
    re_path(r'^listado_stock_producto/$', ProductStockList.as_view(), name="listado_stock_producto"),
    re_path(r'^inventario/$', Inventory.as_view(), name="inventario"),

]
