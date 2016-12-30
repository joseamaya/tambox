angular.module("TamboxApp")
.controller("NavegacionController",["$scope","$routeSegment",function($scope,$routeSegment){
    $scope.rutaEsAdministracion=function(){
        return $routeSegment.startsWith("administracion");
    };
    $scope.rutaEsAdministracion=function(){
        return $routeSegment.startsWith("almacen");
    };
    $scope.rutaEsAdministracion=function(){
        return $routeSegment.startsWith("compras");
    };
    $scope.rutaEsAdministracion=function(){
        return $routeSegment.startsWith("contabilidad");
    };
    $scope.rutaEsAdministracion=function(){
        return $routeSegment.startsWith("requerimientos");
    };
}]);