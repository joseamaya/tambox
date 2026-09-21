from django.db import models
from django.db.models import Max

from tambox.querysets import NavigableQuerySet


class PreviousQuerySet(models.query.QuerySet):
    def previous_requirement(self, year):
        return self.filter(created__year=year).aggregate(Max('code'))


class RequirementQuerySet(NavigableQuerySet, PreviousQuerySet):
    def active_requirements_by_user(self, usuario, status):
        return self.filter(requester__user=usuario).exclude(status=status).order_by('code')

    def update_requirement(self, code):
        return self.filter(code=code).update(status=False)

    def office_user_requirements(self, user_office):
        return self.filter(office=user_office)

    def management_user_requirements(self, user_office):
        offices = user_office.superior.all()
        return self.filter(office__in=offices)


class RequirementApprovalQuerySet(models.query.QuerySet):
    def pending_approvals_office_user(self, requerimientos, level):
        return self.filter(requirement__in=requerimientos, level=level, is_active=True)

    def pending_approvals_management_user(self, requerimientos, level):
        return self.filter(requirement__in=requerimientos, level=level, is_active=True)
