# -*- coding: utf-8 -*-
from django import forms

from tambox.dates import parse_date, parse_time
from tambox.forms import BootstrapFormMixin
from tambox.widgets import DateInput

from administration.models import Producer, Worker
from warehouse.models import Warehouse, MovementType, Movement, Order
from accounting.models import Upload
import datetime
from purchases.models import PurchaseOrder
from django.utils import timezone
from django.forms import formsets
from django.core.exceptions import ValidationError, ObjectDoesNotExist
from warehouse.settings import MONTHS, SEARCH_PARAMETERS, SUNAT_FORMATS,\
    movement_type_choices, warehouse_choices,\
    CONSOLIDATED_CHOICES, SELECTION, FORMATS


class MovementTypeForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = MovementType
        fields = ['description', 'sunat_code', 'increases', 'requires_reference', 'is_purchase', 'is_sale']

    def __init__(self, *args, **kwargs):
        self.is_active = True
        super(MovementTypeForm, self).__init__(*args, **kwargs)

    def save(self, *args, **kwargs):
        self.instance.is_active = self.is_active
        return super(MovementTypeForm, self).save(*args, **kwargs)


class WarehouseForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = Warehouse
        fields = ['code', 'description']


class MovementDetailForm(BootstrapFormMixin, forms.Form):
    warehouse = forms.CharField(widget=forms.HiddenInput())
    code = forms.CharField(max_length=14, widget=forms.TextInput(attrs={'size': 17, 'class': 'entero'}))
    name = forms.CharField(max_length=100, widget=forms.TextInput(attrs={'size': 35}))
    unit = forms.CharField(max_length=6,
                             widget=forms.TextInput(attrs={'size': 6, 'readonly': "readonly"}))
    quantity = forms.DecimalField(max_digits=25, decimal_places=8,
                                  widget=forms.TextInput(attrs={'size': 6, 'class': 'decimal'}))
    price = forms.DecimalField(max_digits=25, decimal_places=8, widget=forms.TextInput(
        attrs={'size': 7, 'readonly': "readonly", 'class': 'decimal'}))
    amount = forms.DecimalField(max_digits=25, decimal_places=8, widget=forms.TextInput(
        attrs={'size': 10, 'readonly': "readonly", 'class': 'decimal'}))


class MovementReportForm(BootstrapFormMixin, forms.Form):
    search_type = forms.ChoiceField(widget=forms.RadioSelect, label='Seleccione:',
                                      choices=SEARCH_PARAMETERS)
    start_date = forms.DateTimeField(input_formats=['%Y-%m-%d', '%d/%m/%Y'],
                                widget=DateInput(attrs={'size': 100}))
    end_date = forms.DateTimeField(input_formats=['%Y-%m-%d', '%d/%m/%Y'],
                                widget=DateInput(attrs={'size': 100}))
    month = forms.ChoiceField(choices=MONTHS, widget=forms.Select(), required=False)
    year = forms.CharField(max_length=4, widget=forms.TextInput(attrs={'size': 4}), label='Año',
                            required=False)
    movement_types = forms.ChoiceField(choices=[],
                                         widget=forms.Select())
    warehouses = forms.ChoiceField(choices=[], widget=forms.Select())

    def __init__(self, *args, **kwargs):
        super(MovementReportForm, self).__init__(*args, **kwargs)
        self.fields['movement_types'].choices = movement_type_choices()
        self.fields['warehouses'].choices = warehouse_choices()

    def clean_end_date(self):
        self.cleaned_data['end_date'] = self.cleaned_data.get('end_date') + datetime.timedelta(days=1)
        return self.cleaned_data['end_date']


class MovementForm(BootstrapFormMixin, forms.ModelForm):
    date = forms.CharField(max_length=100, widget=forms.TextInput(
        attrs={'size': 100, 'type': 'date'}))
    time = forms.CharField(max_length=100, widget=forms.TextInput(
        attrs={'size': 100, 'type': 'time', 'step': 1}))
    reference_document = forms.CharField(max_length=100, widget=forms.TextInput(
        attrs={'size': 100, 'readonly': "readonly"}))
    receiver_dni = forms.CharField(max_length=8, widget=forms.TextInput(
        attrs={'size': 100, 'readonly': "readonly"}))
    receiver = forms.CharField(max_length=150, widget=forms.TextInput(
        attrs={'size': 100, 'readonly': "readonly"}))
    details_count = forms.CharField(widget=forms.HiddenInput(), initial=0)
    total = forms.DecimalField(max_digits=25, decimal_places=8, widget=forms.TextInput(
        attrs={'size': 10, 'readonly': "readonly"}))

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

    def clean_receiver_dni(self):
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
        return timezone.make_aware(
            datetime.datetime.combine(parse_date(r_date), parse_time(r_hora)))

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


