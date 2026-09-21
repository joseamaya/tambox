# -*- coding: utf-8 -*-
from django import forms

from administracion.models import Producer, Worker
from almacen.models import Warehouse, MovementType, Movement, Order
from contabilidad.models import Upload
import datetime
from compras.models import PurchaseOrder
from django.utils import timezone
from django.forms import formsets
from django.core.exceptions import ValidationError, ObjectDoesNotExist
from almacen.settings import MESES, PARAMETROS, FORMATOS_SUNAT, \
    movement_type_choices, warehouse_choices, \
    CHOICES_CONSOLIDADO, SELECCION, FORMATOS


class MovementTypeForm(forms.ModelForm):
    class Meta:
        model = MovementType
        fields = ['description', 'sunat_code', 'increases', 'requires_reference', 'is_purchase', 'is_sale']

    def __init__(self, *args, **kwargs):
        self.aestado = True
        super(MovementTypeForm, self).__init__(*args, **kwargs)
        self.fields['description'].widget.attrs.update({'class': 'form-control'})
        self.fields['sunat_code'].widget.attrs.update({'class': 'form-control'})

    def save(self, *args, **kwargs):
        self.instance.aestado = self.aestado
        return super(MovementTypeForm, self).save(*args, **kwargs)


class WarehouseForm(forms.ModelForm):
    class Meta:
        model = Warehouse
        fields = ['code', 'description']

    def __init__(self, *args, **kwargs):
        super(WarehouseForm, self).__init__(*args, **kwargs)
        for field in iter(self.fields):
            self.fields[field].widget.attrs.update({
                'class': 'form-control'
            })


class MovementDetailForm(forms.Form):
    warehouse = forms.CharField(widget=forms.HiddenInput())
    code = forms.CharField(max_length=14, widget=forms.TextInput(attrs={'size': 17, 'class': 'entero form-control'}))
    name = forms.CharField(max_length=100, widget=forms.TextInput(attrs={'size': 35, 'class': 'form-control'}))
    unit = forms.CharField(max_length=6,
                             widget=forms.TextInput(attrs={'size': 6, 'readonly': "readonly", 'class': 'form-control'}))
    quantity = forms.DecimalField(max_digits=25, decimal_places=8,
                                  widget=forms.TextInput(attrs={'size': 6, 'class': 'form-control decimal'}))
    price = forms.DecimalField(max_digits=25, decimal_places=8, widget=forms.TextInput(
        attrs={'size': 7, 'readonly': "readonly", 'class': 'form-control decimal'}))
    amount = forms.DecimalField(max_digits=25, decimal_places=8, widget=forms.TextInput(
        attrs={'size': 10, 'readonly': "readonly", 'class': 'form-control decimal'}))


class MovementReportForm(forms.Form):
    search_type = forms.ChoiceField(widget=forms.RadioSelect(attrs={'class': 'radiobutton'}), label='Seleccione:',
                                      choices=PARAMETROS)
    start_date = forms.DateTimeField(input_formats=['%d/%m/%Y'],
                                widget=forms.TextInput(attrs={'size': 100, 'class': 'form-control'}))
    end_date = forms.DateTimeField(input_formats=['%d/%m/%Y'],
                                widget=forms.TextInput(attrs={'size': 100, 'class': 'form-control'}))
    month = forms.ChoiceField(choices=MESES, widget=forms.Select(attrs={'class': 'form-control'}), required=False)
    year = forms.CharField(max_length=4, widget=forms.TextInput(attrs={'size': 4, 'class': 'form-control'}), label='Año',
                            required=False)
    movement_types = forms.ChoiceField(choices=[],
                                         widget=forms.Select(attrs={'class': 'form-control'}))
    warehouses = forms.ChoiceField(choices=[], widget=forms.Select(attrs={'class': 'form-control'}))

    def __init__(self, *args, **kwargs):
        super(MovementReportForm, self).__init__(*args, **kwargs)
        self.fields['movement_types'].choices = movement_type_choices()
        self.fields['warehouses'].choices = warehouse_choices()

    def clean_hasta(self):
        self.cleaned_data['end_date'] = self.cleaned_data.get('end_date') + datetime.timedelta(days=1)
        return self.cleaned_data['end_date']


