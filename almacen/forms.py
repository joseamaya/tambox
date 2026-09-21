# -*- coding: utf-8 -*-
from django import forms

from administracion.models import Productor, Trabajador
from almacen.models import Almacen, TipoMovimiento, Movimiento, Pedido
from contabilidad.models import Upload
import datetime
from compras.models import OrdenCompra
from django.utils import timezone
from django.forms import formsets
from django.core.exceptions import ValidationError, ObjectDoesNotExist
from almacen.settings import MESES, PARAMETROS, FORMATOS_SUNAT, \
    choices_tipos_movimiento, choices_almacenes, \
    CHOICES_CONSOLIDADO, SELECCION, FORMATOS


class TipoMovimientoForm(forms.ModelForm):
    class Meta:
        model = TipoMovimiento
        fields = ['description', 'sunat_code', 'increases', 'requires_reference', 'is_purchase', 'is_sale']

    def __init__(self, *args, **kwargs):
        self.aestado = True
        super(TipoMovimientoForm, self).__init__(*args, **kwargs)
        self.fields['description'].widget.attrs.update({'class': 'form-control'})
        self.fields['sunat_code'].widget.attrs.update({'class': 'form-control'})

    def save(self, *args, **kwargs):
        self.instance.aestado = self.aestado
        return super(TipoMovimientoForm, self).save(*args, **kwargs)


class AlmacenForm(forms.ModelForm):
    class Meta:
        model = Almacen
        fields = ['code', 'description']

    def __init__(self, *args, **kwargs):
        super(AlmacenForm, self).__init__(*args, **kwargs)
        for field in iter(self.fields):
            self.fields[field].widget.attrs.update({
                'class': 'form-control'
            })


class FormularioDetalleMovimiento(forms.Form):
    warehouse = forms.CharField(widget=forms.HiddenInput())
    code = forms.CharField(max_length=14, widget=forms.TextInput(attrs={'size': 17, 'class': 'entero form-control'}))
    name = forms.CharField(max_length=100, widget=forms.TextInput(attrs={'size': 35, 'class': 'form-control'}))
    unidad = forms.CharField(max_length=6,
                             widget=forms.TextInput(attrs={'size': 6, 'readonly': "readonly", 'class': 'form-control'}))
    quantity = forms.DecimalField(max_digits=25, decimal_places=8,
                                  widget=forms.TextInput(attrs={'size': 6, 'class': 'form-control decimal'}))
    price = forms.DecimalField(max_digits=25, decimal_places=8, widget=forms.TextInput(
        attrs={'size': 7, 'readonly': "readonly", 'class': 'form-control decimal'}))
    amount = forms.DecimalField(max_digits=25, decimal_places=8, widget=forms.TextInput(
        attrs={'size': 10, 'readonly': "readonly", 'class': 'form-control decimal'}))


class FormularioReporteMovimientos(forms.Form):
    tipo_busqueda = forms.ChoiceField(widget=forms.RadioSelect(attrs={'class': 'radiobutton'}), label='Seleccione:',
                                      choices=PARAMETROS)
    desde = forms.DateTimeField(input_formats=['%d/%m/%Y'],
                                widget=forms.TextInput(attrs={'size': 100, 'class': 'form-control'}))
    hasta = forms.DateTimeField(input_formats=['%d/%m/%Y'],
                                widget=forms.TextInput(attrs={'size': 100, 'class': 'form-control'}))
    month = forms.ChoiceField(choices=MESES, widget=forms.Select(attrs={'class': 'form-control'}), required=False)
    year = forms.CharField(max_length=4, widget=forms.TextInput(attrs={'size': 4, 'class': 'form-control'}), label='Año',
                            required=False)
    tipos_movimiento = forms.ChoiceField(choices=[],
                                         widget=forms.Select(attrs={'class': 'form-control'}))
    almacenes = forms.ChoiceField(choices=[], widget=forms.Select(attrs={'class': 'form-control'}))

    def __init__(self, *args, **kwargs):
        super(FormularioReporteMovimientos, self).__init__(*args, **kwargs)
        self.fields['tipos_movimiento'].choices = choices_tipos_movimiento()
        self.fields['almacenes'].choices = choices_almacenes()

    def clean_hasta(self):
        self.cleaned_data['hasta'] = self.cleaned_data.get('hasta') + datetime.timedelta(days=1)
        return self.cleaned_data['hasta']


