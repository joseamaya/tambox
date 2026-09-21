# -*- coding: utf-8 -*-
from django import forms
from products.models import UnitOfMeasure, ProductGroup, Product


class UnitOfMeasureForm(forms.ModelForm):
    class Meta:
        model = UnitOfMeasure
        fields = ['code', 'sunat_code', 'description']

    def __init__(self, *args, **kwargs):
        super(UnitOfMeasureForm, self).__init__(*args, **kwargs)
        for field in iter(self.fields):
            self.fields[field].widget.attrs.update({
                'class': 'form-control'
            })


class ProductGroupForm(forms.ModelForm):

    def __init__(self, *args, **kwargs):
        super(ProductGroupForm, self).__init__(*args, **kwargs)
        for field in iter(self.fields):
            self.fields[field].widget.attrs.update({
                'class': 'form-control'
            })

    class Meta:
        model = ProductGroup
        fields = ['description', 'account', 'contains_products']


class ProductForm(forms.ModelForm):

    def __init__(self, *args, **kwargs):
        super(ProductForm, self).__init__(*args, **kwargs)
        for field in iter(self.fields):
            if field == 'minimum_stock' or field == 'price':
                self.fields[field].widget.attrs.update({
                    'class': 'form-control decimal',
                    'step': 'any',
                    'min': 0,
                })
            else:
                self.fields[field].widget.attrs.update({
                    'class': 'form-control'
                })

    class Meta:
        model = Product
        fields = ['description', 'product_group', 'unit_of_measure', 'brand', 'model', 'price', 'stock_type']


class ServiceForm(forms.ModelForm):

    def __init__(self, *args, **kwargs):
        super(ServiceForm, self).__init__(*args, **kwargs)
        for field in iter(self.fields):
            self.fields[field].widget.attrs.update({
                'class': 'form-control'
            })

    def save(self, *args, **kwargs):
        self.instance.is_service = True
        return super(ServiceForm, self).save(*args, **kwargs)

    class Meta:
        model = Product
        fields = ['description', 'product_group', 'price']
