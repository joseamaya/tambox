# -*- coding: utf-8 -*-
from django import forms

from tambox.forms import BootstrapFormMixin
from products.models import UnitOfMeasure, ProductGroup, Product


class UnitOfMeasureForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = UnitOfMeasure
        fields = ['code', 'sunat_code', 'description']


class ProductGroupForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = ProductGroup
        fields = ['description', 'account', 'contains_products']


class ProductForm(BootstrapFormMixin, forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super(ProductForm, self).__init__(*args, **kwargs)
        self.fields['price'].widget.attrs.update({'step': 'any', 'min': 0})

    class Meta:
        model = Product
        fields = ['description', 'product_group', 'unit_of_measure', 'brand', 'model', 'price', 'stock_type']


class ServiceForm(BootstrapFormMixin, forms.ModelForm):
    def save(self, *args, **kwargs):
        self.instance.is_service = True
        return super(ServiceForm, self).save(*args, **kwargs)

    class Meta:
        model = Product
        fields = ['description', 'product_group', 'price']