class MovimientoForm(forms.ModelForm):
    date = forms.CharField(max_length=100, widget=forms.TextInput(attrs={'size': 100, 'class': 'form-control'}))
    hora = forms.CharField(max_length=100, widget=forms.TextInput(attrs={'size': 100, 'class': 'form-control'}))
    doc_referencia = forms.CharField(max_length=100, widget=forms.TextInput(
        attrs={'size': 100, 'readonly': "readonly", 'class': 'form-control'}))
    dni_receptor = forms.CharField(max_length=8, widget=forms.TextInput(
        attrs={'size': 100, 'readonly': "readonly", 'class': 'form-control'}))
    receptor = forms.CharField(max_length=150, widget=forms.TextInput(
        attrs={'size': 100, 'readonly': "readonly", 'class': 'form-control'}))
    cdetalles = forms.CharField(widget=forms.HiddenInput(), initial=0)
    total = forms.DecimalField(max_digits=25, decimal_places=8, widget=forms.TextInput(
        attrs={'size': 10, 'readonly': "readonly", 'class': 'form-control'}))

    def __init__(self, *args, **kwargs):
        self.movement_type = kwargs.pop("movement_type")
        super(MovimientoForm, self).__init__(*args, **kwargs)
        self.fields['movement_id'].required = False
        self.fields['document_type'].required = False
        self.fields['series'].required = False
        self.fields['number'].required = False
        self.fields['notes'].required = False
        self.fields['office'].required = False
        self.fields['dni_receptor'].required = False
        self.fields['receptor'].required = False
        self.fields['doc_referencia'].required = False
        if self.movement_type == 'I':
            self.fields['movement_type'].queryset = TipoMovimiento.objects.filter(increases=True)
        elif self.movement_type == 'S':
            self.fields['movement_type'].queryset = TipoMovimiento.objects.filter(increases=False)
        for field in iter(self.fields):
            self.fields[field].widget.attrs.update({
                'class': 'form-control'
            })

    def clean_dni_receptor(self):
        dni_receptor = self.cleaned_data.get('dni_receptor')
        if dni_receptor != "":
            if self.cleaned_data['movement_type'].is_sale:
                try:
                    Productor.objects.get(dni=self.cleaned_data['dni_receptor'])
                except Productor.DoesNotExist:
                    raise ValidationError("El DNI no corresponde a ningun productor")
            else:
                try:
                    Trabajador.objects.get(dni=self.cleaned_data['dni_receptor'])
                except Trabajador.DoesNotExist:
                    raise ValidationError("El DNI no correspone a ningun trabajador")
        return self.cleaned_data['dni_receptor']

    def obtener_fecha_hora(self, r_date, r_hora):
        r_hora = r_hora.replace(" ", "")
        anio = int(r_date[6:])
        month = int(r_date[3:5])
        dia = int(r_date[0:2])
        horas = int(r_hora[0:2])
        minutos = int(r_hora[3:5])
        segundos = int(r_hora[6:8])
        date = timezone.make_aware(datetime.datetime(anio, month, dia, horas, minutos, segundos))
        return date

    def save(self, *args, **kwargs):
        if self.movement_type == 'I':
            try:
                self.instance.reference = OrdenCompra.objects.get(code=self.cleaned_data['doc_referencia'])
            except ObjectDoesNotExist:
                self.instance.reference = None
        if self.cleaned_data['movement_type'].is_sale:
            try:
                self.instance.producer = Productor.objects.get(dni=self.cleaned_data['dni_receptor'])
            except ObjectDoesNotExist:
                self.instance.producer = None
        else:
            try:
                self.instance.worker = Trabajador.objects.get(dni=self.cleaned_data['dni_receptor'])
            except ObjectDoesNotExist:
                self.instance.worker = None
        self.instance.operation_date = self.obtener_fecha_hora(self.cleaned_data['date'], self.cleaned_data['hora'])
        return super(MovimientoForm, self).save(*args, **kwargs)

    class Meta:
        model = Movimiento
        fields = ['movement_id', 'movement_type', 'document_type', 'series', 'number', 'warehouse', 'office',
                  'notes']


