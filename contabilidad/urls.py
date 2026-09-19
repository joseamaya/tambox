from django.urls import re_path
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
    re_path(r'^tablero/$', Tablero.as_view(), name="tablero"),
    re_path(r'^formas_pago/$', ListadoFormasPago.as_view(), name="formas_pago"),
    re_path(r'^crear_forma_pago/$', CrearFormaPago.as_view(), name="crear_forma_pago"),
    re_path(r'^crear_tipo_cambio/$', CrearTipoCambio.as_view(), name="crear_tipo_cambio"),
    re_path(r'^modificar_forma_pago/(?P<pk>.+)/$', ModificarFormaPago.as_view(),
        name="modificar_forma_pago"),
    re_path(r'^detalle_forma_pago/(?P<pk>.+)/$', DetalleFormaPago.as_view(), name="detalle_forma_pago"),
    re_path(r'^detalle_tipo_cambio/(?P<pk>.+)/$', DetalleTipoCambio.as_view(), name="detalle_tipo_cambio"),
    re_path(r'^maestro_formas_pago_excel/$', ReporteExcelFormasPago.as_view(),
        name="maestro_formas_pago_excel"),
    re_path(r'^eliminar_forma_pago/$', EliminarFormaPago.as_view(), name="eliminar_forma_pago"),
    re_path(r'^cuentas_contables/$', ListadoCuentasContables.as_view(), name="cuentas_contables"),
    re_path(r'^tipos_existencias/$', ListadoTiposExistencias.as_view(), name="tipos_existencias"),
    re_path(r'^configuracion/$', CrearConfiguracion.as_view(), name="configuracion"),
    re_path(r'^tipos_documentos/$', ListadoTiposDocumentos.as_view(), name="tipos_documentos"),
    re_path(r'^tipos_cambio/$', ListadoTiposCambio.as_view(), name="tipos_cambio"),
    re_path(r'^impuestos/$', ListadoImpuestos.as_view(), name="impuestos"),
    re_path(r'^detalle_tipo_documento/(?P<pk>.+)/$', DetalleTipoDocumento.as_view(),
        name="detalle_tipo_documento"),
    re_path(r'^detalle_cuenta_contable/(?P<pk>.+)/$', DetalleCuentaContable.as_view(),
        name="detalle_cuenta_contable"),
    re_path(r'^detalle_impuesto/(?P<pk>.+)/$', DetalleImpuesto.as_view(), name="detalle_impuesto"),
    re_path(r'^cargar_cuentas_contables/$', CargarCuentasContables.as_view(),
        name="cargar_cuentas_contables"),
    re_path(r'^cargar_tipos_documento/$', CargarTiposDocumentos.as_view(), name="cargar_tipos_documento"),
    re_path(r'^crear_tipo_documento/$', CrearTipoDocumento.as_view(), name="crear_tipo_documento"),
    re_path(r'^crear_impuesto/$', CrearImpuesto.as_view(), name="crear_impuesto"),
    re_path(r'^crear_cuenta_contable/$', CrearCuentaContable.as_view(), name="crear_cuenta_contable"),
    re_path(r'^cargar_tipos_existencias/$', CargarTiposExistencias.as_view(),
        name="cargar_tipos_existencias"),
    re_path(r'^eliminar_tipo_documento/$', EliminarTipoDocumento.as_view(), name="eliminar_tipo_documento"),
    re_path(r'^modificar_tipo_documento/(?P<pk>.+)/$', ModificarTipoDocumento.as_view(),
        name="modificar_tipo_documento"),
    re_path(r'^modificar_tipo_cambio/(?P<pk>.+)/$', ModificarTipoCambio.as_view(),
        name="modificar_tipo_cambio"),
    re_path(r'^modificar_cuenta_contable/(?P<pk>.+)/$', ModificarCuentaContable.as_view(),
        name="modificar_cuenta_contable"),
    re_path(r'^modificar_impuesto/(?P<pk>.+)/$', ModificarImpuesto.as_view(), name="modificar_impuesto"),
    re_path(r'^modificar_configuracion/(?P<pk>.+)/$', ModificarConfiguracion.as_view(),
        name="modificar_configuracion"),
    re_path(r'^maestro_cuentas_contables_excel/$', ReporteExcelCuentasContables.as_view(),
        name="maestro_cuentas_contables_excel"),
    re_path(r'^maestro_tipos_documentos_excel/$', ReporteExcelTiposDocumentos.as_view(),
        name="maestro_tipos_documentos_excel"),
    re_path(r'^obtener_tipo_cambio/$', ObtenerTipoCambio.as_view(), name="obtener_tipo_cambio"),
]
