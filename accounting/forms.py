from django import forms
from accounting.models import DocumentType, Account, Upload,\
    Tax, Configuration, PaymentMethod, ExchangeRate


class PaymentMethodForm(forms.ModelForm):

    def __init__(self, *args, **kwargs):
        super(PaymentMethodForm, self).__init__(*args, **kwargs)
        for field in iter(self.fields):
            if field == 'credit_days':
                self.fields[field].widget.attrs.update({
                    'class': 'form-control entero',
                    'step': '1',
                    'min': 0,
                })
            else:
                self.fields[field].widget.attrs.update({'class': 'form-control'})

    class Meta:
        model = PaymentMethod
        fields = ['code', 'description', 'credit_days']


class UploadForm(forms.ModelForm):
    class Meta:
        model = Upload
        fields = ['file']


class ExchangeRateForm(forms.ModelForm):
    class Meta:
        model = ExchangeRate
        fields = ['amount', 'date']

    def __init__(self, *args, **kwargs):
        super(ExchangeRateForm, self).__init__(*args, **kwargs)
        self.fields['date'].input_formats = ['%d/%m/%Y']
        for field in iter(self.fields):
            self.fields[field].widget.attrs.update({
                'class': 'form-control'
            })


class DocumentTypeForm(forms.ModelForm):
    class Meta:
        model = DocumentType
        fields = ['sunat_code', 'name', 'description']

    def __init__(self, *args, **kwargs):
        super(DocumentTypeForm, self).__init__(*args, **kwargs)
        for field in iter(self.fields):
            self.fields[field].widget.attrs.update({
                'class': 'form-control'
            })


class TaxForm(forms.ModelForm):
    class Meta:
        model = Tax
        fields = ['abbreviation', 'description', 'amount', 'start_date', 'end_date']

    def __init__(self, *args, **kwargs):
        super(TaxForm, self).__init__(*args, **kwargs)
        for field in iter(self.fields):
            self.fields[field].widget.attrs.update({
                'class': 'form-control'
            })
        self.fields['end_date'].required = False


class ConfigurationForm(forms.ModelForm):
    class Meta:
        model = Configuration
        fields = ['purchase_tax', 'operations', 'administration', 'budget', 'logistics']

    def __init__(self, *args, **kwargs):
        super(ConfigurationForm, self).__init__(*args, **kwargs)
        for field in iter(self.fields):
            self.fields[field].widget.attrs.update({
                'class': 'form-control'
            })
        self.fields['purchase_tax'].queryset = Tax.objects.exclude(end_date__isnull=False)


class AccountForm(forms.ModelForm):
    class Meta:
        model = Account
        fields = ['account_number', 'description', 'is_divisional', 'depreciation']

    def __init__(self, *args, **kwargs):
        super(AccountForm, self).__init__(*args, **kwargs)
        for field in iter(self.fields):
            if field != 'is_divisional':
                self.fields[field].widget.attrs.update({'class': 'form-control'})
