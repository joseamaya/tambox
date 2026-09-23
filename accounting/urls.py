from django.urls import re_path
from accounting.views import Dashboard, AccountList,\
    AccountImport, DocumentTypeList, DocumentTypeCreate,\
    DocumentTypeDelete, DocumentTypeDetail, DocumentTypeUpdate,\
    AccountExcelReport, AccountUpdate, AccountCreate,\
    AccountDetail, TaxCreate, TaxDetail, TaxList,\
    TaxUpdate, ConfigurationCreate, ConfigurationUpdate,\
    PaymentMethodList, PaymentMethodCreate, PaymentMethodUpdate, PaymentMethodDetail,\
    PaymentMethodExcelReport, PaymentMethodDelete, DocumentTypeExcelReport,\
    DocumentTypeImport, ExchangeRateList, ExchangeRateCreate, ExchangeRateDetail, ExchangeRateUpdate,\
    ExchangeRateFetch, StockTypeList, StockTypeImport

app_name = 'accounting'

urlpatterns = [
    re_path(r'^dashboard/$', Dashboard.as_view(), name="dashboard"),
    re_path(r'^payment_method_list/$', PaymentMethodList.as_view(), name="payment_method_list"),
    re_path(r'^payment_method_create/$', PaymentMethodCreate.as_view(), name="payment_method_create"),
    re_path(r'^exchange_rate_create/$', ExchangeRateCreate.as_view(), name="exchange_rate_create"),
    re_path(r'^payment_method_update/(?P<pk>.+)/$', PaymentMethodUpdate.as_view(),
        name="payment_method_update"),
    re_path(r'^payment_method_detail/(?P<pk>.+)/$', PaymentMethodDetail.as_view(), name="payment_method_detail"),
    re_path(r'^exchange_rate_detail/(?P<pk>.+)/$', ExchangeRateDetail.as_view(), name="exchange_rate_detail"),
    re_path(r'^payment_method_excel_report/$', PaymentMethodExcelReport.as_view(),
        name="payment_method_excel_report"),
    re_path(r'^payment_method_delete/$', PaymentMethodDelete.as_view(), name="payment_method_delete"),
    re_path(r'^account_list/$', AccountList.as_view(), name="account_list"),
    re_path(r'^stock_type_list/$', StockTypeList.as_view(), name="stock_type_list"),
    re_path(r'^configuration/$', ConfigurationCreate.as_view(), name="configuration"),
    re_path(r'^document_type_list/$', DocumentTypeList.as_view(), name="document_type_list"),
    re_path(r'^exchange_rate_list/$', ExchangeRateList.as_view(), name="exchange_rate_list"),
    re_path(r'^tax_list/$', TaxList.as_view(), name="tax_list"),
    re_path(r'^document_type_detail/(?P<pk>.+)/$', DocumentTypeDetail.as_view(),
        name="document_type_detail"),
    re_path(r'^account_detail/(?P<pk>.+)/$', AccountDetail.as_view(),
        name="account_detail"),
    re_path(r'^tax_detail/(?P<pk>.+)/$', TaxDetail.as_view(), name="tax_detail"),
    re_path(r'^account_import/$', AccountImport.as_view(),
        name="account_import"),
    re_path(r'^document_type_import/$', DocumentTypeImport.as_view(), name="document_type_import"),
    re_path(r'^document_type_create/$', DocumentTypeCreate.as_view(), name="document_type_create"),
    re_path(r'^tax_create/$', TaxCreate.as_view(), name="tax_create"),
    re_path(r'^account_create/$', AccountCreate.as_view(), name="account_create"),
    re_path(r'^stock_type_import/$', StockTypeImport.as_view(),
        name="stock_type_import"),
    re_path(r'^document_type_delete/$', DocumentTypeDelete.as_view(), name="document_type_delete"),
    re_path(r'^document_type_update/(?P<pk>.+)/$', DocumentTypeUpdate.as_view(),
        name="document_type_update"),
    re_path(r'^exchange_rate_update/(?P<pk>.+)/$', ExchangeRateUpdate.as_view(),
        name="exchange_rate_update"),
    re_path(r'^account_update/(?P<pk>.+)/$', AccountUpdate.as_view(),
        name="account_update"),
    re_path(r'^tax_update/(?P<pk>.+)/$', TaxUpdate.as_view(), name="tax_update"),
    re_path(r'^configuration_update/(?P<pk>.+)/$', ConfigurationUpdate.as_view(),
        name="configuration_update"),
    re_path(r'^account_excel_report/$', AccountExcelReport.as_view(),
        name="account_excel_report"),
    re_path(r'^document_type_excel_report/$', DocumentTypeExcelReport.as_view(),
        name="document_type_excel_report"),
    re_path(r'^exchange_rate_fetch/$', ExchangeRateFetch.as_view(), name="exchange_rate_fetch"),
]