class KardexProductForm(BootstrapFormMixin, forms.Form):
    warehouses = forms.ModelChoiceField(queryset=Warehouse.objects.all(),
                                       widget=forms.Select())
    consolidated = forms.ChoiceField(choices=CONSOLIDATED_CHOICES, widget=forms.RadioSelect, required=False)
    start_date = forms.DateTimeField(input_formats=['%Y-%m-%d', '%d/%m/%Y'],
                                widget=DateInput(attrs={'size': 100}))
    end_date = forms.DateTimeField(input_formats=['%Y-%m-%d', '%d/%m/%Y'],
                                widget=DateInput(attrs={'size': 100}))
    product_code = forms.CharField(widget=forms.TextInput(attrs={'size': 100}), required=False)
    product_description = forms.CharField(widget=forms.TextInput(attrs={'size': 100}),
                                    required=False)
    sunat_format = forms.ChoiceField(choices=SUNAT_FORMATS, widget=forms.RadioSelect, required=False)
    formats = forms.ChoiceField(choices=FORMATS, widget=forms.RadioSelect)


class ProductMovementForm(BootstrapFormMixin, forms.Form):
    warehouse = forms.ModelChoiceField(queryset=Warehouse.objects.all(),
                                     widget=forms.Select())
    start_date = forms.DateTimeField(input_formats=['%Y-%m-%d', '%d/%m/%Y'],
                                widget=DateInput(attrs={'size': 100}))
    end_date = forms.DateTimeField(input_formats=['%Y-%m-%d', '%d/%m/%Y'],
                                widget=DateInput(attrs={'size': 100}))
    product = forms.CharField(widget=forms.TextInput(attrs={'size': 100}))
    description = forms.CharField(widget=forms.TextInput(attrs={'size': 100}))

    def clean_end_date(self):
        self.cleaned_data['end_date'] = self.cleaned_data.get('end_date') + datetime.timedelta(days=1)
        return self.cleaned_data['end_date']


class PriceReprocessForm(BootstrapFormMixin, forms.Form):
    warehouse = forms.ModelChoiceField(queryset=Warehouse.objects.all(),
                                     widget=forms.Select())
    start_date = forms.DateTimeField(input_formats=['%Y-%m-%d', '%d/%m/%Y'],
                                widget=DateInput(attrs={'size': 100}))
    product = forms.CharField(widget=forms.TextInput(attrs={'size': 100}), required=False)
    description = forms.CharField(widget=forms.TextInput(attrs={'size': 100}), required=False)
    selection = forms.ChoiceField(choices=SELECTION, widget=forms.RadioSelect)


class StockQueryForm(BootstrapFormMixin, forms.Form):
    warehouse = forms.ModelChoiceField(queryset=Warehouse.objects.all(),
                                     widget=forms.Select())
    start_date = forms.DateTimeField(input_formats=['%Y-%m-%d', '%d/%m/%Y'],
                                widget=DateInput(attrs={'size': 100}))
    product = forms.CharField(widget=forms.TextInput(attrs={'size': 100}), required=False)
    description = forms.CharField(widget=forms.TextInput(attrs={'size': 100}), required=False)


class InitialInventoryImportForm(BootstrapFormMixin, forms.ModelForm):
    warehouses = forms.ModelChoiceField(queryset=Warehouse.objects.all(),
                                       widget=forms.Select())
    date = forms.CharField(max_length=100, widget=forms.TextInput(attrs={'size': 100, 'type': 'date'}))
    time = forms.CharField(widget=forms.TextInput(attrs={'type': 'time'}))

    class Meta:
        model = Upload
        fields = ['file']


class OrderForm(BootstrapFormMixin, forms.ModelForm):

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop("request")
        super(OrderForm, self).__init__(*args, **kwargs)
        self.fields['code'].required = False
        self.fields['notes'].required = False
        if 'total' in self.fields:
            self.fields['total'].widget.attrs.update({'readonly': "readonly"})

    def save(self, *args, **kwargs):
        self.instance.requester = self.request.user.worker
        positions = self.request.user.worker.positions.all().filter(is_active=True)
        self.instance.office = positions[0].office
        return super(OrderForm, self).save(*args, **kwargs)

    class Meta:
        model = Order
        fields = ['code', 'date', 'notes']


