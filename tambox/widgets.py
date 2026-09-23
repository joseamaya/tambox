"""Widgets de fecha y hora nativos del navegador.

Sustituyen a jQuery UI datepicker y wickedpicker. El navegador manda ISO
(`YYYY-MM-DD` / `HH:MM:SS`), que los formatos del proyecto ya aceptan.
"""
from django import forms


class DateInput(forms.DateInput):
    input_type = 'date'

    def __init__(self, *args, **kwargs):
        kwargs.setdefault('format', '%Y-%m-%d')
        super().__init__(*args, **kwargs)


class DateTimeInput(forms.DateTimeInput):
    input_type = 'date'

    def __init__(self, *args, **kwargs):
        kwargs.setdefault('format', '%Y-%m-%d')
        super().__init__(*args, **kwargs)


class TimeInput(forms.TimeInput):
    input_type = 'time'

    def __init__(self, *args, **kwargs):
        kwargs.setdefault('format', '%H:%M:%S')
        attrs = kwargs.setdefault('attrs', {})
        attrs.setdefault('step', 1)
        super().__init__(*args, **kwargs)


class NativeDateFieldsMixin:
    """Pone `type=date`/`type=time` a los campos de fecha del formulario.

    El formato ya es ISO por `FORMAT_MODULE_PATH`; esto solo hace que el
    navegador abra su selector nativo en vez de un campo de texto.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            if isinstance(field, forms.TimeField):
                field.widget.input_type = 'time'
                field.widget.attrs.setdefault('step', 1)
            elif isinstance(field, (forms.DateField, forms.DateTimeField)):
                field.widget.input_type = 'date'
