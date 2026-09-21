# -*- coding: utf-8 -*-
from django import forms
from compras.models import Proveedor, Cotizacion, OrdenCompra, OrdenServicios, ConformidadServicio
from django.forms import formsets
from requerimientos.models import Requerimiento
from almacen.settings import MESES
from compras.settings import PARAMETROS_BUSQUEDA
from django.core.exceptions import ValidationError


class ProveedorForm(forms.ModelForm):
    class Meta:
        model = Proveedor
        fields = ['ruc', 'razon_social', 'direccion', 'telefono', 'correo', 'estado_sunat', 'condicion', 'ciiu',
                  'registration_date']

    def __init__(self, *args, **kwargs):
        super(ProveedorForm, self).__init__(*args, **kwargs)
        self.fields['ciiu'].required = False
        self.fields['telefono'].required = False
        self.fields['correo'].required = False
        self.fields['estado_sunat'].required = False
        self.fields['condicion'].required = False
        self.fields['registration_date'].input_formats = ['%d/%m/%Y']
        for field in iter(self.fields):
            if field == 'ruc':
                self.fields[field].widget.attrs.update({
                    'class': 'form-control cantidad'
                })

    def clean_ruc(self):
        ruc = self.cleaned_data.get('ruc')
        if len(ruc) != 11:
            raise ValidationError('El RUC debe tener 11 dígitos.')
        return self.cleaned_data['ruc']


class DetalleOrdenCompraForm(forms.Form):
    code = forms.CharField(max_length=14, widget=forms.TextInput(attrs={'size': 17, 'class': 'entero form-control'}))
    nombre = forms.CharField(max_length=100, widget=forms.TextInput(attrs={'size': 35, 'class': 'form-control'}))
    unidad = forms.CharField(max_length=6,
                             widget=forms.TextInput(attrs={'size': 6, 'readonly': "readonly", 'class': 'form-control'}))
    cantidad = forms.DecimalField(max_digits=25, decimal_places=8,
                                  widget=forms.TextInput(attrs={'size': 6, 'class': 'decimal form-control'}))
    precio = forms.DecimalField(max_digits=25, decimal_places=8,
                                widget=forms.TextInput(attrs={'size': 7, 'class': 'decimal form-control'}))
    valor = forms.DecimalField(max_digits=25, decimal_places=8, widget=forms.TextInput(
        attrs={'size': 10, 'readonly': "readonly", 'class': 'form-control'}))


class DetalleOrdenServicioForm(forms.Form):
    code = forms.CharField(widget=forms.HiddenInput())
    cantidad = forms.DecimalField(max_digits=15, decimal_places=5,
                                  widget=forms.TextInput(attrs={'size': 6, 'class': 'decimal form-control'}))
    servicio = forms.CharField(max_length=100, widget=forms.TextInput(attrs={'size': 35, 'class': 'form-control'}))
    description = forms.CharField(widget=forms.Textarea(attrs={'cols': 112, 'rows': 2}))
    precio = forms.DecimalField(max_digits=15, decimal_places=5,
                                widget=forms.TextInput(attrs={'size': 7, 'class': 'decimal form-control'}))
    valor = forms.DecimalField(max_digits=15, decimal_places=5, widget=forms.TextInput(
        attrs={'size': 10, 'readonly': "readonly", 'class': 'form-control'}))


class FormularioReporteOrdenesFecha(forms.Form):
    tipo_busqueda = forms.ChoiceField(widget=forms.RadioSelect(attrs={'class': 'radiobutton'}), label='Seleccione:',
                                      choices=PARAMETROS_BUSQUEDA)
    start_date = forms.CharField(max_length=10, widget=forms.TextInput(attrs={'size': 10, 'class': 'form-control'}),
                                   label='Fecha de Inicio:', required=False)
    end_date = forms.CharField(max_length=10, widget=forms.TextInput(attrs={'size': 10, 'class': 'form-control'}),
                                label='Fecha de Fin:', required=False)
    mes = forms.ChoiceField(choices=MESES, widget=forms.Select(attrs={'class': 'form-control'}), required=False)
    annio = forms.CharField(max_length=4, widget=forms.TextInput(attrs={'size': 4, 'class': 'form-control'}), label='Año',
                            required=False)