class OrderApprovalForm(BootstrapFormMixin, forms.ModelForm):
    order_code = forms.CharField(widget=forms.TextInput(attrs={'size': 100, 'class': 'entero'}))
    date = forms.CharField(max_length=100, widget=forms.TextInput(
        attrs={'size': 100, 'type': 'date'}))
    time = forms.CharField(max_length=100, widget=forms.TextInput(
        attrs={'size': 100, 'type': 'time', 'step': 1}))
    total = forms.DecimalField(max_digits=15, decimal_places=5, widget=forms.TextInput(attrs={'size': 10,
                                                                                              'readonly': "readonly"}))

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop("request")
        super(OrderApprovalForm, self).__init__(*args, **kwargs)
        self.fields['notes'].required = False

    def get_datetime(self, r_date, r_hora):
        return timezone.make_aware(
            datetime.datetime.combine(parse_date(r_date), parse_time(r_hora)))

    def save(self, *args, **kwargs):
        self.instance.order = Order.objects.get(code=self.cleaned_data['order_code'])
        self.instance.operation_date = self.get_datetime(self.cleaned_data['date'], self.cleaned_data['time'])
        self.instance.movement_type = MovementType.objects.get(code="S01")
        self.instance.office = self.instance.order.office
        return super(OrderApprovalForm, self).save(*args, **kwargs)

    class Meta:
        model = Movement
        fields = ['warehouse', 'notes']


class OrderHeaderForm(BootstrapFormMixin, forms.Form):
    order_code = forms.CharField(max_length=100, widget=forms.TextInput(attrs={'size': 100}))
    warehouses = forms.ModelChoiceField(queryset=Warehouse.objects.all(),
                                       widget=forms.Select())
    date = forms.CharField(max_length=100, widget=forms.TextInput(
        attrs={'size': 100, 'type': 'date'}))
    notes = forms.CharField(widget=forms.Textarea(attrs={'cols': 141, 'rows': 5}))
    total = forms.CharField(max_length=100, widget=forms.TextInput(
        attrs={'size': 100, 'readonly': "readonly"}))


class OrderDetailForm(BootstrapFormMixin, forms.Form):
    code = forms.CharField(max_length=14, widget=forms.TextInput(
        attrs={'size': 17, 'readonly': "readonly", 'class': 'entero'}))
    name = forms.CharField(max_length=100, widget=forms.TextInput(attrs={'size': 35, 'class': 'productos'}))
    unit = forms.CharField(max_length=20,
                             widget=forms.TextInput(attrs={'size': 6, 'readonly': "readonly"}))
    quantity = forms.DecimalField(max_digits=15, decimal_places=5,
                                  widget=forms.TextInput(attrs={'size': 6, 'class': 'cantidad decimal'}))


class InboundDetailForm(BootstrapFormMixin, forms.Form):
    purchase_order = forms.CharField(widget=forms.HiddenInput())
    code = forms.CharField(
        widget=forms.TextInput(attrs={'size': 8, 'readonly': "readonly", 'class': 'entero'}))
    name = forms.CharField(widget=forms.TextInput(attrs={'size': 35, 'class': 'productos'}))
    unit = forms.CharField(widget=forms.TextInput(attrs={'size': 5, 'readonly': "readonly"}))
    quantity = forms.DecimalField(max_digits=25, decimal_places=8,
                                  widget=forms.TextInput(attrs={'size': 6, 'class': 'cantidad decimal'}))
    price = forms.DecimalField(max_digits=25, decimal_places=8,
                                widget=forms.TextInput(attrs={'size': 7, 'class': 'precio decimal'}))
    amount = forms.DecimalField(max_digits=25, decimal_places=8, widget=forms.TextInput(
        attrs={'size': 10, 'readonly': "readonly"}))


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


class OutboundDetailForm(BootstrapFormMixin, forms.Form):
    order = forms.CharField(widget=forms.HiddenInput(), required=False)
    code = forms.CharField(
        widget=forms.TextInput(attrs={'size': 8, 'readonly': "readonly", 'class': 'entero'}))
    name = forms.CharField(widget=forms.TextInput(attrs={'size': 35, 'class': 'productos'}))
    unit = forms.CharField(widget=forms.TextInput(attrs={'size': 5, 'readonly': "readonly"}))
    quantity = forms.DecimalField(max_digits=25, decimal_places=8,
                                  widget=forms.TextInput(attrs={'size': 6, 'class': 'cantidad decimal'}))
    price = forms.DecimalField(max_digits=25, decimal_places=8, widget=forms.TextInput(
        attrs={'size': 7, 'readonly': "readonly", 'class': 'precio decimal'}))
    amount = forms.DecimalField(max_digits=25, decimal_places=8, widget=forms.TextInput(
        attrs={'size': 10, 'readonly': "readonly"}))

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


class InventoryQueryForm(BootstrapFormMixin, forms.Form):
    warehouse = forms.ModelChoiceField(queryset=Warehouse.objects.all(),
                                     widget=forms.Select())
    start_date = forms.DateTimeField(input_formats=['%Y-%m-%d', '%d/%m/%Y'],
                                widget=DateInput(attrs={'size': 100}))


InboundDetailFormSet = formsets.formset_factory(InboundDetailForm, BaseInboundDetailFormSet, 0)
OutboundDetailFormSet = formsets.formset_factory(OutboundDetailForm, BaseOutboundDetailFormSet, 0)
OrderDetailFormSet = formsets.formset_factory(OrderDetailForm, BaseOrderDetailFormSet, 0)