class FormularioKardexProducto(forms.Form):
    almacenes = forms.ModelChoiceField(queryset=Almacen.objects.all(),
                                       widget=forms.Select(attrs={'class': 'form-control'}))
    consolidado = forms.ChoiceField(choices=CHOICES_CONSOLIDADO, widget=forms.RadioSelect, required=False)
    desde = forms.DateTimeField(input_formats=['%d/%m/%Y'],
                                widget=forms.TextInput(attrs={'size': 100, 'class': 'form-control'}))
    hasta = forms.DateTimeField(input_formats=['%d/%m/%Y'],
                                widget=forms.TextInput(attrs={'size': 100, 'class': 'form-control'}))
    cod_producto = forms.CharField(widget=forms.TextInput(attrs={'size': 100, 'class': 'form-control'}), required=False)
    desc_producto = forms.CharField(widget=forms.TextInput(attrs={'size': 100, 'class': 'form-control'}),
                                    required=False)
    formato_sunat = forms.ChoiceField(choices=FORMATOS_SUNAT, widget=forms.RadioSelect, required=False)
    formatos = forms.ChoiceField(choices=FORMATOS, widget=forms.RadioSelect)


class FormularioMovimientosProducto(forms.Form):
    warehouse = forms.ModelChoiceField(queryset=Almacen.objects.all(),
                                     widget=forms.Select(attrs={'class': 'form-control'}))
    desde = forms.DateTimeField(input_formats=['%d/%m/%Y'],
                                widget=forms.TextInput(attrs={'size': 100, 'class': 'form-control'}))
    hasta = forms.DateTimeField(input_formats=['%d/%m/%Y'],
                                widget=forms.TextInput(attrs={'size': 100, 'class': 'form-control'}))
    product = forms.CharField(widget=forms.TextInput(attrs={'size': 100, 'class': 'form-control'}))
    description = forms.CharField(widget=forms.TextInput(attrs={'size': 100, 'class': 'form-control'}))

    def clean_hasta(self):
        self.cleaned_data['hasta'] = self.cleaned_data.get('hasta') + datetime.timedelta(days=1)
        return self.cleaned_data['hasta']


class FormularioReprocesoPrecio(forms.Form):
    warehouse = forms.ModelChoiceField(queryset=Almacen.objects.all(),
                                     widget=forms.Select(attrs={'class': 'form-control'}))
    desde = forms.DateTimeField(input_formats=['%d/%m/%Y'],
                                widget=forms.TextInput(attrs={'size': 100, 'class': 'form-control'}))
    product = forms.CharField(widget=forms.TextInput(attrs={'size': 100, 'class': 'form-control'}), required=False)
    description = forms.CharField(widget=forms.TextInput(attrs={'size': 100, 'class': 'form-control'}), required=False)
    seleccion = forms.ChoiceField(choices=SELECCION, widget=forms.RadioSelect)


class FormularioConsultaStock(forms.Form):
    warehouse = forms.ModelChoiceField(queryset=Almacen.objects.all(),
                                     widget=forms.Select(attrs={'class': 'form-control'}))
    desde = forms.DateTimeField(input_formats=['%d/%m/%Y'],
                                widget=forms.TextInput(attrs={'size': 100, 'class': 'form-control'}))
    product = forms.CharField(widget=forms.TextInput(attrs={'size': 100, 'class': 'form-control'}), required=False)
    description = forms.CharField(widget=forms.TextInput(attrs={'size': 100, 'class': 'form-control'}), required=False)


class CargarInventarioInicialForm(forms.ModelForm):
    almacenes = forms.ModelChoiceField(queryset=Almacen.objects.all(),
                                       widget=forms.Select(attrs={'class': 'form-control'}))
    date = forms.CharField(max_length=100, widget=forms.TextInput(attrs={'size': 100, 'class': 'form-control'}))
    hora = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control', 'type': 'time'}))

    class Meta:
        model = Upload
        fields = ['file']

    def __init__(self, *args, **kwargs):
        super(CargarInventarioInicialForm, self).__init__(*args, **kwargs)
        for field in iter(self.fields):
            self.fields[field].widget.attrs.update({
                'class': 'form-control'
            })


