from django.conf.urls import url
from django.contrib.auth.decorators import login_required
from almacen.views import CrearAlmacen, CrearTipoStock, RegistrarIngresoAlmacen,RegistrarSalidaAlmacen, CrearTipoSalida, CrearDetalleSalida,\
    ReportePDFProductos, InicioOperaciones, CrearTipoMovimiento,ListadoAlmacenes,ListadoTiposUnidadMedida,\
    ListadoTiposStock, Tablero, ListadoTiposMovimiento, VerificarSolicitaDocumento,\
    ReporteExcelMovimientos, ReporteExcelMovimientosPorFecha, ListadoMovimientos, CrearDetalleIngreso,\
    ConsultaStock, BusquedaProductosAlmacen, ReportePDFMovimiento, ReporteStock, ReporteExcelKardex,DetalleAlmacen,\
    EliminarMovimiento, ModificarAlmacen, EliminarAlmacen, DetalleTipoMovimiento, ModificarMovimiento,\
    ReporteExcelAlmacenes, ModificarIngresoAlmacen,ModificarSalidaAlmacen, VerificarPideReferencia, ReporteExcelTiposMovimientos, CrearPedido,\
    CargarAlmacenes, CargarInventarioInicial, CrearDetallePedido,ModificarPedido, ListadoPedidos, AprobarPedido, ListadoAprobacionPedidos, VerificarStockParaPedido,\
    DetalleOperacionPedido, DetalleOperacionMovimiento, ListadoStock,\
    ListadoIngresos, ListadoSalidas, ReporteConsolidadoProductosKardexExcel, ReporteConsolidadoGruposKardexExcel,\
    GeneracionKardexProducto, ListadoMovimientosPorPedido

