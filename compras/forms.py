# -*- coding: utf-8 -*-
from django import forms
from compras.models import Supplier, Quotation, PurchaseOrder, ServiceOrder, ServiceConformity
from django.forms import formsets
from requerimientos.models import Requirement
from almacen.settings import MESES
from compras.settings import PARAMETROS_BUSQUEDA
from django.core.exceptions import ValidationError


class SupplierForm(forms.ModelForm):
    class Meta:
        model = Supplier
        fields = ['tax_id', 'business_name', 'address', 'phone', 'email', 'sunat_status', 'sunat_condition', 'ciiu',
                  'registration_date']

    def __init__(self, *args, **kwargs):
        super(SupplierForm, self).__init__(*args, **kwargs)
        self.fields['ciiu'].required = False
        self.fields['phone'].required = False
        self.fields['email'].required = False
        self.fields['sunat_status'].required = False
        self.fields['sunat_condition'].required = False
        self.fields['registration_date'].input_formats = ['%d/%m/%Y']
        for field in iter(self.fields):
            if field == 'tax_id':
                self.fields[field].widget.attrs.update({
                    'class': 'form-control quantity'
                })

    def clean_tax_id(self):
        tax_id = self.cleaned_data.get('tax_id')
        if len(tax_id) != 11:
            raise ValidationError('El RUC debe tener 11 dígitos.')
        return self.cleaned_data['tax_id']


class PurchaseOrderDetailForm(forms.Form):
    code = forms.CharField(max_length=14, widget=forms.TextInput(attrs={'size': 17, 'class': 'entero form-control'}))
    name = forms.CharField(max_length=100, widget=forms.TextInput(attrs={'size': 35, 'class': 'form-control'}))
    unit = forms.CharField(max_length=6,
                             widget=forms.TextInput(attrs={'size': 6, 'readonly': "readonly", 'class': 'form-control'}))
    quantity = forms.DecimalField(max_digits=25, decimal_places=8,
                                  widget=forms.TextInput(attrs={'size': 6, 'class': 'decimal form-control'}))
    price = forms.DecimalField(max_digits=25, decimal_places=8,
                                widget=forms.TextInput(attrs={'size': 7, 'class': 'decimal form-control'}))
    amount = forms.DecimalField(max_digits=25, decimal_places=8, widget=forms.TextInput(
        attrs={'size': 10, 'readonly': "readonly", 'class': 'form-control'}))


class ServiceOrderDetailForm(forms.Form):
    code = forms.CharField(widget=forms.HiddenInput())
    quantity = forms.DecimalField(max_digits=15, decimal_places=5,
                                  widget=forms.TextInput(attrs={'size': 6, 'class': 'decimal form-control'}))
    service = forms.CharField(max_length=100, widget=forms.TextInput(attrs={'size': 35, 'class': 'form-control'}))
    description = forms.CharField(widget=forms.Textarea(attrs={'cols': 112, 'rows': 2}))
    price = forms.DecimalField(max_digits=15, decimal_places=5,
                                widget=forms.TextInput(attrs={'size': 7, 'class': 'decimal form-control'}))
    amount = forms.DecimalField(max_digits=15, decimal_places=5, widget=forms.TextInput(
        attrs={'size': 10, 'readonly': "readonly", 'class': 'form-control'}))


class OrderDateReportForm(forms.Form):
    search_type = forms.ChoiceField(widget=forms.RadioSelect(attrs={'class': 'radiobutton'}), label='Seleccione:',
                                      choices=PARAMETROS_BUSQUEDA)
    start_date = forms.CharField(max_length=10, widget=forms.TextInput(attrs={'size': 10, 'class': 'form-control'}),
                                   label='Fecha de Inicio:', required=False)
    end_date = forms.CharField(max_length=10, widget=forms.TextInput(attrs={'size': 10, 'class': 'form-control'}),
                                label='Fecha de Fin:', required=False)
    month = forms.ChoiceField(choices=MESES, widget=forms.Select(attrs={'class': 'form-control'}), required=False)
    year = forms.CharField(max_length=4, widget=forms.TextInput(attrs={'size': 4, 'class': 'form-control'}), label='Año',
                            required=False)


