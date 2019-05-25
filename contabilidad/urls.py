from django.conf.urls import url
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

urlpatterns = [    
    url(r'^tablero/$',login_required(Tablero.as_view()), name="tablero"),
    url(r'^formas_pago/$',login_required(ListadoFormasPago.as_view()), name="formas_pago"),
    url(r'^crear_forma_pago/$',login_required(CrearFormaPago.as_view()), name="crear_forma_pago"),
    url(r'^crear_tipo_cambio/$',login_required(CrearTipoCambio.as_view()), name="crear_tipo_cambio"),
    url(r'^modificar_forma_pago/(?P<pk>.+)/$',login_required(ModificarFormaPago.as_view()), name="modificar_forma_pago"),
    url(r'^detalle_forma_pago/(?P<pk>.+)/$', login_required(DetalleFormaPago.as_view()), name="detalle_forma_pago"),
    url(r'^detalle_tipo_cambio/(?P<pk>.+)/$', login_required(DetalleTipoCambio.as_view()), name="detalle_tipo_cambio"),
    url(r'^maestro_formas_pago_excel/$',login_required(ReporteExcelFormasPago.as_view()), name="maestro_formas_pago_excel"),
    url(r'^eliminar_forma_pago/$',login_required(EliminarFormaPago.as_view()), name="eliminar_forma_pago"),   
    url(r'^cuentas_contables/$',(ListadoCuentasContables.as_view()), name="cuentas_contables"),
    url(r'^tipos_existencias/$',(ListadoTiposExistencias.as_view()), name="tipos_existencias"),
    url(r'^configuracion/$',(CrearConfiguracion.as_view()), name="configuracion"),    
    url(r'^tipos_documentos/$', (ListadoTiposDocumentos.as_view()), name="tipos_documentos"),
    url(r'^tipos_cambio/$', (ListadoTiposCambio.as_view()), name="tipos_cambio"),
    url(r'^impuestos/$', (ListadoImpuestos.as_view()), name="impuestos"),
    url(r'^detalle_tipo_documento/(?P<pk>.+)/$', (DetalleTipoDocumento.as_view()), name="detalle_tipo_documento"),
    url(r'^detalle_cuenta_contable/(?P<pk>.+)/$', (DetalleCuentaContable.as_view()), name="detalle_cuenta_contable"),
    url(r'^detalle_impuesto/(?P<pk>.+)/$', (DetalleImpuesto.as_view()), name="detalle_impuesto"),
    url(r'^cargar_cuentas_contables/$',(CargarCuentasContables.as_view()), name="cargar_cuentas_contables"),
    url(r'^cargar_tipos_documento/$',(CargarTiposDocumentos.as_view()), name="cargar_tipos_documento"),
    url(r'^crear_tipo_documento/$', (CrearTipoDocumento.as_view()), name="crear_tipo_documento"),
    url(r'^crear_impuesto/$', (CrearImpuesto.as_view()), name="crear_impuesto"),
    url(r'^crear_cuenta_contable/$', (CrearCuentaContable.as_view()), name="crear_cuenta_contable"),
    url(r'^cargar_tipos_existencias/$', (CargarTiposExistencias.as_view()), name="cargar_tipos_existencias"),
    url(r'^eliminar_tipo_documento/$',(EliminarTipoDocumento.as_view()), name="eliminar_tipo_documento"),    
    url(r'^modificar_tipo_documento/(?P<pk>.+)/$',(ModificarTipoDocumento.as_view()), name="modificar_tipo_documento"),
    url(r'^modificar_tipo_cambio/(?P<pk>.+)/$',(ModificarTipoCambio.as_view()), name="modificar_tipo_cambio"),
    url(r'^modificar_cuenta_contable/(?P<pk>.+)/$',(ModificarCuentaContable.as_view()), name="modificar_cuenta_contable"),
    url(r'^modificar_impuesto/(?P<pk>.+)/$',(ModificarImpuesto.as_view()), name="modificar_impuesto"),
    url(r'^modificar_configuracion/(?P<pk>.+)/$',(ModificarConfiguracion.as_view()), name="modificar_configuracion"),
    url(r'^maestro_cuentas_contables_excel/$',(ReporteExcelCuentasContables.as_view()), name="maestro_cuentas_contables_excel"),
    url(r'^maestro_tipos_documentos_excel/$',(ReporteExcelTiposDocumentos.as_view()), name="maestro_tipos_documentos_excel"),
    url(r'^obtener_tipo_cambio/$', (ObtenerTipoCambio.as_view()),name="obtener_tipo_cambio"),
]