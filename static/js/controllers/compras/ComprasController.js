angular.module("TamboxApp")
.controller("ComprasController",["$scope","$routeSegment",function($scope,$routeSegment){

    $scope.rutaEsGruposDeProductos=function(){
        return $routeSegment.startsWith("compras.grupos_de_productos");
    };
    $scope.rutaEsProveedores=function(){
        return $routeSegment.startsWith("compras.proveedores");
    };
    $scope.rutaEsProductos=function(){
        return $routeSegment.startsWith("compras.productos");
    };
    $scope.rutaEsServicios=function(){
        return $routeSegment.startsWith("compras.servicios");
    };
    $scope.rutaEsUnidadesDeMedida=function(){
        return $routeSegment.startsWith("compras.unidades_de_medida");
    };
    $scope.rutaEsSolicitudDeCotizacion=function(){
        return $routeSegment.startsWith("compras.solicitud_de_cotizacion");
    };
    $scope.rutaEsOrdenDeCompra=function(){
        return $routeSegment.startsWith("compras.orden_de_compra");
    };
    $scope.rutaEsOrdenDeServicio=function(){
        return $routeSegment.startsWith("compras.orden_de_servicio");
    };
    $scope.rutaEsConformidadServicios=function(){
        return $routeSegment.startsWith("compras.conformidad_servicios");
    };
    $scope.rutaEsCotizaciones=function(){
        return $routeSegment.startsWith("compras.cotizaciones");
    };
    $scope.rutaEsOrdenesDeCompra=function(){
        return $routeSegment.startsWith("compras.ordenes_de_compra");
    };
    $scope.rutaEsOrdenesDeServicio=function(){
        return $routeSegment.startsWith("compras.ordenes_de_servicio");
    };
    $scope.rutaEsConformidadesDeServicio=function(){
        return $routeSegment.startsWith("compras.conformidades_de_servicio");
    };
    $scope.rutaEsOrdenesDeCompraPorFecha=function(){
        return $routeSegment.startsWith("compras.ordenes_de_compra_por_fecha");
    };
}]);