class MovementForm(forms.ModelForm):
    date = forms.CharField(max_length=100, widget=forms.TextInput(attrs={'size': 100, 'class': 'form-control'}))
    time = forms.CharField(max_length=100, widget=forms.TextInput(attrs={'size': 100, 'class': 'form-control'}))
    reference_document = forms.CharField(max_length=100, widget=forms.TextInput(
        attrs={'size': 100, 'readonly': "readonly", 'class': 'form-control'}))
    receiver_dni = forms.CharField(max_length=8, widget=forms.TextInput(
        attrs={'size': 100, 'readonly': "readonly", 'class': 'form-control'}))
    receiver = forms.CharField(max_length=150, widget=forms.TextInput(
        attrs={'size': 100, 'readonly': "readonly", 'class': 'form-control'}))
    details_count = forms.CharField(widget=forms.HiddenInput(), initial=0)
    total = forms.DecimalField(max_digits=25, decimal_places=8, widget=forms.TextInput(
        attrs={'size': 10, 'readonly': "readonly", 'class': 'form-control'}))

    def __init__(self, *args, **kwargs):
        self.movement_type = kwargs.pop("movement_type")
        super(MovementForm, self).__init__(*args, **kwargs)
        self.fields['movement_id'].required = False
        self.fields['document_type'].required = False
        self.fields['series'].required = False
        self.fields['number'].required = False
        self.fields['notes'].required = False
        self.fields['office'].required = False
        self.fields['receiver_dni'].required = False
        self.fields['receiver'].required = False
        self.fields['reference_document'].required = False
        if self.movement_type == 'I':
            self.fields['movement_type'].queryset = MovementType.objects.filter(increases=True)
        elif self.movement_type == 'S':
            self.fields['movement_type'].queryset = MovementType.objects.filter(increases=False)
        for field in iter(self.fields):
            self.fields[field].widget.attrs.update({
                'class': 'form-control'
            })

    def clean_dni_receptor(self):
        receiver_dni = self.cleaned_data.get('receiver_dni')
        if receiver_dni != "":
            if self.cleaned_data['movement_type'].is_sale:
                try:
                    Producer.objects.get(dni=self.cleaned_data['receiver_dni'])
                except Producer.DoesNotExist:
                    raise ValidationError("El DNI no corresponde a ningun productor")
            else:
                try:
                    Worker.objects.get(dni=self.cleaned_data['receiver_dni'])
                except Worker.DoesNotExist:
                    raise ValidationError("El DNI no correspone a ningun trabajador")
        return self.cleaned_data['receiver_dni']

    def get_datetime(self, r_date, r_hora):
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
                self.instance.reference = PurchaseOrder.objects.get(code=self.cleaned_data['reference_document'])
            except ObjectDoesNotExist:
                self.instance.reference = None
        if self.cleaned_data['movement_type'].is_sale:
            try:
                self.instance.producer = Producer.objects.get(dni=self.cleaned_data['receiver_dni'])
            except ObjectDoesNotExist:
                self.instance.producer = None
        else:
            try:
                self.instance.worker = Worker.objects.get(dni=self.cleaned_data['receiver_dni'])
            except ObjectDoesNotExist:
                self.instance.worker = None
        self.instance.operation_date = self.get_datetime(self.cleaned_data['date'], self.cleaned_data['time'])
        return super(MovementForm, self).save(*args, **kwargs)

    class Meta:
        model = Movement
        fields = ['movement_id', 'movement_type', 'document_type', 'series', 'number', 'warehouse', 'office',
                  'notes']


class KardexProductForm(forms.Form):
    warehouses = forms.ModelChoiceField(queryset=Warehouse.objects.all(),
                                       widget=forms.Select(attrs={'class': 'form-control'}))
    consolidated = forms.ChoiceField(choices=CHOICES_CONSOLIDADO, widget=forms.RadioSelect, required=False)
    start_date = forms.DateTimeField(input_formats=['%d/%m/%Y'],
                                widget=forms.TextInput(attrs={'size': 100, 'class': 'form-control'}))
    end_date = forms.DateTimeField(input_formats=['%d/%m/%Y'],
                                widget=forms.TextInput(attrs={'size': 100, 'class': 'form-control'}))
    product_code = forms.CharField(widget=forms.TextInput(attrs={'size': 100, 'class': 'form-control'}), required=False)
    product_description = forms.CharField(widget=forms.TextInput(attrs={'size': 100, 'class': 'form-control'}),
                                    required=False)
    sunat_format = forms.ChoiceField(choices=FORMATOS_SUNAT, widget=forms.RadioSelect, required=False)
    formats = forms.ChoiceField(choices=FORMATOS, widget=forms.RadioSelect)


class ProductMovementForm(forms.Form):
    warehouse = forms.ModelChoiceField(queryset=Warehouse.objects.all(),
                                     widget=forms.Select(attrs={'class': 'form-control'}))
    start_date = forms.DateTimeField(input_formats=['%d/%m/%Y'],
                                widget=forms.TextInput(attrs={'size': 100, 'class': 'form-control'}))
    end_date = forms.DateTimeField(input_formats=['%d/%m/%Y'],
                                widget=forms.TextInput(attrs={'size': 100, 'class': 'form-control'}))
    product = forms.CharField(widget=forms.TextInput(attrs={'size': 100, 'class': 'form-control'}))
    description = forms.CharField(widget=forms.TextInput(attrs={'size': 100, 'class': 'form-control'}))

    def clean_hasta(self):
        self.cleaned_data['end_date'] = self.cleaned_data.get('end_date') + datetime.timedelta(days=1)
        return self.cleaned_data['end_date']


