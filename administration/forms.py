# -*- coding: utf-8 -*-
from django import forms

from tambox.forms import BootstrapFormMixin
from tambox.widgets import NativeDateFieldsMixin
from administration.models import Office, Worker, Position, Profession,\
    ApprovalLevel, Producer


class ApprovalLevelForm(BootstrapFormMixin, forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super(ApprovalLevelForm, self).__init__(*args, **kwargs)
        self.fields['superior_level'].required = False

    class Meta:
        model = ApprovalLevel
        fields = ['description', 'superior_level']


class ProfessionForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = Profession
        fields = ['abbreviation', 'description']


class OfficeForm(BootstrapFormMixin, forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super(OfficeForm, self).__init__(*args, **kwargs)
        self.fields['dependency'].required = False

    class Meta:
        model = Office
        fields = ['code', 'name', 'dependency', 'is_management']


class WorkerForm(BootstrapFormMixin, forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super(WorkerForm, self).__init__(*args, **kwargs)
        self.fields['profession'].required = False

    class Meta:
        model = Worker
        fields = ['dni', 'last_name', 'first_name', 'profession', 'user', 'signature']


class ProducerForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = Producer
        fields = ['dni', 'last_name', 'first_name']


class PositionForm(BootstrapFormMixin, NativeDateFieldsMixin, forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super(PositionForm, self).__init__(*args, **kwargs)
        self.fields['end_date'].required = False
        self.fields['is_leadership'].required = False
        self.fields['is_assistant'].required = False
        self.fields['worker'].queryset = Worker.objects.exclude(
            pk__in=Position.objects.filter(end_date__isnull=True).values('worker'))

    class Meta:
        model = Position
        fields = ['name', 'office', 'worker', 'start_date', 'end_date', 'is_leadership', 'is_assistant']


class PositionUpdateForm(BootstrapFormMixin, NativeDateFieldsMixin, forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super(PositionUpdateForm, self).__init__(*args, **kwargs)
        self.fields['end_date'].required = False
        self.fields['is_leadership'].required = False
        self.fields['is_assistant'].required = False

    class Meta:
        model = Position
        fields = ['name', 'office', 'worker', 'start_date', 'end_date', 'is_leadership', 'is_assistant']