urlpatterns = [
    url(r'^tablero/$',login_required(Tablero.as_view()), name="tablero"),
    url(r'^inicio_operaciones/$', login_required(InicioOperaciones.as_view()), name="inicio_operaciones"),
    url(r'^registrar_ingreso/$',login_required(RegistrarIngresoAlmacen.as_view()), name="registrar_ingreso"),
    url(r'^registrar_salida/$',login_required(RegistrarSalidaAlmacen.as_view()), name="registrar_salida"),
    url(r'^crear_pedido/$',login_required(CrearPedido.as_view()), name="crear_pedido"),
    url(r'^crear_detalle_pedido/$', login_required(CrearDetallePedido.as_view()), name="crear_detalle_pedido"),
    url(r'^crear_tipo_movimiento/$', login_required(CrearTipoMovimiento.as_view()), name="crear_tipo_movimiento"),
    url(r'^crear_tipo_salida/$', login_required(CrearTipoSalida.as_view()), name="crear_tipo_salida"),
    url(r'^crear_detalle_salida/$', login_required(CrearDetalleSalida.as_view()), name="crear_detalle_salida"),
    url(r'^crear_detalle_ingreso/$', login_required(CrearDetalleIngreso.as_view()), name="crear_detalle_ingreso"),
    url(r'^crear_almacen/$', login_required(CrearAlmacen.as_view()), name="crear_almacen"),
    url(r'^crear_tipo_stock/$', login_required(CrearTipoStock.as_view()), name="crear_tipo_stock"),
    url(r'^almacenes/$', login_required(ListadoAlmacenes.as_view()), name="almacenes"),
    url(r'^movimientos/$', login_required(ListadoMovimientos.as_view()), name="movimientos"),
    url(r'^listado_ingresos/$', login_required(ListadoIngresos.as_view()), name="listado_ingresos"),
    url(r'^listado_salidas/$', login_required(ListadoSalidas.as_view()), name="listado_salidas"),
    url(r'^pedidos/$', login_required(ListadoPedidos.as_view()), name="pedidos"),
    url(r'^tipos_unidad_medida/$', login_required(ListadoTiposUnidadMedida.as_view()), name="tipos_unidad_medida"),
    url(r'^tipos_stock/$', login_required(ListadoTiposStock.as_view()), name="tipos_stock"),
    url(r'^tipos_movimientos/$', login_required(ListadoTiposMovimiento.as_view()), name="tipos_movimientos"),
    url(r'^modificar_almacen/(?P<pk>.+)/$',login_required(ModificarAlmacen.as_view()), name="modificar_almacen"),
    url(r'^modificar_movimiento/(?P<id_movimiento>.+)/$', login_required(ModificarMovimiento.as_view()), name="modificar_movimiento"),
    url(r'^modificar_ingreso_almacen/(?P<pk>.+)/$',login_required(ModificarIngresoAlmacen.as_view()), name="modificar_ingreso_almacen"),
    url(r'^modificar_salida_almacen/(?P<pk>.+)/$',login_required(ModificarSalidaAlmacen.as_view()), name="modificar_salida_almacen"),
    url(r'^modificar_pedido/(?P<pk>.+)/$', login_required(ModificarPedido.as_view()), name="modificar_pedido"),
    url(r'^aprobar_pedido/(?P<codigo>.+)/$', login_required(AprobarPedido.as_view()), name="aprobar_pedido"),
    url(r'^verificar_solicita_documento/$', login_required(VerificarSolicitaDocumento.as_view()), name="verificar_solicita_documento"),
    url(r'^verificar_pide_referencia/$', login_required(VerificarPideReferencia.as_view()), name="verificar_pide_referencia"),
    url(r'^generacion_kardex_producto/$', login_required(GeneracionKardexProducto.as_view()), name="generacion_kardex_producto"),
    url(r'^reporte_productos/$', login_required(ReportePDFProductos), name="reporte_productos"),
    url(r'^reporte_movimientos/$', login_required(ReporteExcelMovimientos.as_view()), name="reporte_movimientos"),
    url(r'^consulta_stock/$', login_required(ConsultaStock.as_view()), name="consulta_stock"),
    url(r'^busqueda_productos_almacen/$', login_required(BusquedaProductosAlmacen.as_view()), name="busqueda_productos_almacen"),
    url(r'^movimientos_fecha/(?P<fecha_inicio>\d{2}/\d{2}/\d{4})/(?P<fecha_fin>\d{2}/\d{2}/\d{4})/(?P<almacen>.+)/(?P<tipo_movimiento>.+)/$', login_required(ReporteExcelMovimientosPorFecha.as_view()), name="movimientos_fecha"),
    url(r'^movimiento_pdf/(?P<id_movimiento>.+)/$', login_required(ReportePDFMovimiento.as_view()), name="movimiento_pdf"),
    url(r'^reporte_stock/$',login_required(ReporteStock.as_view()), name="reporte_stock"),
    url(r'^reporte_kardex/$',login_required(ReporteExcelKardex.as_view()), name="reporte_kardex"),
    url(r'^reporte_consolidado_productos_kardex/$',login_required(ReporteConsolidadoProductosKardexExcel.as_view()), name="reporte_consolidado_productos_kardex"),
    url(r'^reporte_consolidado_grupos_kardex/$',login_required(ReporteConsolidadoGruposKardexExcel.as_view()), name="reporte_consolidado_grupos_kardex"),
    url(r'^eliminar_movimiento/$',login_required(EliminarMovimiento.as_view()), name="eliminar_movimiento"),
    url(r'^eliminar_almacen/$',login_required(EliminarAlmacen.as_view()), name="eliminar_almacen"),
    url(r'^detalle_almacen/(?P<pk>.+)/$', login_required(DetalleAlmacen.as_view()), name="detalle_almacen"),
    url(r'^detalle_tipo_movimiento/(?P<pk>.+)/$', login_required(DetalleTipoMovimiento.as_view()), name="detalle_tipo_movimiento"),
    url(r'^detalle_pedido/(?P<pk>.+)/$', login_required(DetalleOperacionPedido.as_view()), name="detalle_pedido"),
    url(r'^detalle_movimiento/(?P<pk>.+)/$', login_required(DetalleOperacionMovimiento.as_view()), name="detalle_movimiento"),
    url(r'^maestro_almacenes_excel/$', login_required(ReporteExcelAlmacenes.as_view()), name="maestro_almacenes_excel"),
    url(r'^maestro_tipos_movimientos_excel/$', login_required(ReporteExcelTiposMovimientos.as_view()), name="maestro_tipos_movimientos_excel"),
    url(r'^cargar_almacenes/$', login_required(CargarAlmacenes.as_view()), name="cargar_almacenes"),
    url(r'^cargar_inventario_inicial/$', login_required(CargarInventarioInicial.as_view()), name="cargar_inventario_inicial"),
    url(r'^listado_aprobacion_pedidos/$',login_required(ListadoAprobacionPedidos.as_view()), name="listado_aprobacion_pedidos"),
    url(r'^verificar_stock_para_pedido/$',login_required(VerificarStockParaPedido.as_view()), name="verificar_stock_para_pedido"),
    url(r'^listado_stock/$', login_required(ListadoStock.as_view()), name="listado_stock"),
    url(r'^listado_movimientos_pedido/(?P<pedido>.+)/$',login_required(ListadoMovimientosPorPedido.as_view()), name="listado_movimientos_pedido"),
]