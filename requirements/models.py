# -*- coding: utf-8 -*-
from django.db import models
from model_utils.models import TimeStampedModel
from administration.models import Worker, Office, ApprovalLevel
from products.models import Product
from requirements.querysets import RequirementQuerySet, RequirementApprovalQuerySet
from django.core.validators import MaxValueValidator
from datetime import date
from requirements.settings import MONTH_CHOICES, REQUIREMENT_STATUS_CHOICES
from tambox.statuses import classify, PARTIAL, EMPTY
from tambox.config import administration_office, budget, logistics, operations
from simple_history.models import HistoricalRecords
from django.db.models import Q
from django.core.exceptions import ObjectDoesNotExist, ValidationError


class Requirement(TimeStampedModel):
    code = models.CharField(unique=True, max_length=12)
    requester = models.ForeignKey(Worker, on_delete=models.CASCADE, related_name='requirements')
    office = models.ForeignKey(Office, on_delete=models.CASCADE, related_name='requirements')
    reason = models.CharField(max_length=100, blank=True)
    date = models.DateField()
    received_date = models.DateField(null=True)
    month = models.IntegerField(choices=MONTH_CHOICES)
    year = models.PositiveIntegerField(validators=[MaxValueValidator(9999)])
    notes = models.TextField()
    report = models.FileField(upload_to='informes', null=True)
    direct_delivery_to_requester = models.BooleanField(default=False)
    STATUS = REQUIREMENT_STATUS_CHOICES
    status = models.CharField(choices=STATUS, default=STATUS.PEND, max_length=20, verbose_name='Estado')
    history = HistoricalRecords()
    objects = RequirementQuerySet.as_manager()

    class Meta:
        permissions = (('ver_bienvenida', 'Puede ver bienvenida a la aplicación'),
                       ('ver_detalle_requerimiento', 'Puede ver detalle de Requerimiento'),
                       ('ver_tabla_requerimientos', 'Puede ver tabla de Requerimientos'),
                       ('ver_reporte_requerimientos_excel', 'Puede ver Reporte de Requerimientos en excel'),
                       ('puede_hacer_transferencia_requerimiento', 'Puede hacer transferencia de Requerimiento'),)

    def previous(self):
        previous = Requirement.objects.previous(self)
        return previous

    def next(self):
        following = Requirement.objects.next(self)
        return following

    @property
    def total(self):
        """Suma una columna, asi que el total es exacto con o sin agregado SQL.

        Se recorre el manager inverso en lugar de un .filter() para que
        `prefetch_related` sirva de algo en los bucles que cargan muchos
        requerimientos: un .filter() siempre lanza su propia consulta y se salta
        la cache. Se memoriza porque la maquina de estados y las plantillas lo
        invocan varias veces.
        """
        if not hasattr(self, '_calculated_total'):
            self._calculated_total = sum(detail.quantity
                                        for detail in self.details.all())
        return self._calculated_total

    @property
    def total_quoted(self):
        if not hasattr(self, '_calculated_quoted_total'):
            self._calculated_quoted_total = sum(detail.quoted_quantity
                                                 for detail in self.details.all())
        return self._calculated_quoted_total

    @property
    def total_purchased(self):
        if not hasattr(self, '_calculated_purchased_total'):
            self._calculated_purchased_total = sum(detail.purchased_quantity
                                                 for detail in self.details.all())
        return self._calculated_purchased_total

    def __str__(self):
        return self.code

    def set_status_quoted(self):
        caso = classify(self.total_quoted, self.total)
        if caso == EMPTY:
            status = Requirement.STATUS.PEND
        elif caso == PARTIAL:
            status = Requirement.STATUS.COTIZ_PARC
        else:
            status = Requirement.STATUS.COTIZ
        self.status = status
        return self.status

    def set_status_purchased(self):
        caso = classify(self.total_purchased, self.total)
        if caso == EMPTY:
            status = self.set_status_quoted()
        elif caso == PARTIAL:
            status = Requirement.STATUS.COMP_PARC
        else:
            status = Requirement.STATUS.COMP
        self.status = status
        return self.status

    def set_status_served(self):
        total = 0
        total_served = 0
        details = RequirementDetail.objects.filter(requirement=self)
        for detail in details:
            total = total + detail.quantity
            total_served = total_served + detail.served_quantity
        caso = classify(total_served, total)
        if caso == EMPTY:
            status = self.set_status_purchased()
        elif caso == PARTIAL:
            status = Requirement.STATUS.ATEN_PARC
        else:
            status = Requirement.STATUS.ATEN
        self.status = status
        return self.status

    def generate_code(self):
        year = self.created.year
        previous_requirement = Requirement.objects.previous_requirement(year)
        previous_id = previous_requirement['code__max']
        if previous_id is None:
            aux = 1
        else:
            aux = int(previous_id[-6:]) + 1
        correlativo = str(aux).zfill(6)
        code = 'RQ' + str(year) + correlativo
        return code

    def check_access(self, user, administration_office, logistics, budget):
        requester = self.requester
        worker = user.worker
        user_position = worker.position
        user_office = user_position.office
        if (user.is_staff
                or requester == worker
                or (user_office == self.office and user_position.is_leadership)
                or ((user_office == self.office.management
                     or user_office == administration_office
                     or user_office == logistics
                     or user_office == budget) and user_position.is_leadership)):
            return True
        else:
            return False

    @staticmethod
    def get_visible_requirements(user):
        try:
            worker = user.worker
            user_position = worker.position
            user_office = user_position.office
            if (((
                         user_office == administration_office() or user_office == budget()) and user_position.is_leadership) or
                    (user_office == logistics() and (user_position.is_leadership or user_position.is_assistant)) or
                    user.is_staff):
                queryset = Requirement.objects.all()
            elif user_position.is_leadership:
                queryset = Requirement.objects.office_user_requirements(user_office)
            else:
                queryset = Requirement.objects.active_requirements_by_user(user, Requirement.STATUS.CANC)
        except (AttributeError, ObjectDoesNotExist):
            queryset = []
        return queryset

    @staticmethod
    def get_requirements_ready_for_transfer():
        requirement_list = []
        requirements = Requirement.objects.filter(
            approval__level__description="LOGISTICA",
            approval__is_active=True).prefetch_related('details')
        for requirement in requirements:
            total = requirement.total
            total_purchased = requirement.total_purchased
            if total_purchased == 0 or total_purchased < total:
                requirement_list.append(requirement)
        return requirement_list

    def delete_requirement(self):
        self.status = Requirement.STATUS.CANC
        self.save()

    def save(self, *args, **kwargs):
        es_nuevo = self.code == ''
        if es_nuevo:
            self.code = self.generate_code()
            position = self.requester.position
            if position is None:
                raise ValidationError(
                    'No se puede registrar el requerimiento: el solicitante %s no tiene un puesto asignado.'
                    % self.requester)
            self.office = position.office

        super(Requirement, self).save()

        if es_nuevo:
            self.create_initial_approval(position)

    def create_initial_approval(self, position):
        """Crea la aprobacion del primer level. Requiere que el requerimiento ya
        tenga pk, por eso se llama despues de guardar."""
        if (self.office == administration_office() or self.office == operations()) and position.is_leadership:
            approval_levels = ApprovalLevel.objects.filter(description="JEFATURA")
            if approval_levels.count() > 0:
                RequirementApproval.objects.create(requirement=self,
                                                        level=approval_levels[0])
            return
        RequirementApproval.objects.create(requirement=self,
                                               level=position.set_level(self.office))