class QuotationForm(forms.ModelForm):
    tax_id = forms.CharField(max_length=11, widget=forms.TextInput(attrs={'size': 100, 'class': 'entero form-control'}))
    business_name = forms.CharField(max_length=100, widget=forms.TextInput(attrs={'size': 100, 'class': 'form-control'}))
    address = forms.CharField(max_length=100, widget=forms.TextInput(
        attrs={'size': 100, 'readonly': "readonly", 'class': 'form-control'}))
    reference = forms.CharField(max_length=100, widget=forms.TextInput(
        attrs={'size': 100, 'readonly': "readonly", 'class': 'form-control'}))
    order = forms.CharField(max_length=12, widget=forms.TextInput(
        attrs={'size': 100, 'readonly': "readonly", 'class': 'form-control'}), required=False)

    def __init__(self, *args, **kwargs):
        super(QuotationForm, self).__init__(*args, **kwargs)
        self.fields['code'].required = False
        self.fields['date'].input_formats = ['%d/%m/%Y']
        for field in iter(self.fields):
            self.fields[field].widget.attrs.update({
                'class': 'form-control'
            })

    def clean_order(self):
        code_orden = self.cleaned_data.get('order')
        if len(code_orden) != 12 and len(code_orden) != 0:
            raise ValidationError('El código debe tener 12 dígitos.')
        elif len(code_orden) == 12:
            ordenes = ServiceOrder.objects.filter(code=code_orden)
            if len(ordenes) > 0:
                raise ValidationError('La orden ya existe.')
        return self.cleaned_data['order']

    def clean(self):
        cleaned_data = super(QuotationForm, self).clean()
        tax_id = cleaned_data.get('tax_id')
        reference = cleaned_data.get('reference')
        quotation = Quotation.objects.filter(supplier__tax_id=tax_id,
                                               requirement=reference)
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


class PurchaseOrderForm(forms.ModelForm):
    tax_id = forms.CharField(max_length=11, widget=forms.TextInput(attrs={'size': 100, 'class': 'entero form-control'}))
    business_name = forms.CharField(max_length=100, widget=forms.TextInput(attrs={'size': 100, 'class': 'form-control'}))
    address = forms.CharField(max_length=100, widget=forms.TextInput(
        attrs={'size': 100, 'readonly': "readonly", 'class': 'form-control'}))
    reference = forms.CharField(max_length=100, widget=forms.TextInput(
        attrs={'size': 100, 'readonly': "readonly", 'class': 'form-control'}))
    current_tax = forms.CharField(widget=forms.HiddenInput())
    subtotal = forms.DecimalField(max_digits=15, decimal_places=5, widget=forms.TextInput(
        attrs={'size': 10, 'readonly': "readonly", 'class': 'form-control'}))
    tax = forms.DecimalField(max_digits=15, decimal_places=5, widget=forms.TextInput(
        attrs={'size': 10, 'readonly': "readonly", 'class': 'form-control'}))
    total = forms.DecimalField(max_digits=15, decimal_places=5, widget=forms.TextInput(
        attrs={'size': 10, 'readonly': "readonly", 'class': 'form-control'}))
    total_in_words = forms.CharField(max_length=200, widget=forms.TextInput(attrs={'size': 200, 'class': 'form-control'}))

    def __init__(self, *args, **kwargs):
        super(PurchaseOrderForm, self).__init__(*args, **kwargs)
        self.fields['code'].required = False
        self.fields['reference'].required = False
        self.fields['date'].input_formats = ['%d/%m/%Y']
        self.fields['notes'].required = False
        for field in iter(self.fields):
            if field != 'with_tax' and field != 'in_dollars':
                self.fields[field].widget.attrs.update({
                    'class': 'form-control'
                })
            if field == 'igv' or field == 'total' or field == 'subtotal' or field == 'total_in_words':
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
            self.instance.quotation = Quotation.objects.get(code=self.cleaned_data['reference'])
        except Quotation.DoesNotExist:
            self.instance.quotation = None
            self.instance.supplier = Supplier.objects.get(tax_id=self.cleaned_data['tax_id'])
        return super(PurchaseOrderForm, self).save(*args, **kwargs)

    class Meta:
        model = PurchaseOrder
        fields = ['code', 'payment_method', 'date', 'notes', 'with_tax', 'in_dollars']


