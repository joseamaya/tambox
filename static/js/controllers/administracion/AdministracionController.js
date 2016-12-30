angular.module("TamboxApp")
.controller("AdministracionController",["$scope","$routeSegment",function($scope,$routeSegment){

    $scope.rutaEsMaestroNivelesAprobacion=function(){
        return $routeSegment.startsWith("administracion.maestro_niveles_aprobacion");
    };
    $scope.rutaEsMaestroOficinas=function(){
        return $routeSegment.startsWith("administracion.maestro_oficinas");
    };
    $scope.rutaEsMaestroProfesiones=function(){
        return $routeSegment.startsWith("administracion.maestro_profesiones");
    };
    $scope.rutaEsMaestroPuestos=function(){
        return $routeSegment.startsWith("administracion.maestro_puestos");
    };
    $scope.rutaEsMaestroTrabajadores=function(){
        return $routeSegment.startsWith("administracion.maestro_trabajadores");
    };
}]);