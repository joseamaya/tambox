# -*- coding: utf-8 -*-
from django import forms

from tambox.forms import BootstrapFormMixin
from tambox.widgets import NativeDateFieldsMixin
from purchases.models import Supplier, Quotation, PurchaseOrder, ServiceOrder, ServiceConformity
from django.forms import formsets
from requirements.models import Requirement
from warehouse.settings import MONTHS
from purchases.settings import SEARCH_PARAMETERS
from django.core.exceptions import ValidationError


class SupplierForm(BootstrapFormMixin, NativeDateFieldsMixin, forms.ModelForm):
    class Meta:
        model = Supplier
        fields = ['tax_id', 'business_name', 'address', 'phone', 'email', 'sunat_status', 'sunat_condition', 'ciiu',
                  'registration_date', 'is_service_provider']

    def __init__(self, *args, **kwargs):
        super(SupplierForm, self).__init__(*args, **kwargs)
        self.fields['is_service_provider'].label = 'Es locador de servicios'
        self.fields['ciiu'].required = False
        self.fields['phone'].required = False
        self.fields['email'].required = False
        self.fields['sunat_status'].required = False
        self.fields['sunat_condition'].required = False
        self.fields['tax_id'].widget.attrs.update({'class': 'quantity'})

    def clean_tax_id(self):
        tax_id = self.cleaned_data.get('tax_id')
        if len(tax_id) != 11:
            raise ValidationError('El RUC debe tener 11 dígitos.')
        return self.cleaned_data['tax_id']


class PurchaseOrderDetailForm(BootstrapFormMixin, forms.Form):
    code = forms.CharField(max_length=14, widget=forms.TextInput(attrs={'size': 17, 'class': 'entero'}))
    name = forms.CharField(max_length=100, widget=forms.TextInput(attrs={'size': 35}))
    unit = forms.CharField(max_length=6,
                             widget=forms.TextInput(attrs={'size': 6, 'readonly': "readonly"}))
    quantity = forms.DecimalField(max_digits=25, decimal_places=8,
                                  widget=forms.TextInput(attrs={'size': 6, 'class': 'decimal'}))
    price = forms.DecimalField(max_digits=25, decimal_places=8,
                                widget=forms.TextInput(attrs={'size': 7, 'class': 'decimal'}))
    amount = forms.DecimalField(max_digits=25, decimal_places=8, widget=forms.TextInput(
        attrs={'size': 10, 'readonly': "readonly"}))


class ServiceOrderDetailForm(BootstrapFormMixin, forms.Form):
    code = forms.CharField(widget=forms.HiddenInput())
    quantity = forms.DecimalField(max_digits=15, decimal_places=5,
                                  widget=forms.TextInput(attrs={'size': 6, 'class': 'decimal'}))
    service = forms.CharField(max_length=100, widget=forms.TextInput(attrs={'size': 35}))
    description = forms.CharField(widget=forms.Textarea(attrs={'cols': 112, 'rows': 2}))
    price = forms.DecimalField(max_digits=15, decimal_places=5,
                                widget=forms.TextInput(attrs={'size': 7, 'class': 'decimal'}))
    amount = forms.DecimalField(max_digits=15, decimal_places=5, widget=forms.TextInput(
        attrs={'size': 10, 'readonly': "readonly"}))


class OrderDateReportForm(BootstrapFormMixin, forms.Form):
    search_type = forms.ChoiceField(widget=forms.RadioSelect, label='Seleccione:',
                                      choices=SEARCH_PARAMETERS)
    start_date = forms.CharField(max_length=10, widget=forms.TextInput(
        attrs={'size': 10, 'type': 'date'}),
                                   label='Fecha de Inicio:', required=False)
    end_date = forms.CharField(max_length=10, widget=forms.TextInput(
        attrs={'size': 10, 'type': 'date'}),
                                label='Fecha de Fin:', required=False)
    month = forms.ChoiceField(choices=MONTHS, widget=forms.Select(), required=False)
    year = forms.CharField(max_length=4, widget=forms.TextInput(attrs={'size': 4}), label='Año',
                            required=False)


