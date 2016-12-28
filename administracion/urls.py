from django.conf.urls import url
from django.contrib.auth.decorators import login_required
from administracion.views import CrearOficina, ListadoOficinas, Tablero,\
    DetalleOficina, ModificarOficina, ListadoTrabajadores, CrearTrabajador,\
    DetalleTrabajador, ModificarTrabajador, ListadoPuestos, CrearPuesto,\
    DetallePuesto, ModificarPuesto, CargarOficinas, CargarTrabajadores,\
    ReporteExcelOficinas, ReporteExcelTrabajadores, CargarPuestos, ModificarNivelAprobacion,\
    ListadoProfesiones, CrearProfesion, DetalleProfesion, ModificarProfesion,\
    ReporteExcelPuestos, ReporteExcelProfesiones, CrearNivelAprobacion, ListadoNivelesAprobacion, DetalleNivelAprobacion

urlpatterns = [
    url(r'^tablero/$',login_required(Tablero.as_view()), name="tablero"),
    url(r'^maestro_oficinas/$',login_required(ListadoOficinas.as_view()), name="maestro_oficinas"),
    url(r'^cargar_oficinas/$',login_required(CargarOficinas.as_view()), name="cargar_oficinas"),
    url(r'^cargar_trabajadores/$',login_required(CargarTrabajadores.as_view()), name="cargar_trabajadores"),
    url(r'^cargar_puestos/$',login_required(CargarPuestos.as_view()), name="cargar_puestos"),
    url(r'^maestro_oficinas_excel/$',login_required(ReporteExcelOficinas.as_view()), name="maestro_oficinas_excel"),
    url(r'^maestro_trabajadores_excel/$',login_required(ReporteExcelTrabajadores.as_view()), name="maestro_trabajadores_excel"),
    url(r'^reporte_excel_puestos/$',login_required(ReporteExcelPuestos.as_view()), name="reporte_excel_puestos"),
    url(r'^reporte_excel_profesiones/$',login_required(ReporteExcelProfesiones.as_view()), name="reporte_excel_profesiones"),
    url(r'^crear_oficina/$',login_required(CrearOficina.as_view()), name="crear_oficina"),
    url(r'^crear_nivel_aprobacion/$',login_required(CrearNivelAprobacion.as_view()), name="crear_nivel_aprobacion"),
    url(r'^detalle_oficina/(?P<pk>.+)/$', login_required(DetalleOficina.as_view()), name="detalle_oficina"),
    url(r'^modificar_oficina/(?P<pk>.+)/$',login_required(ModificarOficina.as_view()), name="modificar_oficina"),
    url(r'^maestro_trabajadores/$',login_required(ListadoTrabajadores.as_view()), name="maestro_trabajadores"),
    url(r'^crear_trabajador/$',login_required(CrearTrabajador.as_view()), name="crear_trabajador"),
    url(r'^detalle_trabajador/(?P<pk>.+)/$', login_required(DetalleTrabajador.as_view()), name="detalle_trabajador"),
    url(r'^modificar_trabajador/(?P<pk>.+)/$',login_required(ModificarTrabajador.as_view()), name="modificar_trabajador"),
    url(r'^maestro_puestos/$',login_required(ListadoPuestos.as_view()), name="maestro_puestos"),
    url(r'^crear_puesto/$',login_required(CrearPuesto.as_view()), name="crear_puesto"),
    url(r'^detalle_puesto/(?P<pk>.+)/$', login_required(DetallePuesto.as_view()), name="detalle_puesto"),
    url(r'^modificar_puesto/(?P<pk>.+)/$',login_required(ModificarPuesto.as_view()), name="modificar_puesto"),
    url(r'^maestro_profesiones/$',login_required(ListadoProfesiones.as_view()), name="maestro_profesiones"),
    url(r'^crear_profesion/$',login_required(CrearProfesion.as_view()), name="crear_profesion"),
    url(r'^detalle_profesion/(?P<pk>.+)/$', login_required(DetalleProfesion.as_view()), name="detalle_profesion"),
    url(r'^modificar_profesion/(?P<pk>.+)/$',login_required(ModificarProfesion.as_view()), name="modificar_profesion"),
    url(r'^maestro_niveles_aprobacion/$',login_required(ListadoNivelesAprobacion.as_view()), name="maestro_niveles_aprobacion"),
    url(r'^detalle_nivel_aprobacion/(?P<pk>.+)/$', login_required(DetalleNivelAprobacion.as_view()), name="detalle_nivel_aprobacion"),
    url(r'^modificar_nivel_aprobacion/(?P<pk>.+)/$',login_required(ModificarNivelAprobacion.as_view()), name="modificar_nivel_aprobacion"),


]