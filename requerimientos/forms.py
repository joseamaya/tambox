# -*- coding: utf-8 -*- 
from django import forms
from contabilidad.models import Configuracion
from django.utils.translation import gettext as _
from model_utils.choices import Choices
from django.forms import formsets
from django.core.exceptions import ValidationError
from requerimientos.models import AprobacionRequerimiento, Requerimiento
from administracion.models import Puesto
from requerimientos.mail import correo_creacion_requerimiento

class AprobacionRequerimientoForm(forms.ModelForm):
    
    class Meta:
        model = AprobacionRequerimiento
        fields =['estado','motivo_desaprobacion']
        
    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop("request")        
        super(AprobacionRequerimientoForm, self).__init__(*args, **kwargs)
        self.fields['motivo_desaprobacion'].widget.attrs['readonly'] = True
        self.fields['motivo_desaprobacion'].required = False        
        self.estado = self.instance.estado
        puesto_usuario = self.request.user.trabajador.puesto_set.all().filter(estado=True)[0]
        oficina_usuario = puesto_usuario.oficina
        requerimiento_oficina = self.instance.requerimiento.oficina
        configuracion = Configuracion.objects.first()
        oficina_administracion = configuracion.administracion
        presupuesto = configuracion.presupuesto
        logistica = configuracion.logistica
        if puesto_usuario.es_jefatura and oficina_usuario==requerimiento_oficina and self.estado==AprobacionRequerimiento.STATUS.PEND:
            self.fields['estado'].choices = Choices(('APROB_JEF', _('APROBADO JEFATURA')),
                                                    ('DESAP_JEF', _('DESAPROBADO JEFATURA')))
        elif oficina_usuario==requerimiento_oficina.gerencia and self.estado==AprobacionRequerimiento.STATUS.APROB_JEF:
            self.fields['estado'].choices = Choices(('APROB_GER_INM', _('APROBADO GERENCIA INMEDIATA')),
                                                    ('DESAP_GER_INM', _('DESAPROBADO GERENCIA INMEDIATA')))            
        elif oficina_usuario == oficina_administracion and self.estado==AprobacionRequerimiento.STATUS.APROB_GER_INM:
            self.fields['estado'].choices = Choices(('APROB_GER_ADM', _('APROBADO GERENCIA ADMINISTRACION')),
                                                    ('DESAP_GER_ADM', _('DESAPROBADO GERENCIA ADMINISTRACION')))
        elif oficina_usuario == logistica and self.estado==AprobacionRequerimiento.STATUS.APROB_GER_ADM:
            self.fields['estado'].choices = Choices(('APROB_LOG', _('APROBADO LOGISTICA')),
                                                    ('DESAP_LOG', _('DESAPROBADO LOGISTICA')))
        elif oficina_usuario == presupuesto and self.estado==AprobacionRequerimiento.STATUS.APROB_LOG:
            self.fields['estado'].choices = Choices(('APROB_PRES', _('APROBADO PRESUPUESTO')),
                                                    ('DESAP_PRES', _('DESAPROBADO PRESUPUESTO')))
        else:
            self.fields['estado'].choices = Choices()
            
    def save(self, *args, **kwargs):
        configuracion = Configuracion.objects.first()
        oficina_administracion = configuracion.administracion
        presupuesto = configuracion.presupuesto
        logistica = configuracion.logistica
        if self.instance.estado==AprobacionRequerimiento.STATUS.APROB_LOG:
            oficina = presupuesto            
        elif self.instance.estado==AprobacionRequerimiento.STATUS.APROB_GER_INM:
            oficina = oficina_administracion
        elif self.instance.estado==AprobacionRequerimiento.STATUS.APROB_GER_ADM:
            oficina = logistica        
        elif self.instance.estado==AprobacionRequerimiento.STATUS.APROB_JEF:
            oficina = self.instance.requerimiento.oficina.gerencia
        else:
            oficina = None
        if oficina is not None:
            puesto_jefe = Puesto.objects.get(oficina=oficina,es_jefatura=True,estado=True)
            jefe = puesto_jefe.trabajador
            destinatario = [jefe.usuario.email]
            correo_creacion_requerimiento(destinatario, self.instance.requerimiento)
        return super(AprobacionRequerimientoForm, self).save(*args, **kwargs)
            
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
    
    def clean_cantidad(self):
        if not self.cleaned_data.get('cantidad'):
            raise ValidationError("La cantidad no es válida.")
        return self.cleaned_data['cantidad']
    
class RequerimientoForm(forms.ModelForm):
    
    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop("request")
        super(RequerimientoForm, self).__init__(*args, **kwargs)
        self.fields['informe'].required = False
        self.fields['codigo'].required = False
        self.fields['observaciones'].required = False
        for field in iter(self.fields):
            if field<>'entrega_directa_solicitante': 
                self.fields[field].widget.attrs.update({
                    'class': 'form-control'
                })
                
    def save(self, *args, **kwargs):
        self.instance.solicitante = self.request.user.trabajador
        puestos = self.request.user.trabajador.puesto_set.all().filter(estado=True)
        self.instance.oficina= puestos[0].oficina
        return super(RequerimientoForm, self).save(*args, **kwargs)
    
    class Meta:
        model = Requerimiento
        fields =['codigo','motivo','mes','observaciones','informe','entrega_directa_solicitante'] 
        
DetalleRequerimientoFormSet = formsets.formset_factory(FormularioDetalleRequerimiento, BaseDetalleRequerimientoFormSet, 0)