class ServiceOrderForm(forms.ModelForm):
    tax_id = forms.CharField(max_length=11, widget=forms.TextInput(attrs={'size': 100, 'class': 'entero form-control'}))
    business_name = forms.CharField(max_length=100, widget=forms.TextInput(attrs={'size': 100, 'class': 'form-control'}))
    address = forms.CharField(max_length=100, widget=forms.TextInput(
        attrs={'size': 100, 'readonly': "readonly", 'class': 'form-control'}))
    reference = forms.CharField(max_length=100, widget=forms.TextInput(
        attrs={'size': 100, 'readonly': "readonly", 'class': 'form-control'}))
    subtotal = forms.DecimalField(max_digits=15, decimal_places=5, widget=forms.TextInput(
        attrs={'size': 10, 'readonly': "readonly", 'class': 'form-control'}))
    tax = forms.DecimalField(max_digits=15, decimal_places=5, widget=forms.TextInput(
        attrs={'size': 10, 'readonly': "readonly", 'class': 'form-control'}))
    total = forms.DecimalField(max_digits=15, decimal_places=5, widget=forms.TextInput(
        attrs={'size': 10, 'readonly': "readonly", 'class': 'form-control'}))
    total_in_words = forms.CharField(max_length=200, widget=forms.TextInput(attrs={'size': 200, 'class': 'form-control'}))

    def __init__(self, *args, **kwargs):
        super(ServiceOrderForm, self).__init__(*args, **kwargs)
        self.fields['code'].required = False
        self.fields['process'].required = False
        self.fields['date'].input_formats = ['%d/%m/%Y']
        self.fields['notes'].required = False
        self.fields['report_name'].required = False
        self.fields['report'].required = False
        self.fields['reference'].required = False
        for field in iter(self.fields):
            self.fields[field].widget.attrs.update({
                'class': 'form-control'
            })
            if field == 'igv' or field == 'total' or field == 'subtotal' or field == 'total_in_words':
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
            self.instance.quotation = Quotation.objects.get(pk=self.cleaned_data['reference'])
        except Quotation.DoesNotExist:
            self.instance.quotation = None
            self.instance.supplier = Supplier.objects.get(tax_id=self.cleaned_data['tax_id'])
        return super(ServiceOrderForm, self).save(*args, **kwargs)

    class Meta:
        model = ServiceOrder
        fields = ['code', 'payment_method', 'process', 'notes', 'date', 'report_name', 'report']


class ServiceConformityForm(forms.ModelForm):
    reference = forms.CharField(max_length=100, widget=forms.TextInput(
        attrs={'size': 100, 'readonly': "readonly", 'class': 'form-control'}))
    subtotal = forms.CharField(max_length=100, widget=forms.TextInput(
        attrs={'size': 100, 'readonly': "readonly", 'class': 'form-control'}))

    def __init__(self, *args, **kwargs):
        super(ServiceConformityForm, self).__init__(*args, **kwargs)
        self.fields['total'].widget.attrs['readonly'] = True
        self.fields['total_in_words'].widget.attrs['readonly'] = True
        self.fields['code'].required = False
        self.fields['supporting_document'].required = False
        self.fields['file'].required = False
        self.fields['date'].input_formats = ['%d/%m/%Y']
        for field in iter(self.fields):
            self.fields[field].widget.attrs.update({
                'class': 'form-control'
            })

    def save(self, *args, **kwargs):
        self.instance.service_order = ServiceOrder.objects.get(pk=self.cleaned_data['reference'])
        return super(ServiceConformityForm, self).save(*args, **kwargs)

    class Meta:
        model = ServiceConformity
        fields = ['code', 'supporting_document', 'file', 'date', 'total', 'total_in_words']


