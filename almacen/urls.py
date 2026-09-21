from django.urls import re_path
from almacen.views import CrearAlmacen, RegistrarIngresoAlmacen, RegistrarSalidaAlmacen, \
    CrearDetalleSalida, \
    ReportePDFProductos, CrearTipoMovimiento, ListadoAlmacenes, Tablero, ListadoTiposMovimiento, VerificarSolicitaDocumento, \
    ReporteExcelMovimientos, ReporteExcelMovimientosPorFecha, ListadoMovimientos, CrearDetalleIngreso, \
    ConsultaStock, BusquedaProductosAlmacen, ReportePDFMovimiento, ReporteKardex, DetalleAlmacen, \
    EliminarMovimiento, ModificarAlmacen, EliminarAlmacen, DetalleTipoMovimiento, ModificarMovimiento, \
    ReporteExcelAlmacenes, ModificarIngresoAlmacen, ModificarSalidaAlmacen, VerificarPideReferencia, \
    ReporteExcelTiposMovimientos, CrearPedido, \
    CargarAlmacenes, CargarInventarioInicial, CrearDetallePedido, ModificarPedido, ListadoPedidos, AprobarPedido, \
    ListadoAprobacionPedidos, VerificarStockParaPedido, \
    DetalleOperacionPedido, DetalleOperacionMovimiento, StockProductos, \
    ListadoIngresos, ListadoSalidas, ReporteKardexProducto, ListadoMovimientosPorPedido, \
    ReprocesoPrecio, EliminarPedido, MovimientosPorProducto, ListadoStockProducto, Inventario

app_name = 'almacen'

