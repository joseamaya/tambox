# -*- coding: utf-8 -*-
from django import forms
from productos.models import UnidadMedida, GrupoProductos, Producto


class UnidadMedidaForm(forms.ModelForm):
    class Meta:
        model = UnidadMedida
        fields = ['code', 'sunat_code', 'description']

    def __init__(self, *args, **kwargs):
        super(UnidadMedidaForm, self).__init__(*args, **kwargs)
        for field in iter(self.fields):
            self.fields[field].widget.attrs.update({
                'class': 'form-control'
            })


class GrupoProductosForm(forms.ModelForm):

    def __init__(self, *args, **kwargs):
        super(GrupoProductosForm, self).__init__(*args, **kwargs)
        for field in iter(self.fields):
            self.fields[field].widget.attrs.update({
                'class': 'form-control'
            })

    class Meta:
        model = GrupoProductos
        fields = ['description', 'ctacontable', 'contains_products']


class ProductoForm(forms.ModelForm):

    def __init__(self, *args, **kwargs):
        super(ProductoForm, self).__init__(*args, **kwargs)
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
        model = Producto
        fields = ['description', 'grupo_productos', 'unidad_medida', 'brand', 'model', 'price', 'tipo_existencia']


class ServicioForm(forms.ModelForm):

    def __init__(self, *args, **kwargs):
        super(ServicioForm, self).__init__(*args, **kwargs)
        for field in iter(self.fields):
            self.fields[field].widget.attrs.update({
                'class': 'form-control'
            })

    def save(self, *args, **kwargs):
        self.instance.is_service = True
        return super(ServicioForm, self).save(*args, **kwargs)

    class Meta:
        model = Producto
        fields = ['description', 'grupo_productos', 'price']
