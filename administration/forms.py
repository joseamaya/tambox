# -*- coding: utf-8 -*-
from django import forms
from administration.models import Office, Worker, Position, Profession, \
    ApprovalLevel, Producer


class ApprovalLevelForm(forms.ModelForm):
    class Meta:
        model = ApprovalLevel
        fields = ['description', 'superior_level']

    def __init__(self, *args, **kwargs):
        super(ApprovalLevelForm, self).__init__(*args, **kwargs)
        self.fields['superior_level'].required = False
        for field in iter(self.fields):
            self.fields[field].widget.attrs.update({
                'class': 'form-control'
            })


class ProfessionForm(forms.ModelForm):
    class Meta:
        model = Profession
        fields = ['abbreviation', 'description']

    def __init__(self, *args, **kwargs):
        super(ProfessionForm, self).__init__(*args, **kwargs)
        for field in iter(self.fields):
            self.fields[field].widget.attrs.update({
                'class': 'form-control'
            })


class OfficeForm(forms.ModelForm):
    class Meta:
        model = Office
        fields = ['code', 'name', 'dependency', 'is_management']

    def __init__(self, *args, **kwargs):
        super(OfficeForm, self).__init__(*args, **kwargs)
        for field in iter(self.fields):
            if field != 'is_management':
                self.fields[field].widget.attrs.update({
                    'class': 'form-control'
                })
        self.fields['dependency'].required = False


class WorkerForm(forms.ModelForm):
    class Meta:
        model = Worker
        fields = ['dni', 'last_name', 'first_name', 'profession', 'user', 'signature']

    def __init__(self, *args, **kwargs):
        super(WorkerForm, self).__init__(*args, **kwargs)
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


class ProducerForm(forms.ModelForm):
    class Meta:
        model = Producer
        fields = ['dni', 'last_name', 'first_name']

    def __init__(self, *args, **kwargs):
        super(ProducerForm, self).__init__(*args, **kwargs)
        for field in iter(self.fields):
            if field == 'dni':
                self.fields[field].widget.attrs.update({
                    'class': 'form-control entero'
                })
            else:
                self.fields[field].widget.attrs.update({
                    'class': 'form-control'
                })


class PositionForm(forms.ModelForm):
    class Meta:
        model = Position
        fields = ['name', 'office', 'worker', 'start_date', 'end_date', 'is_leadership', 'is_assistant']

    def __init__(self, *args, **kwargs):
        super(PositionForm, self).__init__(*args, **kwargs)
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


class PositionUpdateForm(forms.ModelForm):
    class Meta:
        model = Position
        fields = ['name', 'office', 'worker', 'start_date', 'end_date', 'is_leadership', 'is_assistant']

    def __init__(self, *args, **kwargs):
        super(PositionUpdateForm, self).__init__(*args, **kwargs)
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