class RequirementDetail(TimeStampedModel):
    line_number = models.IntegerField()
    requirement = models.ForeignKey(Requirement, on_delete=models.CASCADE, related_name='details')
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='requirement_details', null=True)
    use = models.TextField(null=True)
    quantity = models.DecimalField(max_digits=15, decimal_places=5)
    quoted_quantity = models.DecimalField(max_digits=15, decimal_places=5, default=0)
    purchased_quantity = models.DecimalField(max_digits=15, decimal_places=5, default=0)
    served_quantity = models.DecimalField(max_digits=15, decimal_places=5, default=0)
    STATUS = REQUIREMENT_STATUS_CHOICES
    status = models.CharField(choices=STATUS, default=STATUS.PEND, max_length=20)
    history = HistoricalRecords()

    class Meta:
        permissions = (('can_view', 'Can view Detalle Requerimiento'),)
        ordering = ['line_number']

    def __str__(self):
        return self.requirement.code + ' ' + str(self.line_number)

    def set_status_quoted(self):
        caso = classify(self.quoted_quantity, self.quantity)
        if caso == EMPTY:
            status = RequirementDetail.STATUS.PEND
        elif caso == PARTIAL:
            status = RequirementDetail.STATUS.COTIZ_PARC
        else:
            status = RequirementDetail.STATUS.COTIZ
        self.status = status
        return self.status

    def set_status_purchased(self):
        caso = classify(self.purchased_quantity, self.quantity)
        if caso == EMPTY:
            status = self.set_status_quoted()
        elif caso == PARTIAL:
            status = RequirementDetail.STATUS.COMP_PARC
        else:
            status = RequirementDetail.STATUS.COMP
        self.status = status
        return self.status

    def set_status_served(self):
        caso = classify(self.served_quantity, self.quantity)
        if caso == EMPTY:
            status = self.set_status_purchased()
        elif caso == PARTIAL:
            status = RequirementDetail.STATUS.ATEN_PARC
        else:
            status = RequirementDetail.STATUS.ATEN
        self.status = status
        return self.status