class CotizacionForm(forms.ModelForm):
    ruc = forms.CharField(max_length=11, widget=forms.TextInput(attrs={'size': 100, 'class': 'entero form-control'}))
    razon_social = forms.CharField(max_length=100, widget=forms.TextInput(attrs={'size': 100, 'class': 'form-control'}))
    direccion = forms.CharField(max_length=100, widget=forms.TextInput(
        attrs={'size': 100, 'readonly': "readonly", 'class': 'form-control'}))
    referencia = forms.CharField(max_length=100, widget=forms.TextInput(
        attrs={'size': 100, 'readonly': "readonly", 'class': 'form-control'}))
    orden = forms.CharField(max_length=12, widget=forms.TextInput(
        attrs={'size': 100, 'readonly': "readonly", 'class': 'form-control'}), required=False)

    def __init__(self, *args, **kwargs):
        super(CotizacionForm, self).__init__(*args, **kwargs)
        self.fields['code'].required = False
        self.fields['date'].input_formats = ['%d/%m/%Y']
        for field in iter(self.fields):
            self.fields[field].widget.attrs.update({
                'class': 'form-control'
            })

    def clean_orden(self):
        code_orden = self.cleaned_data.get('orden')
        if len(code_orden) != 12 and len(code_orden) != 0:
            raise ValidationError('El código debe tener 12 dígitos.')
        elif len(code_orden) == 12:
            ordenes = OrdenServicios.objects.filter(code=code_orden)
            if len(ordenes) > 0:
                raise ValidationError('La orden ya existe.')
        return self.cleaned_data['orden']

    def clean(self):
        cleaned_data = super(CotizacionForm, self).clean()
        ruc = cleaned_data.get('ruc')
        referencia = cleaned_data.get('referencia')
        cotizacion = Cotizacion.objects.filter(proveedor__ruc=ruc,
                                               requerimiento=referencia)
        if len(cotizacion) > 0:
            raise ValidationError('Ya se ingreso una cotización con este RUC para este requerimiento')
        else:
            return cleaned_data

    def save(self, *args, **kwargs):
        self.instance.proveedor = Proveedor.objects.get(ruc=self.cleaned_data['ruc'])
        self.instance.requerimiento = Requerimiento.objects.get(pk=self.cleaned_data['referencia'])
        return super(CotizacionForm, self).save(*args, **kwargs)

    class Meta:
        model = Cotizacion
        fields = ['code', 'date', 'observaciones']


