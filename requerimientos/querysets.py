from django.db import models
from django.db.models import Max

from tambox.querysets import NavegableQuerySet


class PreviousQuerySet(models.query.QuerySet):
    def requerimiento_anterior(self, anio):
        return self.filter(created__year=anio).aggregate(Max('code'))


class RequirementQuerySet(NavegableQuerySet, PreviousQuerySet):
    def requerimientos_activos_por_usuario(self, usuario, estado):
        return self.filter(requester__user=usuario).exclude(status=estado).order_by('code')

    def actualizar_requerimiento(self, code):
        return self.filter(code=code).update(status=False)

    def requerimientos_oficina_usuario(self, oficina_usuario):
        return self.filter(office=oficina_usuario)

    def requerimientos_gerencia_usuario(self, oficina_usuario):
        oficinas = oficina_usuario.superior.all()
        return self.filter(office__in=oficinas)


class RequirementApprovalQuerySet(models.query.QuerySet):
    def aprobaciones_pendientes_oficina_usuario(self, requerimientos, level):
        return self.filter(requirement__in=requerimientos, level=level, is_active=True)

    def aprobaciones_pendientes_gerencia_usuario(self, requerimientos, level):
        return self.filter(requirement__in=requerimientos, level=level, is_active=True)
