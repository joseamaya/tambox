from django.http import HttpResponseBadRequest

from tambox.imports import read_rows


class AjaxOnlyMixin(object):
    """Para las vistas que solo existen para el JavaScript del sistema.

    Antes cada una verificaba la cabecera dentro de su `get` y, si faltaba,
    caia por el `if` y devolvia None: Django lo convierte en un 500. Aqui la
    peticion que no viene del JavaScript recibe un 400, que es lo que es.

    Cada vista declara en `required_params` los parametros que lee sin
    condicion. Si falta alguno tambien es un 400, no un KeyError.
    """

    required_params = ()

    def dispatch(self, request, *args, **kwargs):
        if request.headers.get('X-Requested-With') != 'XMLHttpRequest':
            return HttpResponseBadRequest('Esta direccion responde al JavaScript del sistema.')
        missing = [param for param in self.required_params
                     if param not in request.GET]
        if missing:
            return HttpResponseBadRequest('Faltan los params: %s.' % ', '.join(missing))
        return super(AjaxOnlyMixin, self).dispatch(request, *args, **kwargs)


class CsvImportMixin(object):
    """Para las vistas que importan un CSV con el mismo patron.

    Guarda el archivo subido, recorre el CSV y delega cada fila en
    `process_row()`. El exito lo resuelve `FormView` con `success_url`, asi
    que la vista solo declara las columnas que lee.
    """

    def form_valid(self, form):
        form.save()
        for row in read_rows(form.cleaned_data['file']):
            self.process_row(row)
        return super(CsvImportMixin, self).form_valid(form)

    def process_row(self, row):
        raise NotImplementedError
