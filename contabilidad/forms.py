from django import forms
from contabilidad.models import TipoDocumento, CuentaContable, Upload, \
    Impuesto, Configuracion, FormaPago, TipoCambio


class FormaPagoForm(forms.ModelForm):

    def __init__(self, *args, **kwargs):
        super(FormaPagoForm, self).__init__(*args, **kwargs)
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
        model = FormaPago
        fields = ['code', 'description', 'credit_days']


class UploadForm(forms.ModelForm):
    class Meta:
        model = Upload
        fields = ['file']


class TipoCambioForm(forms.ModelForm):
    class Meta:
        model = TipoCambio
        fields = ['amount', 'date']

    def __init__(self, *args, **kwargs):
        super(TipoCambioForm, self).__init__(*args, **kwargs)
        self.fields['date'].input_formats = ['%d/%m/%Y']
        for field in iter(self.fields):
            self.fields[field].widget.attrs.update({
                'class': 'form-control'
            })


class TipoDocumentoForm(forms.ModelForm):
    class Meta:
        model = TipoDocumento
        fields = ['sunat_code', 'name', 'description']

    def __init__(self, *args, **kwargs):
        super(TipoDocumentoForm, self).__init__(*args, **kwargs)
        for field in iter(self.fields):
            self.fields[field].widget.attrs.update({
                'class': 'form-control'
            })


class ImpuestoForm(forms.ModelForm):
    class Meta:
        model = Impuesto
        fields = ['abbreviation', 'description', 'amount', 'start_date', 'end_date']

    def __init__(self, *args, **kwargs):
        super(ImpuestoForm, self).__init__(*args, **kwargs)
        for field in iter(self.fields):
            self.fields[field].widget.attrs.update({
                'class': 'form-control'
            })
        self.fields['end_date'].required = False


class ConfiguracionForm(forms.ModelForm):
    class Meta:
        model = Configuracion
        fields = ['purchase_tax', 'operaciones', 'administracion', 'presupuesto', 'logistica']

    def __init__(self, *args, **kwargs):
        super(ConfiguracionForm, self).__init__(*args, **kwargs)
        for field in iter(self.fields):
            self.fields[field].widget.attrs.update({
                'class': 'form-control'
            })
        self.fields['purchase_tax'].queryset = Impuesto.objects.exclude(end_date__isnull=False)


class CuentaContableForm(forms.ModelForm):
    class Meta:
        model = CuentaContable
        fields = ['account_number', 'description', 'is_divisional', 'depreciation']

    def __init__(self, *args, **kwargs):
        super(CuentaContableForm, self).__init__(*args, **kwargs)
        for field in iter(self.fields):
            if field != 'is_divisional':
                self.fields[field].widget.attrs.update({'class': 'form-control'})