class PriceReprocessForm(forms.Form):
    warehouse = forms.ModelChoiceField(queryset=Warehouse.objects.all(),
                                     widget=forms.Select(attrs={'class': 'form-control'}))
    start_date = forms.DateTimeField(input_formats=['%d/%m/%Y'],
                                widget=forms.TextInput(attrs={'size': 100, 'class': 'form-control'}))
    product = forms.CharField(widget=forms.TextInput(attrs={'size': 100, 'class': 'form-control'}), required=False)
    description = forms.CharField(widget=forms.TextInput(attrs={'size': 100, 'class': 'form-control'}), required=False)
    selection = forms.ChoiceField(choices=SELECCION, widget=forms.RadioSelect)


class StockQueryForm(forms.Form):
    warehouse = forms.ModelChoiceField(queryset=Warehouse.objects.all(),
                                     widget=forms.Select(attrs={'class': 'form-control'}))
    start_date = forms.DateTimeField(input_formats=['%d/%m/%Y'],
                                widget=forms.TextInput(attrs={'size': 100, 'class': 'form-control'}))
    product = forms.CharField(widget=forms.TextInput(attrs={'size': 100, 'class': 'form-control'}), required=False)
    description = forms.CharField(widget=forms.TextInput(attrs={'size': 100, 'class': 'form-control'}), required=False)


class InitialInventoryImportForm(forms.ModelForm):
    warehouses = forms.ModelChoiceField(queryset=Warehouse.objects.all(),
                                       widget=forms.Select(attrs={'class': 'form-control'}))
    date = forms.CharField(max_length=100, widget=forms.TextInput(attrs={'size': 100, 'class': 'form-control'}))
    time = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control', 'type': 'time'}))

    class Meta:
        model = Upload
        fields = ['file']

    def __init__(self, *args, **kwargs):
        super(InitialInventoryImportForm, self).__init__(*args, **kwargs)
        for field in iter(self.fields):
            self.fields[field].widget.attrs.update({
                'class': 'form-control'
            })


class OrderForm(forms.ModelForm):

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop("request")
        super(OrderForm, self).__init__(*args, **kwargs)
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
        return super(OrderForm, self).save(*args, **kwargs)

    class Meta:
        model = Order
        fields = ['code', 'date', 'notes']


class OrderApprovalForm(forms.ModelForm):
    order_code = forms.CharField(widget=forms.TextInput(attrs={'size': 100, 'class': 'entero form-control'}))
    date = forms.CharField(max_length=100, widget=forms.TextInput(attrs={'size': 100, 'class': 'form-control'}))
    time = forms.CharField(max_length=100, widget=forms.TextInput(attrs={'size': 100, 'class': 'form-control'}))
    total = forms.DecimalField(max_digits=15, decimal_places=5, widget=forms.TextInput(attrs={'size': 10,
                                                                                              'readonly': "readonly",
                                                                                              'class': 'form-control'}))

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop("request")
        super(OrderApprovalForm, self).__init__(*args, **kwargs)
        self.fields['notes'].required = False
        self.fields['date'].input_formats = ['%d/%m/%Y']
        for field in iter(self.fields):
            self.fields[field].widget.attrs.update({
                'class': 'form-control'
            })

    def get_datetime(self, r_date, r_hora):
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
        self.instance.order = Order.objects.get(code=self.cleaned_data['order_code'])
        self.instance.operation_date = self.get_datetime(self.cleaned_data['date'], self.cleaned_data['time'])
        self.instance.movement_type = MovementType.objects.get(code="S01")
        self.instance.office = self.instance.order.office
        return super(OrderApprovalForm, self).save(*args, **kwargs)

    class Meta:
        model = Movement
        fields = ['warehouse', 'notes']


class OrderHeaderForm(forms.Form):
    order_code = forms.CharField(max_length=100, widget=forms.TextInput(attrs={'size': 100, 'class': 'form-control'}))
    warehouses = forms.ModelChoiceField(queryset=Warehouse.objects.all(),
                                       widget=forms.Select(attrs={'class': 'form-control'}))
    date = forms.CharField(max_length=100, widget=forms.TextInput(attrs={'size': 100, 'class': 'form-control'}))
    notes = forms.CharField(widget=forms.Textarea(attrs={'cols': 141, 'rows': 5}))
    total = forms.CharField(max_length=100, widget=forms.TextInput(
        attrs={'size': 100, 'readonly': "readonly", 'class': 'form-control'}))