class PedidoForm(forms.ModelForm):

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop("request")
        super(PedidoForm, self).__init__(*args, **kwargs)
        self.fields['code'].required = False
        self.fields['notes'].required = False
        self.fields['date'].input_formats = ['%d/%m/%Y']
        for field in iter(self.fields):
            self.fields[field].widget.attrs.update({
                'class': 'form-control'
            })
            if field == 'total':
                self.fields[field].widget.attrs.update({
                    'readonly': "readonly"
                })

    def save(self, *args, **kwargs):
        self.instance.requester = self.request.user.worker
        puestos = self.request.user.worker.positions.all().filter(is_active=True)
        self.instance.office = puestos[0].office
        return super(PedidoForm, self).save(*args, **kwargs)

    class Meta:
        model = Pedido
        fields = ['code', 'date', 'notes']


class AprobacionPedidoForm(forms.ModelForm):
    cod_pedido = forms.CharField(widget=forms.TextInput(attrs={'size': 100, 'class': 'entero form-control'}))
    date = forms.CharField(max_length=100, widget=forms.TextInput(attrs={'size': 100, 'class': 'form-control'}))
    hora = forms.CharField(max_length=100, widget=forms.TextInput(attrs={'size': 100, 'class': 'form-control'}))
    total = forms.DecimalField(max_digits=15, decimal_places=5, widget=forms.TextInput(attrs={'size': 10,
                                                                                              'readonly': "readonly",
                                                                                              'class': 'form-control'}))

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop("request")
        super(AprobacionPedidoForm, self).__init__(*args, **kwargs)
        self.fields['notes'].required = False
        self.fields['date'].input_formats = ['%d/%m/%Y']
        for field in iter(self.fields):
            self.fields[field].widget.attrs.update({
                'class': 'form-control'
            })

    def obtener_fecha_hora(self, r_date, r_hora):
        r_hora = r_hora.replace(" ", "")
        anio = int(r_date[6:])
        month = int(r_date[3:5])
        dia = int(r_date[0:2])
        horas = int(r_hora[0:2])
        minutos = int(r_hora[3:5])
        segundos = int(r_hora[6:8])
        date = timezone.make_aware(datetime.datetime(anio, month, dia, horas, minutos, segundos))
        return date

    def save(self, *args, **kwargs):
        self.instance.order = Pedido.objects.get(code=self.cleaned_data['cod_pedido'])
        self.instance.operation_date = self.obtener_fecha_hora(self.cleaned_data['date'], self.cleaned_data['hora'])
        self.instance.movement_type = TipoMovimiento.objects.get(code="S01")
        self.instance.office = self.instance.order.office
        return super(AprobacionPedidoForm, self).save(*args, **kwargs)

    class Meta:
        model = Movimiento
        fields = ['warehouse', 'notes']


class FormularioPedido(forms.Form):
    cod_pedido = forms.CharField(max_length=100, widget=forms.TextInput(attrs={'size': 100, 'class': 'form-control'}))
    almacenes = forms.ModelChoiceField(queryset=Almacen.objects.all(),
                                       widget=forms.Select(attrs={'class': 'form-control'}))
    date = forms.CharField(max_length=100, widget=forms.TextInput(attrs={'size': 100, 'class': 'form-control'}))
    notes = forms.CharField(widget=forms.Textarea(attrs={'cols': 141, 'rows': 5}))
    total = forms.CharField(max_length=100, widget=forms.TextInput(
        attrs={'size': 100, 'readonly': "readonly", 'class': 'form-control'}))


class FormularioDetallePedido(forms.Form):
    code = forms.CharField(max_length=14, widget=forms.TextInput(
        attrs={'size': 17, 'readonly': "readonly", 'class': 'entero form-control'}))
    name = forms.CharField(max_length=100, widget=forms.TextInput(attrs={'size': 35, 'class': 'form-control productos'}))
    unidad = forms.CharField(max_length=20,
                             widget=forms.TextInput(attrs={'size': 6, 'readonly': "readonly", 'class': 'form-control'}))
    quantity = forms.DecimalField(max_digits=15, decimal_places=5,
                                  widget=forms.TextInput(attrs={'size': 6, 'class': 'cantidad decimal form-control'}))


