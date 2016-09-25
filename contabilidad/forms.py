from django import forms
from contabilidad.models import TipoDocumento, CuentaContable, Upload,\
    Impuesto, Configuracion, FormaPago
    
class FormaPagoForm(forms.ModelForm):

    def __init__(self, *args, **kwargs):
        super(FormaPagoForm, self).__init__(*args, **kwargs)
        for field in iter(self.fields):
            if field=='dias_credito': 
                self.fields[field].widget.attrs.update({
                    'class': 'form-control entero',
                    'step': '1',
                    'min': 0,
                })
            else:
                self.fields[field].widget.attrs.update({'class': 'form-control'})

    class Meta:
        model = FormaPago
        fields = ['codigo','descripcion','dias_credito']

class UploadForm(forms.ModelForm):
    class Meta:
        model = Upload
        fields =['archivo']
    
class TipoDocumentoForm(forms.ModelForm):

    class Meta:
        model = TipoDocumento
        fields =['codigo_sunat','nombre','descripcion']

    def __init__(self, *args, **kwargs):
        super(TipoDocumentoForm, self).__init__(*args, **kwargs)
        for field in iter(self.fields):
            self.fields[field].widget.attrs.update({
                'class': 'form-control'
        })  
            
class ImpuestoForm(forms.ModelForm):

    class Meta:
        model = Impuesto
        fields =['abreviatura','descripcion','monto','fecha_inicio','fecha_fin']

    def __init__(self, *args, **kwargs):
        super(ImpuestoForm, self).__init__(*args, **kwargs)
        for field in iter(self.fields):
            self.fields[field].widget.attrs.update({
                'class': 'form-control'
        })
        self.fields['fecha_fin'].required = False
        
class ConfiguracionForm(forms.ModelForm):

    class Meta:
        model = Configuracion
        fields =['impuesto_compra','administracion','presupuesto','logistica']

    def __init__(self, *args, **kwargs):
        super(ConfiguracionForm, self).__init__(*args, **kwargs)
        for field in iter(self.fields):
            self.fields[field].widget.attrs.update({
                'class': 'form-control'
        })
        self.fields['impuesto_compra'].queryset = Impuesto.objects.exclude(fecha_fin__isnull=False)
            
class CuentaContableForm(forms.ModelForm):

    class Meta:
        model = CuentaContable
        fields = ['cuenta','descripcion','divisionaria','depreciacion']

    def __init__(self, *args, **kwargs):
        super(CuentaContableForm, self).__init__(*args, **kwargs)
        for field in iter(self.fields):
            if field<>'divisionaria':
                self.fields[field].widget.attrs.update({'class': 'form-control'}) 