urlpatterns = [
    re_path(r'^tablero/$', Tablero.as_view(), name="tablero"),
    re_path(r'^registrar_ingreso/$', RegistrarIngresoAlmacen.as_view(), name="registrar_ingreso"),
    re_path(r'^registrar_salida/$', RegistrarSalidaAlmacen.as_view(), name="registrar_salida"),
    re_path(r'^crear_pedido/$', CrearPedido.as_view(), name="crear_pedido"),
    re_path(r'^crear_detalle_pedido/$', CrearDetallePedido.as_view(), name="crear_detalle_pedido"),
    re_path(r'^crear_tipo_movimiento/$', CrearTipoMovimiento.as_view(), name="crear_tipo_movimiento"),
    re_path(r'^crear_detalle_salida/$', CrearDetalleSalida.as_view(), name="crear_detalle_salida"),
    re_path(r'^crear_detalle_ingreso/$', CrearDetalleIngreso.as_view(), name="crear_detalle_ingreso"),
    re_path(r'^crear_almacen/$', CrearAlmacen.as_view(), name="crear_almacen"),
    re_path(r'^almacenes/$', ListadoAlmacenes.as_view(), name="almacenes"),
    re_path(r'^movimientos/$', ListadoMovimientos.as_view(), name="movimientos"),
    re_path(r'^listado_ingresos/$', ListadoIngresos.as_view(), name="listado_ingresos"),
    re_path(r'^listado_salidas/$', ListadoSalidas.as_view(), name="listado_salidas"),
    re_path(r'^pedidos/$', ListadoPedidos.as_view(), name="pedidos"),
    re_path(r'^tipos_movimientos/$', ListadoTiposMovimiento.as_view(), name="tipos_movimientos"),
    re_path(r'^modificar_almacen/(?P<pk>.+)/$', ModificarAlmacen.as_view(), name="modificar_almacen"),
    re_path(r'^modificar_movimiento/(?P<pk>.+)/$', ModificarMovimiento.as_view(),
        name="modificar_movimiento"),
    re_path(r'^modificar_ingreso_almacen/(?P<pk>.+)/$', ModificarIngresoAlmacen.as_view(),
        name="modificar_ingreso_almacen"),
    re_path(r'^modificar_salida_almacen/(?P<pk>.+)/$', ModificarSalidaAlmacen.as_view(),
        name="modificar_salida_almacen"),
    re_path(r'^modificar_pedido/(?P<pk>.+)/$', ModificarPedido.as_view(), name="modificar_pedido"),
    re_path(r'^aprobar_pedido/(?P<code>.+)/$', AprobarPedido.as_view(), name="aprobar_pedido"),
    re_path(r'^verificar_solicita_documento/$', VerificarSolicitaDocumento.as_view(),
        name="verificar_solicita_documento"),
    re_path(r'^verificar_pide_referencia/$', VerificarPideReferencia.as_view(),
        name="verificar_pide_referencia"),
    re_path(r'^reporte_kardex_producto/$', ReporteKardexProducto.as_view(), name="reporte_kardex_producto"),
    re_path(r'^reporte_productos/$', ReportePDFProductos.as_view(), name="reporte_productos"),
    re_path(r'^reporte_movimientos/$', ReporteExcelMovimientos.as_view(), name="reporte_movimientos"),
    re_path(r'^consulta_stock/$', ConsultaStock.as_view(), name="consulta_stock"),
    re_path(r'^busqueda_productos_almacen/$', BusquedaProductosAlmacen.as_view(),
        name="busqueda_productos_almacen"),
    re_path(
        r'^movimientos_fecha/(?P<fecha_inicio>\d{2}/\d{2}/\d{4})/(?P<fecha_fin>\d{2}/\d{2}/\d{4})/(?P<almacen>.+)/(?P<tipo_movimiento>.+)/$',
        ReporteExcelMovimientosPorFecha.as_view(), name="movimientos_fecha"),
    re_path(r'^movimiento_pdf/(?P<id_movimiento>.+)/$', ReportePDFMovimiento.as_view(),
        name="movimiento_pdf"),
    re_path(r'^reporte_kardex/$', ReporteKardex.as_view(), name="reporte_kardex"),
    re_path(r'^eliminar_movimiento/$', EliminarMovimiento.as_view(), name="eliminar_movimiento"),
    re_path(r'^eliminar_almacen/$', EliminarAlmacen.as_view(), name="eliminar_almacen"),
    re_path(r'^detalle_almacen/(?P<pk>.+)/$', DetalleAlmacen.as_view(), name="detalle_almacen"),
    re_path(r'^detalle_tipo_movimiento/(?P<pk>.+)/$', DetalleTipoMovimiento.as_view(),
        name="detalle_tipo_movimiento"),
    re_path(r'^detalle_pedido/(?P<pk>.+)/$', DetalleOperacionPedido.as_view(), name="detalle_pedido"),
    re_path(r'^detalle_movimiento/(?P<pk>.+)/$', DetalleOperacionMovimiento.as_view(),
        name="detalle_movimiento"),
    re_path(r'^maestro_almacenes_excel/$', ReporteExcelAlmacenes.as_view(), name="maestro_almacenes_excel"),
    re_path(r'^maestro_tipos_movimientos_excel/$', ReporteExcelTiposMovimientos.as_view(),
        name="maestro_tipos_movimientos_excel"),
    re_path(r'^cargar_almacenes/$', CargarAlmacenes.as_view(), name="cargar_almacenes"),
    re_path(r'^cargar_inventario_inicial/$', CargarInventarioInicial.as_view(),
        name="cargar_inventario_inicial"),
    re_path(r'^listado_aprobacion_pedidos/$', ListadoAprobacionPedidos.as_view(),
        name="listado_aprobacion_pedidos"),
    re_path(r'^verificar_stock_para_pedido/$', VerificarStockParaPedido.as_view(),
        name="verificar_stock_para_pedido"),
    re_path(r'^stock_productos/$', StockProductos.as_view(), name="stock_productos"),
    re_path(r'^listado_movimientos_pedido/(?P<pedido>.+)/$', ListadoMovimientosPorPedido.as_view(),
        name="listado_movimientos_pedido"),
    re_path(r'^reproceso_precio/$', ReprocesoPrecio.as_view(), name="reproceso_precio"),
    re_path(r'^movimientos_por_producto/$', MovimientosPorProducto.as_view(),
        name="movimientos_por_producto"),
    re_path(r'^eliminar_pedido/$', EliminarPedido.as_view(), name="eliminar_pedido"),
    re_path(r'^listado_stock_producto/$', ListadoStockProducto.as_view(), name="listado_stock_producto"),
    re_path(r'^inventario/$', Inventario.as_view(), name="inventario"),

]
