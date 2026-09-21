from django.urls import re_path
from contabilidad.views import Dashboard, AccountList, \
    AccountImport, DocumentTypeList, DocumentTypeCreate, \
    DocumentTypeDelete, DocumentTypeDetail, DocumentTypeUpdate, \
    AccountExcelReport, AccountUpdate, AccountCreate, \
    AccountDetail, TaxCreate, TaxDetail, TaxList, \
    TaxUpdate, ConfigurationCreate, ConfigurationUpdate, \
    PaymentMethodList, PaymentMethodCreate, PaymentMethodUpdate, PaymentMethodDetail, \
    PaymentMethodExcelReport, PaymentMethodDelete, DocumentTypeExcelReport, \
    DocumentTypeImport, ExchangeRateList, ExchangeRateCreate, ExchangeRateDetail, ExchangeRateUpdate, \
    ExchangeRateFetch, StockTypeList, StockTypeImport

app_name = 'contabilidad'

urlpatterns = [
    re_path(r'^tablero/$', Dashboard.as_view(), name="tablero"),
    re_path(r'^formas_pago/$', PaymentMethodList.as_view(), name="formas_pago"),
    re_path(r'^crear_forma_pago/$', PaymentMethodCreate.as_view(), name="crear_forma_pago"),
    re_path(r'^crear_tipo_cambio/$', ExchangeRateCreate.as_view(), name="crear_tipo_cambio"),
    re_path(r'^modificar_forma_pago/(?P<pk>.+)/$', PaymentMethodUpdate.as_view(),
        name="modificar_forma_pago"),
    re_path(r'^detalle_forma_pago/(?P<pk>.+)/$', PaymentMethodDetail.as_view(), name="detalle_forma_pago"),
    re_path(r'^detalle_tipo_cambio/(?P<pk>.+)/$', ExchangeRateDetail.as_view(), name="detalle_tipo_cambio"),
    re_path(r'^maestro_formas_pago_excel/$', PaymentMethodExcelReport.as_view(),
        name="maestro_formas_pago_excel"),
    re_path(r'^eliminar_forma_pago/$', PaymentMethodDelete.as_view(), name="eliminar_forma_pago"),
    re_path(r'^cuentas_contables/$', AccountList.as_view(), name="cuentas_contables"),
    re_path(r'^tipos_existencias/$', StockTypeList.as_view(), name="tipos_existencias"),
    re_path(r'^configuracion/$', ConfigurationCreate.as_view(), name="configuracion"),
    re_path(r'^tipos_documentos/$', DocumentTypeList.as_view(), name="tipos_documentos"),
    re_path(r'^tipos_cambio/$', ExchangeRateList.as_view(), name="tipos_cambio"),
    re_path(r'^impuestos/$', TaxList.as_view(), name="impuestos"),
    re_path(r'^detalle_tipo_documento/(?P<pk>.+)/$', DocumentTypeDetail.as_view(),
        name="detalle_tipo_documento"),
    re_path(r'^detalle_cuenta_contable/(?P<pk>.+)/$', AccountDetail.as_view(),
        name="detalle_cuenta_contable"),
    re_path(r'^detalle_impuesto/(?P<pk>.+)/$', TaxDetail.as_view(), name="detalle_impuesto"),
    re_path(r'^cargar_cuentas_contables/$', AccountImport.as_view(),
        name="cargar_cuentas_contables"),
    re_path(r'^cargar_tipos_documento/$', DocumentTypeImport.as_view(), name="cargar_tipos_documento"),
    re_path(r'^crear_tipo_documento/$', DocumentTypeCreate.as_view(), name="crear_tipo_documento"),
    re_path(r'^crear_impuesto/$', TaxCreate.as_view(), name="crear_impuesto"),
    re_path(r'^crear_cuenta_contable/$', AccountCreate.as_view(), name="crear_cuenta_contable"),
    re_path(r'^cargar_tipos_existencias/$', StockTypeImport.as_view(),
        name="cargar_tipos_existencias"),
    re_path(r'^eliminar_tipo_documento/$', DocumentTypeDelete.as_view(), name="eliminar_tipo_documento"),
    re_path(r'^modificar_tipo_documento/(?P<pk>.+)/$', DocumentTypeUpdate.as_view(),
        name="modificar_tipo_documento"),
    re_path(r'^modificar_tipo_cambio/(?P<pk>.+)/$', ExchangeRateUpdate.as_view(),
        name="modificar_tipo_cambio"),
    re_path(r'^modificar_cuenta_contable/(?P<pk>.+)/$', AccountUpdate.as_view(),
        name="modificar_cuenta_contable"),
    re_path(r'^modificar_impuesto/(?P<pk>.+)/$', TaxUpdate.as_view(), name="modificar_impuesto"),
    re_path(r'^modificar_configuracion/(?P<pk>.+)/$', ConfigurationUpdate.as_view(),
        name="modificar_configuracion"),
    re_path(r'^maestro_cuentas_contables_excel/$', AccountExcelReport.as_view(),
        name="maestro_cuentas_contables_excel"),
    re_path(r'^maestro_tipos_documentos_excel/$', DocumentTypeExcelReport.as_view(),
        name="maestro_tipos_documentos_excel"),
    re_path(r'^obtener_tipo_cambio/$', ExchangeRateFetch.as_view(), name="obtener_tipo_cambio"),
]
