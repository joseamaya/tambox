from django.urls import re_path
from django.contrib.auth.decorators import login_required
from almacen.views import CrearAlmacen, CrearTipoStock, RegistrarIngresoAlmacen, RegistrarSalidaAlmacen, \
    CrearTipoSalida, CrearDetalleSalida, \
    ReportePDFProductos, InicioOperaciones, CrearTipoMovimiento, ListadoAlmacenes, ListadoTiposUnidadMedida, \
    ListadoTiposStock, Tablero, ListadoTiposMovimiento, VerificarSolicitaDocumento, \
    ReporteExcelMovimientos, ReporteExcelMovimientosPorFecha, ListadoMovimientos, CrearDetalleIngreso, \
    ConsultaStock, BusquedaProductosAlmacen, ReportePDFMovimiento, ReporteStock, ReporteKardex, DetalleAlmacen, \
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
    re_path(r'^tablero/$', login_required(Tablero.as_view()), name="tablero"),
    re_path(r'^inicio_operaciones/$', login_required(InicioOperaciones.as_view()), name="inicio_operaciones"),
    re_path(r'^registrar_ingreso/$', login_required(RegistrarIngresoAlmacen.as_view()), name="registrar_ingreso"),
    re_path(r'^registrar_salida/$', login_required(RegistrarSalidaAlmacen.as_view()), name="registrar_salida"),
    re_path(r'^crear_pedido/$', login_required(CrearPedido.as_view()), name="crear_pedido"),
    re_path(r'^crear_detalle_pedido/$', login_required(CrearDetallePedido.as_view()), name="crear_detalle_pedido"),
    re_path(r'^crear_tipo_movimiento/$', login_required(CrearTipoMovimiento.as_view()), name="crear_tipo_movimiento"),
    re_path(r'^crear_tipo_salida/$', login_required(CrearTipoSalida.as_view()), name="crear_tipo_salida"),
    re_path(r'^crear_detalle_salida/$', login_required(CrearDetalleSalida.as_view()), name="crear_detalle_salida"),
    re_path(r'^crear_detalle_ingreso/$', login_required(CrearDetalleIngreso.as_view()), name="crear_detalle_ingreso"),
    re_path(r'^crear_almacen/$', login_required(CrearAlmacen.as_view()), name="crear_almacen"),
    re_path(r'^crear_tipo_stock/$', login_required(CrearTipoStock.as_view()), name="crear_tipo_stock"),
    re_path(r'^almacenes/$', login_required(ListadoAlmacenes.as_view()), name="almacenes"),
    re_path(r'^movimientos/$', login_required(ListadoMovimientos.as_view()), name="movimientos"),
    re_path(r'^listado_ingresos/$', login_required(ListadoIngresos.as_view()), name="listado_ingresos"),
    re_path(r'^listado_salidas/$', login_required(ListadoSalidas.as_view()), name="listado_salidas"),
    re_path(r'^pedidos/$', login_required(ListadoPedidos.as_view()), name="pedidos"),
    re_path(r'^tipos_unidad_medida/$', login_required(ListadoTiposUnidadMedida.as_view()), name="tipos_unidad_medida"),
    re_path(r'^tipos_stock/$', login_required(ListadoTiposStock.as_view()), name="tipos_stock"),
    re_path(r'^tipos_movimientos/$', login_required(ListadoTiposMovimiento.as_view()), name="tipos_movimientos"),
    re_path(r'^modificar_almacen/(?P<pk>.+)/$', login_required(ModificarAlmacen.as_view()), name="modificar_almacen"),
    re_path(r'^modificar_movimiento/(?P<pk>.+)/$', login_required(ModificarMovimiento.as_view()),
        name="modificar_movimiento"),
    re_path(r'^modificar_ingreso_almacen/(?P<pk>.+)/$', login_required(ModificarIngresoAlmacen.as_view()),
        name="modificar_ingreso_almacen"),
    re_path(r'^modificar_salida_almacen/(?P<pk>.+)/$', login_required(ModificarSalidaAlmacen.as_view()),
        name="modificar_salida_almacen"),
    re_path(r'^modificar_pedido/(?P<pk>.+)/$', login_required(ModificarPedido.as_view()), name="modificar_pedido"),
    re_path(r'^aprobar_pedido/(?P<codigo>.+)/$', login_required(AprobarPedido.as_view()), name="aprobar_pedido"),
    re_path(r'^verificar_solicita_documento/$', login_required(VerificarSolicitaDocumento.as_view()),
        name="verificar_solicita_documento"),
    re_path(r'^verificar_pide_referencia/$', login_required(VerificarPideReferencia.as_view()),
        name="verificar_pide_referencia"),
    re_path(r'^reporte_kardex_producto/$', login_required(ReporteKardexProducto.as_view()), name="reporte_kardex_producto"),
    re_path(r'^reporte_productos/$', login_required(ReportePDFProductos), name="reporte_productos"),
    re_path(r'^reporte_movimientos/$', login_required(ReporteExcelMovimientos.as_view()), name="reporte_movimientos"),
    re_path(r'^consulta_stock/$', login_required(ConsultaStock.as_view()), name="consulta_stock"),
    re_path(r'^busqueda_productos_almacen/$', login_required(BusquedaProductosAlmacen.as_view()),
        name="busqueda_productos_almacen"),
    re_path(
        r'^movimientos_fecha/(?P<fecha_inicio>\d{2}/\d{2}/\d{4})/(?P<fecha_fin>\d{2}/\d{2}/\d{4})/(?P<almacen>.+)/(?P<tipo_movimiento>.+)/$',
        login_required(ReporteExcelMovimientosPorFecha.as_view()), name="movimientos_fecha"),
    re_path(r'^movimiento_pdf/(?P<id_movimiento>.+)/$', login_required(ReportePDFMovimiento.as_view()),
        name="movimiento_pdf"),
    re_path(r'^reporte_stock/$', login_required(ReporteStock.as_view()), name="reporte_stock"),
    re_path(r'^reporte_kardex/$', login_required(ReporteKardex.as_view()), name="reporte_kardex"),
    re_path(r'^eliminar_movimiento/$', login_required(EliminarMovimiento.as_view()), name="eliminar_movimiento"),
    re_path(r'^eliminar_almacen/$', login_required(EliminarAlmacen.as_view()), name="eliminar_almacen"),
    re_path(r'^detalle_almacen/(?P<pk>.+)/$', login_required(DetalleAlmacen.as_view()), name="detalle_almacen"),
    re_path(r'^detalle_tipo_movimiento/(?P<pk>.+)/$', login_required(DetalleTipoMovimiento.as_view()),
        name="detalle_tipo_movimiento"),
    re_path(r'^detalle_pedido/(?P<pk>.+)/$', login_required(DetalleOperacionPedido.as_view()), name="detalle_pedido"),
    re_path(r'^detalle_movimiento/(?P<pk>.+)/$', login_required(DetalleOperacionMovimiento.as_view()),
        name="detalle_movimiento"),
    re_path(r'^maestro_almacenes_excel/$', login_required(ReporteExcelAlmacenes.as_view()), name="maestro_almacenes_excel"),
    re_path(r'^maestro_tipos_movimientos_excel/$', login_required(ReporteExcelTiposMovimientos.as_view()),
        name="maestro_tipos_movimientos_excel"),
    re_path(r'^cargar_almacenes/$', login_required(CargarAlmacenes.as_view()), name="cargar_almacenes"),
    re_path(r'^cargar_inventario_inicial/$', login_required(CargarInventarioInicial.as_view()),
        name="cargar_inventario_inicial"),
    re_path(r'^listado_aprobacion_pedidos/$', login_required(ListadoAprobacionPedidos.as_view()),
        name="listado_aprobacion_pedidos"),
    re_path(r'^verificar_stock_para_pedido/$', login_required(VerificarStockParaPedido.as_view()),
        name="verificar_stock_para_pedido"),
    re_path(r'^stock_productos/$', login_required(StockProductos.as_view()), name="stock_productos"),
    re_path(r'^listado_movimientos_pedido/(?P<pedido>.+)/$', login_required(ListadoMovimientosPorPedido.as_view()),
        name="listado_movimientos_pedido"),
    re_path(r'^reproceso_precio/$', login_required(ReprocesoPrecio.as_view()), name="reproceso_precio"),
    re_path(r'^movimientos_por_producto/$', login_required(MovimientosPorProducto.as_view()),
        name="movimientos_por_producto"),
    re_path(r'^eliminar_pedido/$', login_required(EliminarPedido.as_view()), name="eliminar_pedido"),
    re_path(r'^listado_stock_producto/$', login_required(ListadoStockProducto.as_view()), name="listado_stock_producto"),
    re_path(r'^inventario/$', login_required(Inventario.as_view()), name="inventario"),

]
