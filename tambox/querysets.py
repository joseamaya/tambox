from django.db import models


class NavigableQuerySet(models.query.QuerySet):
    """Navegacion entre registros consecutivos por pk.

    `anterior()` y `siguiente()` devuelven el objeto (no la pk), porque hay
    consumidores que necesitan la instancia: el tag `url_anterior` llama a
    `verificar_acceso()` sobre ella, y las URL montadas sobre `code` la
    resuelven via `__str__`. Los modelos cuyas rutas usan `pk` exponen un
    envoltorio que devuelve `pk`, que es lo que esperan sus plantillas.
    """

    def ultimo(self):
        return self.order_by('pk').last()

    def anterior(self, instancia):
        try:
            return self.filter(pk__lt=instancia.pk).order_by('-pk')[0]
        except IndexError:
            return self.order_by('pk').last()

    def siguiente(self, instancia):
        try:
            return self.filter(pk__gt=instancia.pk).order_by('pk')[0]
        except IndexError:
            return self.order_by('pk').first()
