from django.http import HttpResponseBadRequest

from tambox.importacion import leer_filas


class SoloAjaxMixin(object):
    """Para las vistas que solo existen para el JavaScript del sistema.

    Antes cada una verificaba la cabecera dentro de su `get` y, si faltaba,
    caia por el `if` y devolvia None: Django lo convierte en un 500. Aqui la
    peticion que no viene del JavaScript recibe un 400, que es lo que es.

    Cada vista declara en `parametros_requeridos` los parametros que lee sin
    condicion. Si falta alguno tambien es un 400, no un KeyError.
    """

    parametros_requeridos = ()

    def dispatch(self, request, *args, **kwargs):
        if request.headers.get('X-Requested-With') != 'XMLHttpRequest':
            return HttpResponseBadRequest('Esta direccion responde al JavaScript del sistema.')
        faltantes = [parametro for parametro in self.parametros_requeridos
                     if parametro not in request.GET]
        if faltantes:
            return HttpResponseBadRequest('Faltan los parametros: %s.' % ', '.join(faltantes))
        return super(SoloAjaxMixin, self).dispatch(request, *args, **kwargs)


class CargarCsvMixin(object):
    """Para las vistas que importan un CSV con el mismo patron.

    Guarda el archivo subido, recorre el CSV y delega cada fila en
    `procesar_fila()`. El exito lo resuelve `FormView` con `success_url`, asi
    que la vista solo declara las columnas que lee.
    """

    def form_valid(self, form):
        form.save()
        for fila in leer_filas(form.cleaned_data['archivo']):
            self.procesar_fila(fila)
        return super(CargarCsvMixin, self).form_valid(form)

    def procesar_fila(self, fila):
        raise NotImplementedError