class FormularioDetalleIngreso(forms.Form):
    orden_compra = forms.CharField(widget=forms.HiddenInput())
    code = forms.CharField(
        widget=forms.TextInput(attrs={'size': 8, 'readonly': "readonly", 'class': 'entero form-control'}))
    name = forms.CharField(widget=forms.TextInput(attrs={'size': 35, 'class': 'productos form-control'}))
    unidad = forms.CharField(widget=forms.TextInput(attrs={'size': 5, 'readonly': "readonly", 'class': 'form-control'}))
    quantity = forms.DecimalField(max_digits=25, decimal_places=8,
                                  widget=forms.TextInput(attrs={'size': 6, 'class': 'cantidad decimal form-control'}))
    price = forms.DecimalField(max_digits=25, decimal_places=8,
                                widget=forms.TextInput(attrs={'size': 7, 'class': 'precio decimal form-control'}))
    amount = forms.DecimalField(max_digits=25, decimal_places=8, widget=forms.TextInput(
        attrs={'size': 10, 'readonly': "readonly", 'class': 'form-control'}))


class BaseDetalleIngresoFormSet(formsets.BaseFormSet):

    def clean(self):
        for form in self.forms:
            if form.cleaned_data:
                pass
            else:
                raise forms.ValidationError(
                    'Registro de datos incompletos.',
                    code='datos_incompletos'
                )


class FormularioDetalleSalida(forms.Form):
    order = forms.CharField(widget=forms.HiddenInput(), required=False)
    code = forms.CharField(
        widget=forms.TextInput(attrs={'size': 8, 'readonly': "readonly", 'class': 'entero form-control'}))
    name = forms.CharField(widget=forms.TextInput(attrs={'size': 35, 'class': 'productos form-control'}))
    unidad = forms.CharField(widget=forms.TextInput(attrs={'size': 5, 'readonly': "readonly", 'class': 'form-control'}))
    quantity = forms.DecimalField(max_digits=25, decimal_places=8,
                                  widget=forms.TextInput(attrs={'size': 6, 'class': 'cantidad decimal form-control'}))
    price = forms.DecimalField(max_digits=25, decimal_places=8, widget=forms.TextInput(
        attrs={'size': 7, 'readonly': "readonly", 'class': 'precio decimal form-control'}))
    amount = forms.DecimalField(max_digits=25, decimal_places=8, widget=forms.TextInput(
        attrs={'size': 10, 'readonly': "readonly", 'class': 'form-control'}))

    def clean_cantidad(self):
        if self.cleaned_data.get('quantity') == 0:
            raise ValidationError("La cantidad no puede ser 0")
        elif self.cleaned_data.get('quantity') < 0:
            raise ValidationError("La cantidad no puede ser negativa")
        return self.cleaned_data['quantity']


class BaseDetalleSalidaFormSet(formsets.BaseFormSet):

    def __init__(self, *args, **kwargs):
        super(BaseDetalleSalidaFormSet, self).__init__(*args, **kwargs)
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


class BaseDetallePedidoFormSet(formsets.BaseFormSet):

    def clean(self):
        for form in self.forms:
            if form.cleaned_data:
                pass
            else:
                raise forms.ValidationError(
                    'Registro de datos incompletos.',
                    code='datos_incompletos'
                )


class FormularioConsultaInventario(forms.Form):
    warehouse = forms.ModelChoiceField(queryset=Almacen.objects.all(),
                                     widget=forms.Select(attrs={'class': 'form-control'}))
    desde = forms.DateTimeField(input_formats=['%d/%m/%Y'],
                                widget=forms.TextInput(attrs={'size': 100, 'class': 'form-control'}))


DetalleIngresoFormSet = formsets.formset_factory(FormularioDetalleIngreso, BaseDetalleIngresoFormSet, 0)
DetalleSalidaFormSet = formsets.formset_factory(FormularioDetalleSalida, BaseDetalleSalidaFormSet, 0)
DetallePedidoFormSet = formsets.formset_factory(FormularioDetallePedido, BaseDetallePedidoFormSet, 0)
