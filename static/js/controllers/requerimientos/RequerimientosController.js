angular.module("TamboxApp")
.controller("RequerimientosController",["$scope","$routeSegment",function($scope,$routeSegment){

    $scope.rutaEsRequerimiento=function(){
        return $routeSegment.startsWith("requerimientos.requerimiento");
    };
    $scope.rutaEsAprobacionRequerimientos=function(){
        return $routeSegment.startsWith("requerimientos.aprobacion_requerimientos");
    };
    $scope.rutaEsRequerimientos=function(){
        return $routeSegment.startsWith("requerimientos.requerimientos_requerimientos");
    };
}]);