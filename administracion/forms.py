# -*- coding: utf-8 -*-
from django import forms
from administracion.models import Office, Worker, Position, Profession, \
    ApprovalLevel, Producer


class NivelAprobacionForm(forms.ModelForm):
    class Meta:
        model = ApprovalLevel
        fields = ['description', 'superior_level']

    def __init__(self, *args, **kwargs):
        super(NivelAprobacionForm, self).__init__(*args, **kwargs)
        self.fields['superior_level'].required = False
        for field in iter(self.fields):
            self.fields[field].widget.attrs.update({
                'class': 'form-control'
            })


class ProfesionForm(forms.ModelForm):
    class Meta:
        model = Profession
        fields = ['abbreviation', 'description']

    def __init__(self, *args, **kwargs):
        super(ProfesionForm, self).__init__(*args, **kwargs)
        for field in iter(self.fields):
            self.fields[field].widget.attrs.update({
                'class': 'form-control'
            })


class OficinaForm(forms.ModelForm):
    class Meta:
        model = Office
        fields = ['code', 'name', 'dependency', 'is_management']

    def __init__(self, *args, **kwargs):
        super(OficinaForm, self).__init__(*args, **kwargs)
        for field in iter(self.fields):
            if field != 'is_management':
                self.fields[field].widget.attrs.update({
                    'class': 'form-control'
                })
        self.fields['dependency'].required = False


class TrabajadorForm(forms.ModelForm):
    class Meta:
        model = Worker
        fields = ['dni', 'last_name', 'first_name', 'profession', 'user', 'signature']

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
        self.fields['profession'].required = False


class ProductorForm(forms.ModelForm):
    class Meta:
        model = Producer
        fields = ['dni', 'last_name', 'first_name']

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
        model = Position
        fields = ['name', 'office', 'worker', 'start_date', 'end_date', 'is_leadership', 'is_assistant']

    def __init__(self, *args, **kwargs):
        super(PuestoForm, self).__init__(*args, **kwargs)
        for field in iter(self.fields):
            if field != 'is_leadership' and field != 'is_assistant':
                self.fields[field].widget.attrs.update({
                    'class': 'form-control'
                })
        self.fields['start_date'].input_formats = ['%d/%m/%Y']
        self.fields['end_date'].input_formats = ['%d/%m/%Y']
        self.fields['end_date'].required = False
        self.fields['is_leadership'].required = False
        self.fields['is_assistant'].required = False
        self.fields['worker'].queryset = Worker.objects.exclude(
            pk__in=Position.objects.filter(end_date__isnull=True).values('worker'))


class ModificacionPuestoForm(forms.ModelForm):
    class Meta:
        model = Position
        fields = ['name', 'office', 'worker', 'start_date', 'end_date', 'is_leadership', 'is_assistant']

    def __init__(self, *args, **kwargs):
        super(ModificacionPuestoForm, self).__init__(*args, **kwargs)
        for field in iter(self.fields):
            if field != 'is_leadership' and field != 'is_assistant':
                self.fields[field].widget.attrs.update({
                    'class': 'form-control'
                })
        self.fields['start_date'].input_formats = ['%d/%m/%Y']
        self.fields['end_date'].input_formats = ['%d/%m/%Y']
        self.fields['end_date'].required = False
        self.fields['is_leadership'].required = False
        self.fields['is_assistant'].required = False
