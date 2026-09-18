from django.urls import re_path
from django.contrib.auth.decorators import login_required
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
    re_path(r'^tablero/$', login_required(Tablero.as_view()), name="tablero"),
    re_path(r'^maestro_oficinas/$', login_required(ListadoOficinas.as_view()), name="maestro_oficinas"),
    re_path(r'^cargar_oficinas/$', login_required(CargarOficinas.as_view()), name="cargar_oficinas"),
    re_path(r'^cargar_trabajadores/$', login_required(CargarTrabajadores.as_view()), name="cargar_trabajadores"),
    re_path(r'^cargar_puestos/$', login_required(CargarPuestos.as_view()), name="cargar_puestos"),
    re_path(r'^cargar_productores/$', login_required(CargarProductores.as_view()), name="cargar_productores"),
    re_path(r'^maestro_oficinas_excel/$', login_required(ReporteExcelOficinas.as_view()), name="maestro_oficinas_excel"),
    re_path(r'^maestro_trabajadores_excel/$', login_required(ReporteExcelTrabajadores.as_view()),
        name="maestro_trabajadores_excel"),
    re_path(r'^reporte_excel_puestos/$', login_required(ReporteExcelPuestos.as_view()), name="reporte_excel_puestos"),
    re_path(r'^reporte_excel_profesiones/$', login_required(ReporteExcelProfesiones.as_view()),
        name="reporte_excel_profesiones"),
    re_path(r'^crear_oficina/$', login_required(CrearOficina.as_view()), name="crear_oficina"),
    re_path(r'^crear_nivel_aprobacion/$', login_required(CrearNivelAprobacion.as_view()), name="crear_nivel_aprobacion"),
    re_path(r'^detalle_oficina/(?P<pk>.+)/$', login_required(DetalleOficina.as_view()), name="detalle_oficina"),
    re_path(r'^modificar_oficina/(?P<pk>.+)/$', login_required(ModificarOficina.as_view()), name="modificar_oficina"),
    re_path(r'^maestro_trabajadores/$', login_required(ListadoTrabajadores.as_view()), name="maestro_trabajadores"),
    re_path(r'^crear_trabajador/$', login_required(CrearTrabajador.as_view()), name="crear_trabajador"),
    re_path(r'^detalle_trabajador/(?P<pk>.+)/$', login_required(DetalleTrabajador.as_view()), name="detalle_trabajador"),
    re_path(r'^modificar_trabajador/(?P<pk>.+)/$', login_required(ModificarTrabajador.as_view()),
        name="modificar_trabajador"),
    re_path(r'^crear_productor/$', login_required(CrearProductor.as_view()), name="crear_productor"),
    re_path(r'^detalle_productor/(?P<pk>.+)/$', login_required(DetalleProductor.as_view()), name="detalle_productor"),
    re_path(r'^modificar_productor/(?P<pk>.+)/$', login_required(ModificarProductor.as_view()), name="modificar_productor"),
    re_path(r'^maestro_productores/$', login_required(ListadoProductores.as_view()), name="maestro_productores"),
    re_path(r'^maestro_puestos/$', login_required(ListadoPuestos.as_view()), name="maestro_puestos"),
    re_path(r'^busqueda_receptor_dni/$', login_required(BusquedaReceptorDni.as_view()), name="busqueda_receptor_dni"),
    re_path(r'^busqueda_receptor_nombre/$', login_required(BusquedaReceptorNombre.as_view()),
        name="busqueda_receptor_nombre"),
    re_path(r'^crear_puesto/$', login_required(CrearPuesto.as_view()), name="crear_puesto"),
    re_path(r'^detalle_puesto/(?P<pk>.+)/$', login_required(DetallePuesto.as_view()), name="detalle_puesto"),
    re_path(r'^modificar_puesto/(?P<pk>.+)/$', login_required(ModificarPuesto.as_view()), name="modificar_puesto"),
    re_path(r'^maestro_profesiones/$', login_required(ListadoProfesiones.as_view()), name="maestro_profesiones"),
    re_path(r'^crear_profesion/$', login_required(CrearProfesion.as_view()), name="crear_profesion"),
    re_path(r'^detalle_profesion/(?P<pk>.+)/$', login_required(DetalleProfesion.as_view()), name="detalle_profesion"),
    re_path(r'^modificar_profesion/(?P<pk>.+)/$', login_required(ModificarProfesion.as_view()), name="modificar_profesion"),
    re_path(r'^maestro_niveles_aprobacion/$', login_required(ListadoNivelesAprobacion.as_view()),
        name="maestro_niveles_aprobacion"),
    re_path(r'^detalle_nivel_aprobacion/(?P<pk>.+)/$', login_required(DetalleNivelAprobacion.as_view()),
        name="detalle_nivel_aprobacion"),
    re_path(r'^modificar_nivel_aprobacion/(?P<pk>.+)/$', login_required(ModificarNivelAprobacion.as_view()),
        name="modificar_nivel_aprobacion"),
]
