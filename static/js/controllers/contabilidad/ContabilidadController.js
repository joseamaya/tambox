angular.module("TamboxApp")
.controller("ContabilidadController",["$scope","$routeSegment",function($scope,$routeSegment){

    $scope.rutaEsConfiguracion=function(){
        return $routeSegment.startsWith("contabilidad.configuracion");
    };
    $scope.rutaEsCuentasContables=function(){
        return $routeSegment.startsWith("contabilidad.cuentas_contables");
    }
    $scope.rutaEsFormasDePago=function(){
        return $routeSegment.startsWith("contabilidad.formas_de_pago");
    }
    $scope.rutaEsImpuestos=function(){
        return $routeSegment.startsWith("contabilidad.impuestos");
    }
    $scope.rutaEsTiposDeDocumentos=function(){
        return $routeSegment.startsWith("contabilidad.tipos_de_documentos");
    }
}]);