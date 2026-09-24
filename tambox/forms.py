"""Utilidades de formularios compartidas.

`BootstrapFormMixin` aplica las clases de Bootstrap 5 a los widgets de un
formulario y marca los campos con error, para que las plantillas no repitan el
bucle de `form-control` en cada `__init__`.
"""
from django import forms


class BootstrapFormMixin:
    """Pone `form-control`/`form-select`/`form-check-input` a los widgets.

    Respeta las clases propias de cada campo (`decimal`, `productos`, ...),
    normaliza los `select` que hoy traen `form-control`, y añade `is-invalid`
    a los campos que fallan la validacion.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name, field in self.fields.items():
            widget = field.widget
            if isinstance(widget, forms.HiddenInput):
                continue
            self._set_class(widget, self._base_class(widget))
            if field.help_text:
                widget.attrs['aria-describedby'] = self._element_id(name, 'help')

    def full_clean(self):
        super().full_clean()
        if not self._errors:
            return
        for name, field in self.fields.items():
            widget = field.widget
            if self._errors.get(name):
                self._set_class(widget, 'is-invalid')
                widget.attrs['aria-invalid'] = 'true'
                self._add_described_by(widget, self._element_id(name, 'error'))
            else:
                self._remove_class(widget, 'is-invalid')
                widget.attrs.pop('aria-invalid', None)

    def _element_id(self, name, suffix):
        """Mismo id que `field.auto_id` en `includes/field.html`.

        Se calcula a mano en vez de leer `self[name].auto_id` porque crear el
        `BoundField` lo deja en cache con el prefijo actual: varias vistas de
        fila de formset cambian `form.prefix` despues de construir el form.
        """
        if not self.auto_id:
            return ''
        return '%s-%s' % (self.auto_id % self.add_prefix(name), suffix)

    @staticmethod
    def _add_described_by(widget, element_id):
        described = set((widget.attrs.get('aria-describedby') or '').split())
        described.add(element_id)
        widget.attrs['aria-describedby'] = ' '.join(sorted(described))

    @staticmethod
    def _base_class(widget):
        if isinstance(widget, (forms.CheckboxInput, forms.RadioSelect,
                               forms.CheckboxSelectMultiple)):
            return 'form-check-input'
        if isinstance(widget, (forms.Select, forms.SelectMultiple)):
            return 'form-select'
        return 'form-control'

    @staticmethod
    def _set_class(widget, css_class):
        classes = set((widget.attrs.get('class') or '').split())
        if css_class == 'form-select':
            classes.discard('form-control')
        elif css_class == 'form-control':
            classes.discard('form-select')
        classes.add(css_class)
        widget.attrs['class'] = ' '.join(sorted(classes))

    @staticmethod
    def _remove_class(widget, css_class):
        classes = set((widget.attrs.get('class') or '').split())
        classes.discard(css_class)
        widget.attrs['class'] = ' '.join(sorted(classes))
