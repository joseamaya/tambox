from django.db.models import Q
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


class HtmxListMixin(object):
    """ListView que htmx puede refrescar sin recargar la pagina.

    Cuando la peticion trae la cabecera `HX-Request` devuelve solo el fragmento
    de la tabla (`fragment_template_name`); si no, la pagina completa. El filtro
    de busqueda (`search_param`, por defecto `q`) se aplica sobre
    `search_fields`, que son nombres de campo del modelo.
    """

    fragment_template_name = None
    search_fields = ()
    search_param = 'q'

    def get_template_names(self):
        if (self.fragment_template_name
                and self.request.headers.get('HX-Request')):
            return [self.fragment_template_name]
        return super(HtmxListMixin, self).get_template_names()

    def get_queryset(self):
        queryset = super(HtmxListMixin, self).get_queryset()
        term = self.request.GET.get(self.search_param, '').strip()
        if term and self.search_fields:
            condition = Q()
            for field in self.search_fields:
                condition |= Q(**{field + '__icontains': term})
            queryset = queryset.filter(condition)
        return queryset


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