class QuotationForm(BootstrapFormMixin, NativeDateFieldsMixin, forms.ModelForm):
    tax_id = forms.CharField(max_length=11, widget=forms.TextInput(attrs={'size': 100, 'class': 'entero'}))
    business_name = forms.CharField(max_length=100, widget=forms.TextInput(attrs={'size': 100}))
    address = forms.CharField(max_length=100, widget=forms.TextInput(
        attrs={'size': 100, 'readonly': "readonly"}))
    reference = forms.CharField(max_length=100, widget=forms.TextInput(
        attrs={'size': 100, 'readonly': "readonly"}))
    order = forms.CharField(max_length=12, widget=forms.TextInput(
        attrs={'size': 100, 'readonly': "readonly"}), required=False)

    def __init__(self, *args, **kwargs):
        super(QuotationForm, self).__init__(*args, **kwargs)
        self.fields['code'].required = False

    def clean_order(self):
        order_code = self.cleaned_data.get('order')
        if len(order_code) != 12 and len(order_code) != 0:
            raise ValidationError('El código debe tener 12 dígitos.')
        elif len(order_code) == 12:
            orders = ServiceOrder.objects.filter(code=order_code)
            if len(orders) > 0:
                raise ValidationError('La orden ya existe.')
        return self.cleaned_data['order']

    def clean(self):
        cleaned_data = super(QuotationForm, self).clean()
        tax_id = cleaned_data.get('tax_id')
        reference = cleaned_data.get('reference')
        quotation = Quotation.objects.filter(supplier__tax_id=tax_id,
                                               requirement=reference)
        if self.instance.pk is not None:
            quotation = quotation.exclude(pk=self.instance.pk)
        if len(quotation) > 0:
            raise ValidationError('Ya se ingreso una cotización con este RUC para este requerimiento')
        else:
            return cleaned_data

    def save(self, *args, **kwargs):
        self.instance.supplier = Supplier.objects.get(tax_id=self.cleaned_data['tax_id'])
        self.instance.requirement = Requirement.objects.get(pk=self.cleaned_data['reference'])
        return super(QuotationForm, self).save(*args, **kwargs)

    class Meta:
        model = Quotation
        fields = ['code', 'date', 'notes']


class PurchaseOrderForm(BootstrapFormMixin, NativeDateFieldsMixin, forms.ModelForm):
    tax_id = forms.CharField(max_length=11, widget=forms.TextInput(attrs={'size': 100, 'class': 'entero'}))
    business_name = forms.CharField(max_length=100, widget=forms.TextInput(attrs={'size': 100}))
    address = forms.CharField(max_length=100, widget=forms.TextInput(
        attrs={'size': 100, 'readonly': "readonly"}))
    reference = forms.CharField(max_length=100, widget=forms.TextInput(
        attrs={'size': 100, 'readonly': "readonly"}))
    current_tax = forms.CharField(widget=forms.HiddenInput())
    subtotal = forms.DecimalField(max_digits=15, decimal_places=5, widget=forms.TextInput(
        attrs={'size': 10, 'readonly': "readonly"}))
    tax = forms.DecimalField(max_digits=15, decimal_places=5, widget=forms.TextInput(
        attrs={'size': 10, 'readonly': "readonly"}))
    total = forms.DecimalField(max_digits=15, decimal_places=5, widget=forms.TextInput(
        attrs={'size': 10, 'readonly': "readonly"}))
    total_in_words = forms.CharField(max_length=200, widget=forms.TextInput(attrs={'size': 200}))

    def __init__(self, *args, **kwargs):
        super(PurchaseOrderForm, self).__init__(*args, **kwargs)
        self.fields['code'].required = False
        self.fields['reference'].required = False
        self.fields['notes'].required = False
        for field in ('igv', 'total', 'subtotal', 'total_in_words'):
            if field in self.fields:
                self.fields[field].widget.attrs.update({'readonly': "readonly"})

    def clean_code(self):
        code = self.cleaned_data.get('code')
        if len(code) != 12 and len(code) != 0:
            raise ValidationError('El código debe tener 12 dígitos.')
        return self.cleaned_data['code']

    def save(self, *args, **kwargs):
        try:
            self.instance.quotation = Quotation.objects.get(code=self.cleaned_data['reference'])
        except Quotation.DoesNotExist:
            self.instance.quotation = None
            self.instance.supplier = Supplier.objects.get(tax_id=self.cleaned_data['tax_id'])
        return super(PurchaseOrderForm, self).save(*args, **kwargs)

    class Meta:
        model = PurchaseOrder
        fields = ['code', 'payment_method', 'date', 'notes', 'with_tax', 'in_dollars']