class OrderDetailForm(forms.Form):
    code = forms.CharField(max_length=14, widget=forms.TextInput(
        attrs={'size': 17, 'readonly': "readonly", 'class': 'entero form-control'}))
    name = forms.CharField(max_length=100, widget=forms.TextInput(attrs={'size': 35, 'class': 'form-control productos'}))
    unit = forms.CharField(max_length=20,
                             widget=forms.TextInput(attrs={'size': 6, 'readonly': "readonly", 'class': 'form-control'}))
    quantity = forms.DecimalField(max_digits=15, decimal_places=5,
                                  widget=forms.TextInput(attrs={'size': 6, 'class': 'cantidad decimal form-control'}))


class InboundDetailForm(forms.Form):
    purchase_order = forms.CharField(widget=forms.HiddenInput())
    code = forms.CharField(
        widget=forms.TextInput(attrs={'size': 8, 'readonly': "readonly", 'class': 'entero form-control'}))
    name = forms.CharField(widget=forms.TextInput(attrs={'size': 35, 'class': 'productos form-control'}))
    unit = forms.CharField(widget=forms.TextInput(attrs={'size': 5, 'readonly': "readonly", 'class': 'form-control'}))
    quantity = forms.DecimalField(max_digits=25, decimal_places=8,
                                  widget=forms.TextInput(attrs={'size': 6, 'class': 'cantidad decimal form-control'}))
    price = forms.DecimalField(max_digits=25, decimal_places=8,
                                widget=forms.TextInput(attrs={'size': 7, 'class': 'precio decimal form-control'}))
    amount = forms.DecimalField(max_digits=25, decimal_places=8, widget=forms.TextInput(
        attrs={'size': 10, 'readonly': "readonly", 'class': 'form-control'}))


class BaseInboundDetailFormSet(formsets.BaseFormSet):

    def clean(self):
        for form in self.forms:
            if form.cleaned_data:
                pass
            else:
                raise forms.ValidationError(
                    'Registro de datos incompletos.',
                    code='datos_incompletos'
                )


class OutboundDetailForm(forms.Form):
    order = forms.CharField(widget=forms.HiddenInput(), required=False)
    code = forms.CharField(
        widget=forms.TextInput(attrs={'size': 8, 'readonly': "readonly", 'class': 'entero form-control'}))
    name = forms.CharField(widget=forms.TextInput(attrs={'size': 35, 'class': 'productos form-control'}))
    unit = forms.CharField(widget=forms.TextInput(attrs={'size': 5, 'readonly': "readonly", 'class': 'form-control'}))
    quantity = forms.DecimalField(max_digits=25, decimal_places=8,
                                  widget=forms.TextInput(attrs={'size': 6, 'class': 'cantidad decimal form-control'}))
    price = forms.DecimalField(max_digits=25, decimal_places=8, widget=forms.TextInput(
        attrs={'size': 7, 'readonly': "readonly", 'class': 'precio decimal form-control'}))
    amount = forms.DecimalField(max_digits=25, decimal_places=8, widget=forms.TextInput(
        attrs={'size': 10, 'readonly': "readonly", 'class': 'form-control'}))

    def clean_quantity(self):
        if self.cleaned_data.get('quantity') == 0:
            raise ValidationError("La cantidad no puede ser 0")
        elif self.cleaned_data.get('quantity') < 0:
            raise ValidationError("La cantidad no puede ser negativa")
        return self.cleaned_data['quantity']


class BaseOutboundDetailFormSet(formsets.BaseFormSet):

    def __init__(self, *args, **kwargs):
        super(BaseOutboundDetailFormSet, self).__init__(*args, **kwargs)
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


class BaseOrderDetailFormSet(formsets.BaseFormSet):

    def clean(self):
        for form in self.forms:
            if form.cleaned_data:
                pass
            else:
                raise forms.ValidationError(
                    'Registro de datos incompletos.',
                    code='datos_incompletos'
                )


class InventoryQueryForm(forms.Form):
    warehouse = forms.ModelChoiceField(queryset=Warehouse.objects.all(),
                                     widget=forms.Select(attrs={'class': 'form-control'}))
    start_date = forms.DateTimeField(input_formats=['%d/%m/%Y'],
                                widget=forms.TextInput(attrs={'size': 100, 'class': 'form-control'}))


InboundDetailFormSet = formsets.formset_factory(InboundDetailForm, BaseInboundDetailFormSet, 0)
OutboundDetailFormSet = formsets.formset_factory(OutboundDetailForm, BaseOutboundDetailFormSet, 0)
OrderDetailFormSet = formsets.formset_factory(OrderDetailForm, BaseOrderDetailFormSet, 0)
