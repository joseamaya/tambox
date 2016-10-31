from django.db import models
from django.db.models import Max


class NavegableQuerySet(models.query.QuerySet):
    def anterior(self, instancia):
        try:
            return self.filter(pk__lt=instancia.pk).order_by('-pk')[0]
        except:
            return self.order_by('pk').last()

    def siguiente(self, instancia):
        try:
            return self.filter(pk__gt=instancia.pk).order_by('pk')[0]
        except:
            return self.order_by('pk').first()


class AnteriorQuerySet(models.query.QuerySet):
    def requerimiento_anterior(self, anio):
        return self.filter(created__year=anio).aggregate(Max('codigo'))


class RequerimientoQuerySet(NavegableQuerySet, AnteriorQuerySet):
    pass