class ServiceOrderForm(BootstrapFormMixin, NativeDateFieldsMixin, forms.ModelForm):
    tax_id = forms.CharField(max_length=11, widget=forms.TextInput(attrs={'size': 100, 'class': 'entero'}))
    business_name = forms.CharField(max_length=100, widget=forms.TextInput(attrs={'size': 100}))
    address = forms.CharField(max_length=100, widget=forms.TextInput(
        attrs={'size': 100, 'readonly': "readonly"}))
    reference = forms.CharField(max_length=100, widget=forms.TextInput(
        attrs={'size': 100, 'readonly': "readonly"}))
    subtotal = forms.DecimalField(max_digits=15, decimal_places=5, widget=forms.TextInput(
        attrs={'size': 10, 'readonly': "readonly"}))
    tax = forms.DecimalField(max_digits=15, decimal_places=5, widget=forms.TextInput(
        attrs={'size': 10, 'readonly': "readonly"}))
    total = forms.DecimalField(max_digits=15, decimal_places=5, widget=forms.TextInput(
        attrs={'size': 10, 'readonly': "readonly"}))
    total_in_words = forms.CharField(max_length=200, widget=forms.TextInput(attrs={'size': 200}))

    def __init__(self, *args, **kwargs):
        super(ServiceOrderForm, self).__init__(*args, **kwargs)
        self.fields['code'].required = False
        self.fields['process'].required = False
        self.fields['notes'].required = False
        self.fields['report_name'].required = False
        self.fields['report'].required = False
        self.fields['reference'].required = False
        for field in ('igv', 'total', 'subtotal', 'total_in_words'):
            if field in self.fields:
                self.fields[field].widget.attrs.update({'readonly': "readonly"})

    def clean_code(self):
        code = self.cleaned_data.get('code')
        if len(code) != 12 and len(code) != 0:
            raise ValidationError('El código debe tener 12 dígitos.')
        return self.cleaned_data['code']

    def save(self, *args, **kwargs):
        try:
            self.instance.quotation = Quotation.objects.get(pk=self.cleaned_data['reference'])
        except Quotation.DoesNotExist:
            self.instance.quotation = None
            self.instance.supplier = Supplier.objects.get(tax_id=self.cleaned_data['tax_id'])
        return super(ServiceOrderForm, self).save(*args, **kwargs)

    class Meta:
        model = ServiceOrder
        fields = ['code', 'payment_method', 'process', 'notes', 'date', 'report_name', 'report']


class ServiceConformityForm(BootstrapFormMixin, NativeDateFieldsMixin, forms.ModelForm):
    reference = forms.CharField(max_length=100, widget=forms.TextInput(
        attrs={'size': 100, 'readonly': "readonly"}))
    subtotal = forms.CharField(max_length=100, widget=forms.TextInput(
        attrs={'size': 100, 'readonly': "readonly"}))

    def __init__(self, *args, **kwargs):
        super(ServiceConformityForm, self).__init__(*args, **kwargs)
        self.fields['total'].widget.attrs['readonly'] = True
        self.fields['total_in_words'].widget.attrs['readonly'] = True
        self.fields['code'].required = False
        self.fields['supporting_document'].required = False
        self.fields['file'].required = False

    def save(self, *args, **kwargs):
        self.instance.service_order = ServiceOrder.objects.get(pk=self.cleaned_data['reference'])
        return super(ServiceConformityForm, self).save(*args, **kwargs)

    class Meta:
        model = ServiceConformity
        fields = ['code', 'supporting_document', 'file', 'date', 'total', 'total_in_words']


class QuotationDetailForm(BootstrapFormMixin, forms.Form):
    requirement = forms.CharField(widget=forms.HiddenInput())
    code = forms.CharField(max_length=14, widget=forms.TextInput(
        attrs={'size': 14, 'readonly': "readonly", 'class': 'entero'}))
    name = forms.CharField(max_length=100, widget=forms.TextInput(
        attrs={'size': 120, 'readonly': "readonly"}))
    unit = forms.CharField(max_length=6,
                             widget=forms.TextInput(attrs={'size': 6, 'readonly': "readonly"}))
    quantity = forms.DecimalField(max_digits=15, decimal_places=5, widget=forms.TextInput(
        attrs={'size': 6, 'readonly': "readonly", 'class': 'cantidad decimal'}))


