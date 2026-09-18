from tambox.importacion import leer_filas


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