class RequirementApproval(TimeStampedModel):
    requirement = models.OneToOneField(Requirement, on_delete=models.CASCADE, related_name='approval', primary_key=True)
    level = models.ForeignKey(ApprovalLevel, on_delete=models.CASCADE, related_name='approvals')
    is_active = models.BooleanField(default=True, verbose_name='Estado')
    rejection_reason = models.TextField(default='')
    received_date = models.DateField(null=True)
    history = HistoricalRecords()
    objects = RequirementApprovalQuerySet.as_manager()

    class Meta:
        permissions = (('ver_tabla_aprobacion_requerimientos', 'Puede ver tabla de Aprobación de Requerimientos'),
                       ('ver_reporte_aprobacion_requerimientos_excel',
                        'Puede ver Reporte de Aprobación de Requerimientos en excel'),)

    def __str__(self):
        return str(self.pk)

    def check_approval_access(self, user):
        user_position = user.worker.position
        requirement_office = self.requirement.office
        current_level = user_position.set_level(requirement_office)
        previous_level = current_level.superior.all()[0]
        if ((self.level == current_level or self.level == previous_level) or
                (self.level.description == "JEFATURA" and current_level.description == "GERENCIA ADMINISTRACION") or
                (
                        self.level.description == "USUARIO" and requirement_office == operations() and current_level.description == "GERENCIA INMEDIATA")):
            return True
        else:
            return False

    def get_superior_approval_office(self):
        level = self.level
        if level.description == "PRESUPUESTO":
            office = logistics()
        elif level.description == "GERENCIA ADMINISTRACION":
            office = budget()
        elif level.description == "GERENCIA INMEDIATA":
            office = administration_office()
        elif level.description == "JEFATURA":
            office = self.requirement.office.management
        elif level.description == "USUARIO":
            office = self.requirement.office
        else:
            office = None
        return office

    @staticmethod
    def get_pending_approvals(user):
        user_position = user.worker.position
        user_office = user_position.office
        queryset = []
        if user_office == logistics() and user_position.is_leadership:
            queryset = RequirementApproval.objects.filter(~Q(requirement__status=Requirement.STATUS.CANC),
                                                              level__description="USUARIO",
                                                              is_active=True)
        return queryset

    def save(self, *args, **kwargs):
        if self.level.description == "LOGISTICA" and self.is_active == True:
            self.requirement.received_date = date.today()
        super(RequirementApproval, self).save()