class PurchaseOrderDetailLineForm(BootstrapFormMixin, forms.Form):
    quotation = forms.CharField(widget=forms.HiddenInput())
    code = forms.CharField(
        widget=forms.TextInput(attrs={'size': 12, 'readonly': "readonly", 'class': 'entero'}))
    name = forms.CharField(widget=forms.TextInput(attrs={'size': 35, 'class': 'productos'}))
    unit = forms.CharField(widget=forms.TextInput(attrs={'size': 6, 'readonly': "readonly"}))
    quantity = forms.DecimalField(max_digits=25, decimal_places=8,
                                  widget=forms.TextInput(attrs={'size': 6, 'class': 'cantidad decimal'}))
    price = forms.DecimalField(max_digits=25, decimal_places=8,
                                widget=forms.TextInput(attrs={'size': 7, 'class': 'precio decimal'}))
    tax = forms.DecimalField(max_digits=25, decimal_places=8, widget=forms.TextInput(
        attrs={'size': 7, 'readonly': "readonly", 'class': 'impuesto decimal'}))
    amount = forms.DecimalField(max_digits=25, decimal_places=8, widget=forms.TextInput(
        attrs={'size': 10, 'readonly': "readonly"}))


class ServiceOrderDetailLineForm(BootstrapFormMixin, forms.Form):
    quotation = forms.CharField(widget=forms.HiddenInput())
    code = forms.CharField(widget=forms.HiddenInput())
    name = forms.CharField(widget=forms.TextInput(attrs={'size': 35, 'class': 'productos'}))
    unit = forms.CharField(widget=forms.TextInput(attrs={'size': 6, 'readonly': "readonly"}))
    quantity = forms.DecimalField(max_digits=15, decimal_places=5,
                                  widget=forms.TextInput(attrs={'size': 6, 'class': 'cantidad decimal'}))
    price = forms.DecimalField(max_digits=15, decimal_places=5,
                                widget=forms.TextInput(attrs={'size': 7, 'class': 'precio decimal'}))
    amount = forms.DecimalField(max_digits=15, decimal_places=5, widget=forms.TextInput(
        attrs={'size': 10, 'readonly': "readonly"}))


class ServiceConformityDetailLineForm(BootstrapFormMixin, forms.Form):
    service_order = forms.CharField(widget=forms.HiddenInput())
    quantity = forms.DecimalField(max_digits=15, decimal_places=5, widget=forms.TextInput(
        attrs={'size': 6, 'readonly': "readonly", 'class': 'cantidad decimal'}))
    service = forms.CharField(
        widget=forms.TextInput(attrs={'size': 35, 'readonly': "readonly"}))
    use = forms.CharField(widget=forms.TextInput(attrs={'size': 6, 'readonly': "readonly"}),
                          required=False)
    price = forms.DecimalField(max_digits=15, decimal_places=5, widget=forms.TextInput(
        attrs={'size': 7, 'readonly': "readonly", 'class': 'precio decimal'}))
    amount = forms.DecimalField(max_digits=15, decimal_places=5, widget=forms.TextInput(
        attrs={'size': 10, 'readonly': "readonly"}))


class BaseQuotationDetailFormSet(formsets.BaseFormSet):

    def clean(self):
        for form in self.forms:
            if form.cleaned_data:
                pass
            else:
                raise forms.ValidationError(
                    'Registro de datos incompletos.',
                    code='datos_incompletos'
                )


class BasePurchaseOrderDetailFormSet(formsets.BaseFormSet):

    def clean(self):
        for form in self.forms:
            if form.cleaned_data:
                pass
            else:
                raise forms.ValidationError(
                    'Registro de datos incompletos.',
                    code='datos_incompletos'
                )


class BaseServiceOrderDetailFormSet(formsets.BaseFormSet):

    def clean(self):
        for form in self.forms:
            if form.cleaned_data:
                pass
            else:
                raise forms.ValidationError(
                    'Registro de datos incompletos.',
                    code='datos_incompletos'
                )


class BaseServiceConformityDetailFormSet(formsets.BaseFormSet):

    def clean(self):
        for form in self.forms:
            if form.cleaned_data:
                pass
            else:
                raise forms.ValidationError(
                    'Registro de datos incompletos.',
                    code='datos_incompletos'
                )


QuotationDetailFormSet = formsets.formset_factory(QuotationDetailForm, BaseQuotationDetailFormSet, 0)
PurchaseOrderDetailFormSet = formsets.formset_factory(PurchaseOrderDetailLineForm, BasePurchaseOrderDetailFormSet, 0)
ServiceOrderDetailFormSet = formsets.formset_factory(ServiceOrderDetailLineForm,
                                                        BaseServiceOrderDetailFormSet, 0)
ServiceConformityDetailFormSet = formsets.formset_factory(ServiceConformityDetailLineForm,
                                                             BaseServiceConformityDetailFormSet, 0)
