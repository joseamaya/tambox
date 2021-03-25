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
    def requerimientos_activos_por_usuario(self, usuario, estado):
        return self.filter(solicitante__usuario=usuario).exclude(estado=estado).order_by('codigo')

    def actualizar_requerimiento(self, codigo):
        return self.filter(codigo=codigo).update(estado=False)

    def requerimientos_oficina_usuario(self, oficina_usuario):
        return self.filter(oficina=oficina_usuario)

    def requerimientos_gerencia_usuario(self, oficina_usuario):
        oficinas = oficina_usuario.superior.all()
        return self.filter(oficina__in=oficinas)


class AprobacionRequerimientoQuerySet(models.query.QuerySet):
    def aprobaciones_pendientes_oficina_usuario(self, requerimientos, nivel):
        return self.filter(requerimiento__in=requerimientos, nivel=nivel, estado=True)

    def aprobaciones_pendientes_gerencia_usuario(self, requerimientos, nivel):
        return self.filter(requerimiento__in=requerimientos, nivel=nivel, estado=True)
