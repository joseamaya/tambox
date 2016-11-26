# -*- coding: utf-8 -*- 
from django import forms
from contabilidad.models import Configuracion
from django.forms import formsets
from django.core.exceptions import ValidationError
from requerimientos.models import AprobacionRequerimiento, Requerimiento
from administracion.models import Puesto
from requerimientos.mail import correo_creacion_requerimiento
from requerimientos.settings import CHOICES_JEFATURA, CHOICES_GER_INM,\
    CHOICES_GER_ADM, CHOICES_PRES, CHOICES_LOG, CHOICES_VACIA,\
    OFICINA_ADMINISTRACION, LOGISTICA, PRESUPUESTO
from productos.models import Producto

class AprobacionRequerimientoForm(forms.ModelForm):
    
    class Meta:
        model = AprobacionRequerimiento
        fields =['estado','motivo_desaprobacion']
        
    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop("request")        
        super(AprobacionRequerimientoForm, self).__init__(*args, **kwargs)
        self.fields['motivo_desaprobacion'].widget.attrs['readonly'] = True
        self.fields['motivo_desaprobacion'].required = False
        aprobacion = self.instance
        self.estado = aprobacion.estado
        puesto_usuario = self.request.user.trabajador.puesto_set.all().filter(estado=True)[0]
        oficina_usuario = puesto_usuario.oficina
        oficina_requerimiento = aprobacion.requerimiento.oficina
        if aprobacion.verificar_estado_aprobacion(puesto_usuario,
                                                    oficina_usuario,
                                                    LOGISTICA,
                                                    AprobacionRequerimiento.STATUS.PEND):
            self.fields['estado'].choices = CHOICES_LOG
        else:
            self.fields['estado'].choices = CHOICES_VACIA

class BaseDetalleRequerimientoFormSet(formsets.BaseFormSet):
    
    def __init__(self, *args, **kwargs):
        super(BaseDetalleRequerimientoFormSet, self).__init__(*args, **kwargs)
        for form in self.forms:
            form.empty_permitted = False
    
    def clean(self):
        for form in self.forms:
            if form.cleaned_data:
                pass
            else:
                raise forms.ValidationError(
                        'Registro de datos incompletos.',
                        code='datos_incompletos'
                    )
                
class FormularioDetalleRequerimientoProducto(forms.Form):
    codigo = forms.CharField(widget=forms.HiddenInput())
    nombre = forms.CharField(100, widget= forms.TextInput(attrs={'size': 35, 'class': 'form-control'}))
    unidad = forms.CharField(6, widget= forms.TextInput(attrs={'size': 6,'readonly':"readonly", 'class': 'form-control'}))
    cantidad = forms.IntegerField(6, widget= forms.TextInput(attrs={'size': 6, 'class': 'entero form-control'}))
    uso = forms.CharField(100, widget= forms.TextInput(attrs={'class': 'form-control'}))
    
class FormularioDetalleRequerimiento(forms.Form):
    codigo = forms.CharField(12, required=False, widget= forms.TextInput(attrs={'size': 9, 'class': 'form-control'}))
    cantidad = forms.DecimalField(100, widget= forms.TextInput(attrs={'size': 4, 'class': 'form-control cantidad decimal'}))    
    producto = forms.CharField(100, widget= forms.TextInput(attrs={'size': 35, 'class': 'form-control productos'}))
    unidad = forms.CharField(10,required=False, widget= forms.TextInput(attrs={'size': 6,'readonly':"readonly", 'class': 'form-control'}))
    uso = forms.CharField(required=False,widget= forms.Textarea(attrs={'cols': 30, 'rows': 2}))
    
    def clean_codigo(self):
        codigo = self.cleaned_data.get('codigo')
        try:
            producto = Producto.objects.get(codigo=codigo)
            return self.cleaned_data['codigo']
        except Producto.DoesNotExist:
            raise ValidationError("El código no es válido.")
    
    def clean_cantidad(self):
        if not self.cleaned_data.get('cantidad'):
            raise ValidationError("La cantidad no es válida.")
        return self.cleaned_data['cantidad']
    
class RequerimientoForm(forms.ModelForm):
    
    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop("request")
        super(RequerimientoForm, self).__init__(*args, **kwargs)
        self.fields['motivo'].required = False
        self.fields['informe'].required = False
        self.fields['codigo'].required = False
        self.fields['observaciones'].required = False
        self.fields['fecha'].input_formats = ['%d/%m/%Y']
        for field in iter(self.fields):
            if field<>'entrega_directa_solicitante': 
                self.fields[field].widget.attrs.update({
                    'class': 'form-control'
                })
            if field=='annio': 
                self.fields[field].widget.attrs.update({
                    'class': 'form-control numero'                    
                })
                
    def save(self, *args, **kwargs):
        self.instance.solicitante = self.request.user.trabajador
        return super(RequerimientoForm, self).save(*args, **kwargs)
    
    class Meta:
        model = Requerimiento
        fields =['codigo','motivo','fecha','mes','annio','observaciones','informe','entrega_directa_solicitante'] 
        
DetalleRequerimientoFormSet = formsets.formset_factory(FormularioDetalleRequerimiento, BaseDetalleRequerimientoFormSet, 0)