class OrdenCompraForm(forms.ModelForm):
    ruc = forms.CharField(max_length=11, widget=forms.TextInput(attrs={'size': 100, 'class': 'entero form-control'}))
    razon_social = forms.CharField(max_length=100, widget=forms.TextInput(attrs={'size': 100, 'class': 'form-control'}))
    direccion = forms.CharField(max_length=100, widget=forms.TextInput(
        attrs={'size': 100, 'readonly': "readonly", 'class': 'form-control'}))
    referencia = forms.CharField(max_length=100, widget=forms.TextInput(
        attrs={'size': 100, 'readonly': "readonly", 'class': 'form-control'}))
    impuesto_actual = forms.CharField(widget=forms.HiddenInput())
    subtotal = forms.DecimalField(max_digits=15, decimal_places=5, widget=forms.TextInput(
        attrs={'size': 10, 'readonly': "readonly", 'class': 'form-control'}))
    impuesto = forms.DecimalField(max_digits=15, decimal_places=5, widget=forms.TextInput(
        attrs={'size': 10, 'readonly': "readonly", 'class': 'form-control'}))
    total = forms.DecimalField(max_digits=15, decimal_places=5, widget=forms.TextInput(
        attrs={'size': 10, 'readonly': "readonly", 'class': 'form-control'}))
    total_letras = forms.CharField(max_length=200, widget=forms.TextInput(attrs={'size': 200, 'class': 'form-control'}))

    def __init__(self, *args, **kwargs):
        super(OrdenCompraForm, self).__init__(*args, **kwargs)
        self.fields['code'].required = False
        self.fields['referencia'].required = False
        self.fields['date'].input_formats = ['%d/%m/%Y']
        self.fields['observaciones'].required = False
        for field in iter(self.fields):
            if field != 'con_impuesto' and field != 'dolares':
                self.fields[field].widget.attrs.update({
                    'class': 'form-control'
                })
            if field == 'igv' or field == 'total' or field == 'subtotal' or field == 'total_letras':
                self.fields[field].widget.attrs.update({
                    'readonly': "readonly"
                })

    def clean_code(self):
        code = self.cleaned_data.get('code')
        if len(code) != 12 and len(code) != 0:
            raise ValidationError('El código debe tener 12 dígitos.')
        return self.cleaned_data['code']

    def save(self, *args, **kwargs):
        try:
            self.instance.cotizacion = Cotizacion.objects.get(code=self.cleaned_data['referencia'])
        except Cotizacion.DoesNotExist:
            self.instance.cotizacion = None
            self.instance.proveedor = Proveedor.objects.get(ruc=self.cleaned_data['ruc'])
        return super(OrdenCompraForm, self).save(*args, **kwargs)

    class Meta:
        model = OrdenCompra
        fields = ['code', 'forma_pago', 'date', 'observaciones', 'con_impuesto', 'dolares']


class OrdenServiciosForm(forms.ModelForm):
    ruc = forms.CharField(max_length=11, widget=forms.TextInput(attrs={'size': 100, 'class': 'entero form-control'}))
    razon_social = forms.CharField(max_length=100, widget=forms.TextInput(attrs={'size': 100, 'class': 'form-control'}))
    direccion = forms.CharField(max_length=100, widget=forms.TextInput(
        attrs={'size': 100, 'readonly': "readonly", 'class': 'form-control'}))
    referencia = forms.CharField(max_length=100, widget=forms.TextInput(
        attrs={'size': 100, 'readonly': "readonly", 'class': 'form-control'}))
    subtotal = forms.DecimalField(max_digits=15, decimal_places=5, widget=forms.TextInput(
        attrs={'size': 10, 'readonly': "readonly", 'class': 'form-control'}))
    impuesto = forms.DecimalField(max_digits=15, decimal_places=5, widget=forms.TextInput(
        attrs={'size': 10, 'readonly': "readonly", 'class': 'form-control'}))
    total = forms.DecimalField(max_digits=15, decimal_places=5, widget=forms.TextInput(
        attrs={'size': 10, 'readonly': "readonly", 'class': 'form-control'}))
    total_letras = forms.CharField(max_length=200, widget=forms.TextInput(attrs={'size': 200, 'class': 'form-control'}))

    def __init__(self, *args, **kwargs):
        super(OrdenServiciosForm, self).__init__(*args, **kwargs)
        self.fields['code'].required = False
        self.fields['proceso'].required = False
        self.fields['date'].input_formats = ['%d/%m/%Y']
        self.fields['observaciones'].required = False
        self.fields['nombre_informe'].required = False
        self.fields['informe'].required = False
        self.fields['referencia'].required = False
        for field in iter(self.fields):
            self.fields[field].widget.attrs.update({
                'class': 'form-control'
            })
            if field == 'igv' or field == 'total' or field == 'subtotal' or field == 'total_letras':
                self.fields[field].widget.attrs.update({
                    'readonly': "readonly"
                })

    def clean_code(self):
        code = self.cleaned_data.get('code')
        if len(code) != 12 and len(code) != 0:
            raise ValidationError('El código debe tener 12 dígitos.')
        return self.cleaned_data['code']

    def save(self, *args, **kwargs):
        try:
            self.instance.cotizacion = Cotizacion.objects.get(pk=self.cleaned_data['referencia'])
        except Cotizacion.DoesNotExist:
            self.instance.cotizacion = None
            self.instance.proveedor = Proveedor.objects.get(ruc=self.cleaned_data['ruc'])
        return super(OrdenServiciosForm, self).save(*args, **kwargs)

    class Meta:
        model = OrdenServicios
        fields = ['code', 'forma_pago', 'proceso', 'observaciones', 'date', 'nombre_informe', 'informe']


