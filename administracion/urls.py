from django.urls import re_path
from administracion.views import CrearOficina, ListadoOficinas, Tablero, \
    DetalleOficina, ModificarOficina, ListadoTrabajadores, CrearTrabajador, \
    DetalleTrabajador, ModificarTrabajador, ListadoPuestos, CrearPuesto, \
    DetallePuesto, ModificarPuesto, CargarOficinas, CargarTrabajadores, \
    ReporteExcelOficinas, ReporteExcelTrabajadores, CargarPuestos, ModificarNivelAprobacion, \
    ListadoProfesiones, CrearProfesion, DetalleProfesion, ModificarProfesion, \
    ReporteExcelPuestos, ReporteExcelProfesiones, CrearNivelAprobacion, ListadoNivelesAprobacion, \
    DetalleNivelAprobacion, BusquedaReceptorDni, \
    ModificarProductor, DetalleProductor, CrearProductor, ListadoProductores, BusquedaReceptorNombre, CargarProductores

app_name = 'administracion'

urlpatterns = [
    re_path(r'^tablero/$', Tablero.as_view(), name="tablero"),
    re_path(r'^maestro_oficinas/$', ListadoOficinas.as_view(), name="maestro_oficinas"),
    re_path(r'^cargar_oficinas/$', CargarOficinas.as_view(), name="cargar_oficinas"),
    re_path(r'^cargar_trabajadores/$', CargarTrabajadores.as_view(), name="cargar_trabajadores"),
    re_path(r'^cargar_puestos/$', CargarPuestos.as_view(), name="cargar_puestos"),
    re_path(r'^cargar_productores/$', CargarProductores.as_view(), name="cargar_productores"),
    re_path(r'^maestro_oficinas_excel/$', ReporteExcelOficinas.as_view(), name="maestro_oficinas_excel"),
    re_path(r'^maestro_trabajadores_excel/$', ReporteExcelTrabajadores.as_view(),
        name="maestro_trabajadores_excel"),
    re_path(r'^reporte_excel_puestos/$', ReporteExcelPuestos.as_view(), name="reporte_excel_puestos"),
    re_path(r'^reporte_excel_profesiones/$', ReporteExcelProfesiones.as_view(),
        name="reporte_excel_profesiones"),
    re_path(r'^crear_oficina/$', CrearOficina.as_view(), name="crear_oficina"),
    re_path(r'^crear_nivel_aprobacion/$', CrearNivelAprobacion.as_view(), name="crear_nivel_aprobacion"),
    re_path(r'^detalle_oficina/(?P<pk>.+)/$', DetalleOficina.as_view(), name="detalle_oficina"),
    re_path(r'^modificar_oficina/(?P<pk>.+)/$', ModificarOficina.as_view(), name="modificar_oficina"),
    re_path(r'^maestro_trabajadores/$', ListadoTrabajadores.as_view(), name="maestro_trabajadores"),
    re_path(r'^crear_trabajador/$', CrearTrabajador.as_view(), name="crear_trabajador"),
    re_path(r'^detalle_trabajador/(?P<pk>.+)/$', DetalleTrabajador.as_view(), name="detalle_trabajador"),
    re_path(r'^modificar_trabajador/(?P<pk>.+)/$', ModificarTrabajador.as_view(),
        name="modificar_trabajador"),
    re_path(r'^crear_productor/$', CrearProductor.as_view(), name="crear_productor"),
    re_path(r'^detalle_productor/(?P<pk>.+)/$', DetalleProductor.as_view(), name="detalle_productor"),
    re_path(r'^modificar_productor/(?P<pk>.+)/$', ModificarProductor.as_view(), name="modificar_productor"),
    re_path(r'^maestro_productores/$', ListadoProductores.as_view(), name="maestro_productores"),
    re_path(r'^maestro_puestos/$', ListadoPuestos.as_view(), name="maestro_puestos"),
    re_path(r'^busqueda_receptor_dni/$', BusquedaReceptorDni.as_view(), name="busqueda_receptor_dni"),
    re_path(r'^busqueda_receptor_name/$', BusquedaReceptorNombre.as_view(),
        name="busqueda_receptor_name"),
    re_path(r'^crear_puesto/$', CrearPuesto.as_view(), name="crear_puesto"),
    re_path(r'^detalle_puesto/(?P<pk>.+)/$', DetallePuesto.as_view(), name="detalle_puesto"),
    re_path(r'^modificar_puesto/(?P<pk>.+)/$', ModificarPuesto.as_view(), name="modificar_puesto"),
    re_path(r'^maestro_profesiones/$', ListadoProfesiones.as_view(), name="maestro_profesiones"),
    re_path(r'^crear_profesion/$', CrearProfesion.as_view(), name="crear_profesion"),
    re_path(r'^detalle_profesion/(?P<pk>.+)/$', DetalleProfesion.as_view(), name="detalle_profesion"),
    re_path(r'^modificar_profesion/(?P<pk>.+)/$', ModificarProfesion.as_view(), name="modificar_profesion"),
    re_path(r'^maestro_niveles_aprobacion/$', ListadoNivelesAprobacion.as_view(),
        name="maestro_niveles_aprobacion"),
    re_path(r'^detalle_nivel_aprobacion/(?P<pk>.+)/$', DetalleNivelAprobacion.as_view(),
        name="detalle_nivel_aprobacion"),
    re_path(r'^modificar_nivel_aprobacion/(?P<pk>.+)/$', ModificarNivelAprobacion.as_view(),
        name="modificar_nivel_aprobacion"),
]
