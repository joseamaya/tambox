# -*- coding: utf-8 -*-
from django import forms
from django.forms import formsets
from django.core.exceptions import ValidationError
from requerimientos.models import RequirementApproval, Requirement
from administracion.models import Position
from requerimientos.mail import correo_creacion_requerimiento
from productos.models import Product


class AprobacionRequerimientoForm(forms.ModelForm):
    class Meta:
        model = RequirementApproval
        fields = ['is_active', 'rejection_reason']

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop("request")
        super(AprobacionRequerimientoForm, self).__init__(*args, **kwargs)
        self.fields['rejection_reason'].widget.attrs['readonly'] = True
        self.fields['rejection_reason'].required = False

    def clean(self):
        office = self.instance.obtener_oficina_aprobacion_superior()
        if office is not None:
            try:
                puesto_jefe = Position.objects.get(office=office, is_leadership=True, is_active=True)
                jefe = puesto_jefe.worker
                destinatario = jefe.user.email
                correo_creacion_requerimiento(destinatario, self.instance.requirement)
            except Position.DoesNotExist:
                raise ValidationError("No existe el puesto superior, imposible continuar.")

    def save(self, *args, **kwargs):
        usuario = self.request.user
        puesto_usuario = usuario.worker.puesto
        oficina_requerimiento = self.instance.requirement.office
        self.instance.level = puesto_usuario.establecer_nivel(oficina_requerimiento)
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
    code = forms.CharField(widget=forms.HiddenInput())
    name = forms.CharField(max_length=100, widget=forms.TextInput(attrs={'size': 35, 'class': 'form-control'}))
    unidad = forms.CharField(max_length=6,
                             widget=forms.TextInput(attrs={'size': 6, 'readonly': "readonly", 'class': 'form-control'}))
    quantity = forms.DecimalField(max_digits=15, decimal_places=5,
                                  widget=forms.TextInput(attrs={'size': 6, 'class': 'decimal form-control'}))
    use = forms.CharField(max_length=100, widget=forms.TextInput(attrs={'class': 'form-control'}))


class FormularioDetalleRequerimiento(forms.Form):
    code = forms.CharField(required=False, widget=forms.TextInput(attrs={'size': 9, 'class': 'form-control'}))
    quantity = forms.DecimalField(widget=forms.TextInput(attrs={'size': 4, 'class': 'form-control cantidad decimal'}))
    product = forms.CharField(widget=forms.TextInput(attrs={'size': 35, 'class': 'form-control productos'}))
    unidad = forms.CharField(required=False,
                             widget=forms.TextInput(attrs={'size': 6, 'readonly': "readonly", 'class': 'form-control'}))
    use = forms.CharField(required=False, widget=forms.Textarea(attrs={'cols': 30, 'rows': 2}))

    def clean_code(self):
        code = self.cleaned_data.get('code')
        try:
            Product.objects.get(code=code)
            return self.cleaned_data['code']
        except Product.DoesNotExist:
            raise ValidationError("El código no es válido.")

    def clean_cantidad(self):
        if not self.cleaned_data.get('quantity'):
            raise ValidationError("La cantidad no es válida.")
        return self.cleaned_data['quantity']


class RequerimientoForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop("request")
        super(RequerimientoForm, self).__init__(*args, **kwargs)
        self.fields['reason'].required = False
        self.fields['report'].required = False
        self.fields['code'].required = False
        self.fields['notes'].required = False
        self.fields['date'].input_formats = ['%d/%m/%Y']
        for field in iter(self.fields):
            if field != 'direct_delivery_to_requester':
                self.fields[field].widget.attrs.update({
                    'class': 'form-control'
                })
            if field == 'year':
                self.fields[field].widget.attrs.update({
                    'class': 'form-control number'
                })

    def save(self, *args, **kwargs):
        self.instance.requester = self.request.user.worker
        return super(RequerimientoForm, self).save(*args, **kwargs)

    class Meta:
        model = Requirement
        fields = ['code', 'reason', 'date', 'month', 'year', 'notes', 'report',
                  'direct_delivery_to_requester']


DetalleRequerimientoFormSet = formsets.formset_factory(FormularioDetalleRequerimiento, BaseDetalleRequerimientoFormSet,
                                                       0)
