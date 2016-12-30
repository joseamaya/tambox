angular.module("TamboxApp")
.controller("AlmacenController",["$scope","$routeSegment",function($scope,$routeSegment){

    $scope.rutaEsAlmacenes=function(){
        return $routeSegment.startsWith("almacen.almacenes");
    };
    $scope.rutaEsTiposMovimientos=function(){
        return $routeSegment.startsWith("almacen.tipos_movimientos");
    };
    $scope.rutaEsCargarInventarioInicial=function(){
        return $routeSegment.startsWith("almacen.cargar_inventario_inicial");
    };
    $scope.rutaEsCrearPedido=function(){
        return $routeSegment.startsWith("almacen.crear_pedido");
    };
    $scope.rutaEsAprobacionPedidos=function(){
        return $routeSegment.startsWith("almacen.aprobacion_pedidos");
    };
    $scope.rutaEsRegistrarIngreso=function(){
        return $routeSegment.startsWith("almacen.registrar_ingreso");
    };
    $scope.rutaEsRegistrarSalida=function(){
        return $routeSegment.startsWith("almacen.registrar_salida");
    };
    $scope.rutaEsKardex=function(){
        return $routeSegment.startsWith("almacen.kardex");
    };
    $scope.rutaEsKardexProducto=function(){
        return $routeSegment.startsWith("almacen.kardex_producto");
    };
    $scope.rutaEsConsolidadoKardexProductos=function(){
        return $routeSegment.startsWith("almacen.consolidado_kardex_productos");
    };
    $scope.rutaEsConsolidadoKardexGrupos=function(){
        return $routeSegment.startsWith("almacen.consolidado_kardex_grupos");
    };
    $scope.rutaEsMovimientos=function(){
        return $routeSegment.startsWith("almacen.movimientos");
    };
    $scope.rutaEsPedidos=function(){
        return $routeSegment.startsWith("almacen.pedidos");
    };
    $scope.rutaEsMovimientosPorFecha=function(){
        return $routeSegment.startsWith("almacen.movimientos_por_fecha");
    };
    $scope.rutaEsStockDeProductos=function(){
        return $routeSegment.startsWith("almacen.stock_de_productos");
    };
}]);