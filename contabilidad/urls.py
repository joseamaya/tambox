from django.urls import re_path
from django.contrib.auth.decorators import login_required
from contabilidad.views import Tablero, ListadoCuentasContables, \
    CargarCuentasContables, ListadoTiposDocumentos, CrearTipoDocumento, \
    EliminarTipoDocumento, DetalleTipoDocumento, ModificarTipoDocumento, \
    ReporteExcelCuentasContables, ModificarCuentaContable, CrearCuentaContable, \
    DetalleCuentaContable, CrearImpuesto, DetalleImpuesto, ListadoImpuestos, \
    ModificarImpuesto, CrearConfiguracion, ModificarConfiguracion, \
    ListadoFormasPago, CrearFormaPago, ModificarFormaPago, DetalleFormaPago, \
    ReporteExcelFormasPago, EliminarFormaPago, ReporteExcelTiposDocumentos, \
    CargarTiposDocumentos, ListadoTiposCambio, CrearTipoCambio, DetalleTipoCambio, ModificarTipoCambio, \
    ObtenerTipoCambio, ListadoTiposExistencias, CargarTiposExistencias

app_name = 'contabilidad'

urlpatterns = [
    re_path(r'^tablero/$', login_required(Tablero.as_view()), name="tablero"),
    re_path(r'^formas_pago/$', login_required(ListadoFormasPago.as_view()), name="formas_pago"),
    re_path(r'^crear_forma_pago/$', login_required(CrearFormaPago.as_view()), name="crear_forma_pago"),
    re_path(r'^crear_tipo_cambio/$', login_required(CrearTipoCambio.as_view()), name="crear_tipo_cambio"),
    re_path(r'^modificar_forma_pago/(?P<pk>.+)/$', login_required(ModificarFormaPago.as_view()),
        name="modificar_forma_pago"),
    re_path(r'^detalle_forma_pago/(?P<pk>.+)/$', login_required(DetalleFormaPago.as_view()), name="detalle_forma_pago"),
    re_path(r'^detalle_tipo_cambio/(?P<pk>.+)/$', login_required(DetalleTipoCambio.as_view()), name="detalle_tipo_cambio"),
    re_path(r'^maestro_formas_pago_excel/$', login_required(ReporteExcelFormasPago.as_view()),
        name="maestro_formas_pago_excel"),
    re_path(r'^eliminar_forma_pago/$', login_required(EliminarFormaPago.as_view()), name="eliminar_forma_pago"),
    re_path(r'^cuentas_contables/$', login_required(ListadoCuentasContables.as_view()), name="cuentas_contables"),
    re_path(r'^tipos_existencias/$', login_required(ListadoTiposExistencias.as_view()), name="tipos_existencias"),
    re_path(r'^configuracion/$', login_required(CrearConfiguracion.as_view()), name="configuracion"),
    re_path(r'^tipos_documentos/$', login_required(ListadoTiposDocumentos.as_view()), name="tipos_documentos"),
    re_path(r'^tipos_cambio/$', login_required(ListadoTiposCambio.as_view()), name="tipos_cambio"),
    re_path(r'^impuestos/$', login_required(ListadoImpuestos.as_view()), name="impuestos"),
    re_path(r'^detalle_tipo_documento/(?P<pk>.+)/$', login_required(DetalleTipoDocumento.as_view()),
        name="detalle_tipo_documento"),
    re_path(r'^detalle_cuenta_contable/(?P<pk>.+)/$', login_required(DetalleCuentaContable.as_view()),
        name="detalle_cuenta_contable"),
    re_path(r'^detalle_impuesto/(?P<pk>.+)/$', login_required(DetalleImpuesto.as_view()), name="detalle_impuesto"),
    re_path(r'^cargar_cuentas_contables/$', login_required(CargarCuentasContables.as_view()),
        name="cargar_cuentas_contables"),
    re_path(r'^cargar_tipos_documento/$', login_required(CargarTiposDocumentos.as_view()), name="cargar_tipos_documento"),
    re_path(r'^crear_tipo_documento/$', login_required(CrearTipoDocumento.as_view()), name="crear_tipo_documento"),
    re_path(r'^crear_impuesto/$', login_required(CrearImpuesto.as_view()), name="crear_impuesto"),
    re_path(r'^crear_cuenta_contable/$', login_required(CrearCuentaContable.as_view()), name="crear_cuenta_contable"),
    re_path(r'^cargar_tipos_existencias/$', login_required(CargarTiposExistencias.as_view()),
        name="cargar_tipos_existencias"),
    re_path(r'^eliminar_tipo_documento/$', login_required(EliminarTipoDocumento.as_view()), name="eliminar_tipo_documento"),
    re_path(r'^modificar_tipo_documento/(?P<pk>.+)/$', login_required(ModificarTipoDocumento.as_view()),
        name="modificar_tipo_documento"),
    re_path(r'^modificar_tipo_cambio/(?P<pk>.+)/$', login_required(ModificarTipoCambio.as_view()),
        name="modificar_tipo_cambio"),
    re_path(r'^modificar_cuenta_contable/(?P<pk>.+)/$', login_required(ModificarCuentaContable.as_view()),
        name="modificar_cuenta_contable"),
    re_path(r'^modificar_impuesto/(?P<pk>.+)/$', login_required(ModificarImpuesto.as_view()), name="modificar_impuesto"),
    re_path(r'^modificar_configuracion/(?P<pk>.+)/$', login_required(ModificarConfiguracion.as_view()),
        name="modificar_configuracion"),
    re_path(r'^maestro_cuentas_contables_excel/$', login_required(ReporteExcelCuentasContables.as_view()),
        name="maestro_cuentas_contables_excel"),
    re_path(r'^maestro_tipos_documentos_excel/$', login_required(ReporteExcelTiposDocumentos.as_view()),
        name="maestro_tipos_documentos_excel"),
    re_path(r'^obtener_tipo_cambio/$', login_required(ObtenerTipoCambio.as_view()), name="obtener_tipo_cambio"),
]
