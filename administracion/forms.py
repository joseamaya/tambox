# -*- coding: utf-8 -*-
from django import forms
from administracion.models import Oficina, Trabajador, Puesto, Profesion, \
    NivelAprobacion, Productor


class NivelAprobacionForm(forms.ModelForm):
    class Meta:
        model = NivelAprobacion
        fields = ['descripcion', 'nivel_superior']

    def __init__(self, *args, **kwargs):
        super(NivelAprobacionForm, self).__init__(*args, **kwargs)
        self.fields['nivel_superior'].required = False
        for field in iter(self.fields):
            self.fields[field].widget.attrs.update({
                'class': 'form-control'
            })


class ProfesionForm(forms.ModelForm):
    class Meta:
        model = Profesion
        fields = ['abreviatura', 'descripcion']

    def __init__(self, *args, **kwargs):
        super(ProfesionForm, self).__init__(*args, **kwargs)
        for field in iter(self.fields):
            self.fields[field].widget.attrs.update({
                'class': 'form-control'
            })


class OficinaForm(forms.ModelForm):
    class Meta:
        model = Oficina
        fields = ['codigo', 'nombre', 'dependencia', 'es_gerencia']

    def __init__(self, *args, **kwargs):
        super(OficinaForm, self).__init__(*args, **kwargs)
        for field in iter(self.fields):
            if field != 'es_gerencia':
                self.fields[field].widget.attrs.update({
                    'class': 'form-control'
                })
        self.fields['dependencia'].required = False


class TrabajadorForm(forms.ModelForm):
    class Meta:
        model = Trabajador
        fields = ['dni', 'apellido_paterno', 'apellido_materno', 'nombres', 'profesion', 'usuario', 'firma']

    def __init__(self, *args, **kwargs):
        super(TrabajadorForm, self).__init__(*args, **kwargs)
        for field in iter(self.fields):
            if field == 'dni':
                self.fields[field].widget.attrs.update({
                    'class': 'form-control entero'
                })
            else:
                self.fields[field].widget.attrs.update({
                    'class': 'form-control'
                })
        self.fields['profesion'].required = False

class ProductorForm(forms.ModelForm):
    class Meta:
        model = Productor
        fields = ['dni', 'apellido_paterno', 'apellido_materno', 'nombres']

    def __init__(self, *args, **kwargs):
        super(ProductorForm, self).__init__(*args, **kwargs)
        for field in iter(self.fields):
            if field == 'dni':
                self.fields[field].widget.attrs.update({
                    'class': 'form-control entero'
                })
            else:
                self.fields[field].widget.attrs.update({
                    'class': 'form-control'
                })


class PuestoForm(forms.ModelForm):
    class Meta:
        model = Puesto
        fields = ['nombre', 'oficina', 'trabajador', 'fecha_inicio', 'fecha_fin', 'es_jefatura', 'es_asistente']

    def __init__(self, *args, **kwargs):
        super(PuestoForm, self).__init__(*args, **kwargs)
        for field in iter(self.fields):
            if field != 'es_jefatura' and field != 'es_asistente':
                self.fields[field].widget.attrs.update({
                    'class': 'form-control'
                })
        self.fields['fecha_inicio'].input_formats = ['%d/%m/%Y']
        self.fields['fecha_fin'].input_formats = ['%d/%m/%Y']
        self.fields['fecha_fin'].required = False
        self.fields['es_jefatura'].required = False
        self.fields['es_asistente'].required = False
        self.fields['trabajador'].queryset = Trabajador.objects.exclude(
            pk__in=Puesto.objects.filter(fecha_fin__isnull=True).values('trabajador'))


class ModificacionPuestoForm(forms.ModelForm):
    class Meta:
        model = Puesto
        fields = ['nombre', 'oficina', 'trabajador', 'fecha_inicio', 'fecha_fin', 'es_jefatura', 'es_asistente']

    def __init__(self, *args, **kwargs):
        super(ModificacionPuestoForm, self).__init__(*args, **kwargs)
        for field in iter(self.fields):
            if field != 'es_jefatura' and field != 'es_asistente':
                self.fields[field].widget.attrs.update({
                    'class': 'form-control'
                })
        self.fields['fecha_inicio'].input_formats = ['%d/%m/%Y']
        self.fields['fecha_fin'].input_formats = ['%d/%m/%Y']
        self.fields['fecha_fin'].required = False
        self.fields['es_jefatura'].required = False
        self.fields['es_asistente'].required = False