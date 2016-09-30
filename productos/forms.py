# -*- coding: utf-8 -*-
from django import forms
from productos.models import UnidadMedida, GrupoProductos, Producto

class UnidadMedidaForm(forms.ModelForm):

    class Meta:
        model = UnidadMedida
        fields =['codigo','descripcion']

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
        fields = ['descripcion','ctacontable','son_productos']        

class ProductoForm(forms.ModelForm):

    def __init__(self, *args, **kwargs):
        super(ProductoForm, self).__init__(*args, **kwargs)
        for field in iter(self.fields):
            if field=='stock_minimo' or field=='precio': 
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
        fields =['descripcion', 'desc_abreviada', 'grupo_productos','unidad_medida','marca','modelo','precio']
        
class ServicioForm(forms.ModelForm):

    def __init__(self, *args, **kwargs):
        super(ServicioForm, self).__init__(*args, **kwargs)
        for field in iter(self.fields):
            self.fields[field].widget.attrs.update({
                'class': 'form-control'
        })
            
    def save(self, *args, **kwargs):
        self.instance.es_servicio = True
        return super(ServicioForm, self).save(*args, **kwargs)  
            
    class Meta:
        model = Producto
        fields =['descripcion','grupo_productos']        