class QuotationDetailForm(forms.Form):
    requirement = forms.CharField(widget=forms.HiddenInput())
    code = forms.CharField(max_length=14, widget=forms.TextInput(
        attrs={'size': 14, 'readonly': "readonly", 'class': 'entero form-control'}))
    name = forms.CharField(max_length=100, widget=forms.TextInput(
        attrs={'size': 120, 'readonly': "readonly", 'class': 'form-control'}))
    unit = forms.CharField(max_length=6,
                             widget=forms.TextInput(attrs={'size': 6, 'readonly': "readonly", 'class': 'form-control'}))
    quantity = forms.DecimalField(max_digits=15, decimal_places=5, widget=forms.TextInput(
        attrs={'size': 6, 'readonly': "readonly", 'class': 'cantidad decimal form-control'}))


class PurchaseOrderDetailLineForm(forms.Form):
    quotation = forms.CharField(widget=forms.HiddenInput())
    code = forms.CharField(
        widget=forms.TextInput(attrs={'size': 12, 'readonly': "readonly", 'class': 'entero form-control'}))
    name = forms.CharField(widget=forms.TextInput(attrs={'size': 35, 'class': 'productos form-control'}))
    unit = forms.CharField(widget=forms.TextInput(attrs={'size': 6, 'readonly': "readonly", 'class': 'form-control'}))
    quantity = forms.DecimalField(max_digits=25, decimal_places=8,
                                  widget=forms.TextInput(attrs={'size': 6, 'class': 'cantidad decimal form-control'}))
    price = forms.DecimalField(max_digits=25, decimal_places=8,
                                widget=forms.TextInput(attrs={'size': 7, 'class': 'precio decimal form-control'}))
    tax = forms.DecimalField(max_digits=25, decimal_places=8, widget=forms.TextInput(
        attrs={'size': 7, 'readonly': "readonly", 'class': 'impuesto decimal form-control'}))
    amount = forms.DecimalField(max_digits=25, decimal_places=8, widget=forms.TextInput(
        attrs={'size': 10, 'readonly': "readonly", 'class': 'form-control'}))


class ServiceOrderDetailLineForm(forms.Form):
    quotation = forms.CharField(widget=forms.HiddenInput())
    code = forms.CharField(widget=forms.HiddenInput())
    name = forms.CharField(widget=forms.TextInput(attrs={'size': 35, 'class': 'productos form-control'}))
    unit = forms.CharField(widget=forms.TextInput(attrs={'size': 6, 'readonly': "readonly", 'class': 'form-control'}))
    quantity = forms.DecimalField(max_digits=15, decimal_places=5,
                                  widget=forms.TextInput(attrs={'size': 6, 'class': 'cantidad decimal form-control'}))
    price = forms.DecimalField(max_digits=15, decimal_places=5,
                                widget=forms.TextInput(attrs={'size': 7, 'class': 'precio decimal form-control'}))
    amount = forms.DecimalField(max_digits=15, decimal_places=5, widget=forms.TextInput(
        attrs={'size': 10, 'readonly': "readonly", 'class': 'form-control'}))


class ServiceConformityDetailLineForm(forms.Form):
    service_order = forms.CharField(widget=forms.HiddenInput())
    quantity = forms.DecimalField(max_digits=15, decimal_places=5, widget=forms.TextInput(
        attrs={'size': 6, 'readonly': "readonly", 'class': 'cantidad decimal form-control'}))
    service = forms.CharField(
        widget=forms.TextInput(attrs={'size': 35, 'readonly': "readonly", 'class': 'form-control'}))
    use = forms.CharField(widget=forms.TextInput(attrs={'size': 6, 'readonly': "readonly", 'class': 'form-control'}),
                          required=False)
    price = forms.DecimalField(max_digits=15, decimal_places=5, widget=forms.TextInput(
        attrs={'size': 7, 'readonly': "readonly", 'class': 'precio decimal form-control'}))
    amount = forms.DecimalField(max_digits=15, decimal_places=5, widget=forms.TextInput(
        attrs={'size': 10, 'readonly': "readonly", 'class': 'form-control'}))


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