class ConformidadServicioForm(forms.ModelForm):
    referencia = forms.CharField(max_length=100, widget=forms.TextInput(
        attrs={'size': 100, 'readonly': "readonly", 'class': 'form-control'}))
    subtotal = forms.CharField(max_length=100, widget=forms.TextInput(
        attrs={'size': 100, 'readonly': "readonly", 'class': 'form-control'}))

    def __init__(self, *args, **kwargs):
        super(ConformidadServicioForm, self).__init__(*args, **kwargs)
        self.fields['total'].widget.attrs['readonly'] = True
        self.fields['total_letras'].widget.attrs['readonly'] = True
        self.fields['code'].required = False
        self.fields['doc_sustento'].required = False
        self.fields['archivo'].required = False
        self.fields['date'].input_formats = ['%d/%m/%Y']
        for field in iter(self.fields):
            self.fields[field].widget.attrs.update({
                'class': 'form-control'
            })

    def save(self, *args, **kwargs):
        self.instance.orden_servicios = OrdenServicios.objects.get(pk=self.cleaned_data['referencia'])
        return super(ConformidadServicioForm, self).save(*args, **kwargs)

    class Meta:
        model = ConformidadServicio
        fields = ['code', 'doc_sustento', 'archivo', 'date', 'total', 'total_letras']


class FormularioDetalleCotizacion(forms.Form):
    requerimiento = forms.CharField(widget=forms.HiddenInput())
    code = forms.CharField(max_length=14, widget=forms.TextInput(
        attrs={'size': 14, 'readonly': "readonly", 'class': 'entero form-control'}))
    nombre = forms.CharField(max_length=100, widget=forms.TextInput(
        attrs={'size': 120, 'readonly': "readonly", 'class': 'form-control'}))
    unidad = forms.CharField(max_length=6,
                             widget=forms.TextInput(attrs={'size': 6, 'readonly': "readonly", 'class': 'form-control'}))
    cantidad = forms.DecimalField(max_digits=15, decimal_places=5, widget=forms.TextInput(
        attrs={'size': 6, 'readonly': "readonly", 'class': 'cantidad decimal form-control'}))


class FormularioDetalleOrdenCompra(forms.Form):
    cotizacion = forms.CharField(widget=forms.HiddenInput())
    code = forms.CharField(
        widget=forms.TextInput(attrs={'size': 12, 'readonly': "readonly", 'class': 'entero form-control'}))
    nombre = forms.CharField(widget=forms.TextInput(attrs={'size': 35, 'class': 'productos form-control'}))
    unidad = forms.CharField(widget=forms.TextInput(attrs={'size': 6, 'readonly': "readonly", 'class': 'form-control'}))
    cantidad = forms.DecimalField(max_digits=25, decimal_places=8,
                                  widget=forms.TextInput(attrs={'size': 6, 'class': 'cantidad decimal form-control'}))
    precio = forms.DecimalField(max_digits=25, decimal_places=8,
                                widget=forms.TextInput(attrs={'size': 7, 'class': 'precio decimal form-control'}))
    impuesto = forms.DecimalField(max_digits=25, decimal_places=8, widget=forms.TextInput(
        attrs={'size': 7, 'readonly': "readonly", 'class': 'impuesto decimal form-control'}))
    valor = forms.DecimalField(max_digits=25, decimal_places=8, widget=forms.TextInput(
        attrs={'size': 10, 'readonly': "readonly", 'class': 'form-control'}))


