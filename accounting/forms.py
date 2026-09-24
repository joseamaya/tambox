from django import forms

from tambox.forms import BootstrapFormMixin
from tambox.widgets import NativeDateFieldsMixin
from accounting.models import DocumentType, Account, Upload,\
    Tax, Configuration, PaymentMethod, ExchangeRate, Company, StockType


class PaymentMethodForm(BootstrapFormMixin, forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super(PaymentMethodForm, self).__init__(*args, **kwargs)
        self.fields['credit_days'].widget.attrs.update({'step': '1', 'min': 0})

    class Meta:
        model = PaymentMethod
        fields = ['code', 'description', 'credit_days']


class UploadForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = Upload
        fields = ['file']


class ExchangeRateForm(BootstrapFormMixin, NativeDateFieldsMixin, forms.ModelForm):
    class Meta:
        model = ExchangeRate
        fields = ['amount', 'date']


class DocumentTypeForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = DocumentType
        fields = ['sunat_code', 'name', 'description']


class TaxForm(BootstrapFormMixin, NativeDateFieldsMixin, forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super(TaxForm, self).__init__(*args, **kwargs)
        self.fields['end_date'].required = False

    class Meta:
        model = Tax
        fields = ['abbreviation', 'description', 'amount', 'start_date', 'end_date']


class ConfigurationForm(BootstrapFormMixin, forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super(ConfigurationForm, self).__init__(*args, **kwargs)
        self.fields['purchase_tax'].queryset = Tax.objects.exclude(end_date__isnull=False)

    class Meta:
        model = Configuration
        fields = ['purchase_tax', 'operations', 'administration', 'budget', 'logistics']


class AccountForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = Account
        fields = ['account_number', 'description', 'is_divisional', 'depreciation']


class StockTypeForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = StockType
        fields = ['sunat_code', 'description']
        labels = {'sunat_code': 'Código SUNAT'}


class CompanyForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = Company
        fields = ['business_name', 'tax_id', 'logo', 'place', 'street', 'district',
                  'province', 'department', 'mail_host', 'mail_port', 'username',
                  'password', 'uses_tls']
        labels = {
            'business_name': 'Razón social',
            'tax_id': 'RUC',
            'logo': 'Logo',
            'place': 'Lugar',
            'street': 'Dirección',
            'district': 'Distrito',
            'province': 'Provincia',
            'department': 'Departamento',
            'mail_host': 'Servidor de correo',
            'mail_port': 'Puerto',
            'username': 'Usuario de correo',
            'password': 'Contraseña de correo',
            'uses_tls': 'Usa TLS',
        }