class FormularioDetalleOrdenServicios(forms.Form):
    cotizacion = forms.CharField(widget=forms.HiddenInput())
    code = forms.CharField(widget=forms.HiddenInput())
    nombre = forms.CharField(widget=forms.TextInput(attrs={'size': 35, 'class': 'productos form-control'}))
    unidad = forms.CharField(widget=forms.TextInput(attrs={'size': 6, 'readonly': "readonly", 'class': 'form-control'}))
    cantidad = forms.DecimalField(max_digits=15, decimal_places=5,
                                  widget=forms.TextInput(attrs={'size': 6, 'class': 'cantidad decimal form-control'}))
    precio = forms.DecimalField(max_digits=15, decimal_places=5,
                                widget=forms.TextInput(attrs={'size': 7, 'class': 'precio decimal form-control'}))
    valor = forms.DecimalField(max_digits=15, decimal_places=5, widget=forms.TextInput(
        attrs={'size': 10, 'readonly': "readonly", 'class': 'form-control'}))


class FormularioDetalleConformidadServicio(forms.Form):
    orden_servicios = forms.CharField(widget=forms.HiddenInput())
    cantidad = forms.DecimalField(max_digits=15, decimal_places=5, widget=forms.TextInput(
        attrs={'size': 6, 'readonly': "readonly", 'class': 'cantidad decimal form-control'}))
    servicio = forms.CharField(
        widget=forms.TextInput(attrs={'size': 35, 'readonly': "readonly", 'class': 'form-control'}))
    uso = forms.CharField(widget=forms.TextInput(attrs={'size': 6, 'readonly': "readonly", 'class': 'form-control'}),
                          required=False)
    precio = forms.DecimalField(max_digits=15, decimal_places=5, widget=forms.TextInput(
        attrs={'size': 7, 'readonly': "readonly", 'class': 'precio decimal form-control'}))
    valor = forms.DecimalField(max_digits=15, decimal_places=5, widget=forms.TextInput(
        attrs={'size': 10, 'readonly': "readonly", 'class': 'form-control'}))


class BaseDetalleCotizacionFormSet(formsets.BaseFormSet):

    def clean(self):
        for form in self.forms:
            if form.cleaned_data:
                pass
            else:
                raise forms.ValidationError(
                    'Registro de datos incompletos.',
                    code='datos_incompletos'
                )


class BaseDetalleOrdenCompraFormSet(formsets.BaseFormSet):

    def clean(self):
        for form in self.forms:
            if form.cleaned_data:
                pass
            else:
                raise forms.ValidationError(
                    'Registro de datos incompletos.',
                    code='datos_incompletos'
                )


class BaseDetalleOrdenServiciosFormSet(formsets.BaseFormSet):

    def clean(self):
        for form in self.forms:
            if form.cleaned_data:
                pass
            else:
                raise forms.ValidationError(
                    'Registro de datos incompletos.',
                    code='datos_incompletos'
                )


class BaseDetalleConformidadServicioFormSet(formsets.BaseFormSet):

    def clean(self):
        for form in self.forms:
            if form.cleaned_data:
                pass
            else:
                raise forms.ValidationError(
                    'Registro de datos incompletos.',
                    code='datos_incompletos'
                )


DetalleCotizacionFormSet = formsets.formset_factory(FormularioDetalleCotizacion, BaseDetalleCotizacionFormSet, 0)
DetalleOrdenCompraFormSet = formsets.formset_factory(FormularioDetalleOrdenCompra, BaseDetalleOrdenCompraFormSet, 0)
DetalleOrdenServiciosFormSet = formsets.formset_factory(FormularioDetalleOrdenServicios,
                                                        BaseDetalleOrdenServiciosFormSet, 0)
DetalleConformidadServicioFormSet = formsets.formset_factory(FormularioDetalleConformidadServicio,
                                                             BaseDetalleConformidadServicioFormSet, 0)
