# -*- coding: utf-8 -*-
from django.db import models
from model_utils.models import TimeStampedModel
from administracion.models import Trabajador, Oficina, NivelAprobacion
from productos.models import Producto
from requerimientos.querysets import RequerimientoQuerySet, AprobacionRequerimientoQuerySet
from django.core.validators import MaxValueValidator
from datetime import date
from requerimientos.settings import CHOICES_MESES, CHOICES_ESTADO_REQ
from tambox.estados import clasificar, PARCIAL, VACIO
from tambox.configuracion import oficina_administracion, presupuesto, logistica, operaciones
from simple_history.models import HistoricalRecords
from django.db.models import Q
from django.core.exceptions import ObjectDoesNotExist, ValidationError


class Requerimiento(TimeStampedModel):
    code = models.CharField(unique=True, max_length=12)
    solicitante = models.ForeignKey(Trabajador, on_delete=models.CASCADE, related_name='requirements')
    oficina = models.ForeignKey(Oficina, on_delete=models.CASCADE, related_name='requirements')
    reason = models.CharField(max_length=100, blank=True)
    date = models.DateField()
    received_date = models.DateField(null=True)
    month = models.IntegerField(choices=CHOICES_MESES)
    year = models.PositiveIntegerField(validators=[MaxValueValidator(9999)])
    notes = models.TextField()
    report = models.FileField(upload_to='informes', null=True)
    direct_delivery_to_requester = models.BooleanField(default=False)
    STATUS = CHOICES_ESTADO_REQ
    status = models.CharField(choices=STATUS, default=STATUS.PEND, max_length=20, verbose_name='Estado')
    history = HistoricalRecords()
    objects = RequerimientoQuerySet.as_manager()

    class Meta:
        permissions = (('ver_bienvenida', 'Puede ver bienvenida a la aplicación'),
                       ('ver_detalle_requerimiento', 'Puede ver detalle de Requerimiento'),
                       ('ver_tabla_requerimientos', 'Puede ver tabla de Requerimientos'),
                       ('ver_reporte_requerimientos_excel', 'Puede ver Reporte de Requerimientos en excel'),
                       ('puede_hacer_transferencia_requerimiento', 'Puede hacer transferencia de Requerimiento'),)

    def anterior(self):
        ant = Requerimiento.objects.anterior(self)
        return ant

    def siguiente(self):
        sig = Requerimiento.objects.siguiente(self)
        return sig

    @property
    def total(self):
        """Suma una columna, asi que el total es exacto con o sin agregado SQL.

        Se recorre el manager inverso en lugar de un .filter() para que
        `prefetch_related` sirva de algo en los bucles que cargan muchos
        requerimientos: un .filter() siempre lanza su propia consulta y se salta
        la cache. Se memoriza porque la maquina de estados y las plantillas lo
        invocan varias veces.
        """
        if not hasattr(self, '_total_calculado'):
            self._total_calculado = sum(detalle.quantity
                                        for detalle in self.details.all())
        return self._total_calculado

    @property
    def total_cotizado(self):
        if not hasattr(self, '_total_cotizado_calculado'):
            self._total_cotizado_calculado = sum(detalle.quoted_quantity
                                                 for detalle in self.details.all())
        return self._total_cotizado_calculado

    @property
    def total_comprado(self):
        if not hasattr(self, '_total_comprado_calculado'):
            self._total_comprado_calculado = sum(detalle.purchased_quantity
                                                 for detalle in self.details.all())
        return self._total_comprado_calculado

    def __str__(self):
        return self.code

    def establecer_estado_cotizado(self):
        caso = clasificar(self.total_cotizado, self.total)
        if caso == VACIO:
            estado = Requerimiento.STATUS.PEND
        elif caso == PARCIAL:
            estado = Requerimiento.STATUS.COTIZ_PARC
        else:
            estado = Requerimiento.STATUS.COTIZ
        self.status = estado
        return self.status

    def establecer_estado_comprado(self):
        caso = clasificar(self.total_comprado, self.total)
        if caso == VACIO:
            estado = self.establecer_estado_cotizado()
        elif caso == PARCIAL:
            estado = Requerimiento.STATUS.COMP_PARC
        else:
            estado = Requerimiento.STATUS.COMP
        self.status = estado
        return self.status

    def establecer_estado_atendido(self):
        total = 0
        total_atendido = 0
        detalles = DetalleRequerimiento.objects.filter(requerimiento=self)
        for detalle in detalles:
            total = total + detalle.quantity
            total_atendido = total_atendido + detalle.served_quantity
        caso = clasificar(total_atendido, total)
        if caso == VACIO:
            estado = self.establecer_estado_comprado()
        elif caso == PARCIAL:
            estado = Requerimiento.STATUS.ATEN_PARC
        else:
            estado = Requerimiento.STATUS.ATEN
        self.status = estado
        return self.status

    def generar_code(self):
        anio = self.created.year
        req_ant = Requerimiento.objects.requerimiento_anterior(anio)
        id_ant = req_ant['code__max']
        if id_ant is None:
            aux = 1
        else:
            aux = int(id_ant[-6:]) + 1
        correlativo = str(aux).zfill(6)
        code = 'RQ' + str(anio) + correlativo
        return code

    def verificar_acceso(self, usuario, oficina_administracion, logistica, presupuesto):
        solicitante = self.solicitante
        trabajador = usuario.worker
        puesto_usuario = trabajador.puesto
        oficina_usuario = puesto_usuario.oficina
        if (usuario.is_staff
                or solicitante == trabajador
                or (oficina_usuario == self.oficina and puesto_usuario.is_leadership)
                or ((oficina_usuario == self.oficina.gerencia
                     or oficina_usuario == oficina_administracion
                     or oficina_usuario == logistica
                     or oficina_usuario == presupuesto) and puesto_usuario.is_leadership)):
            return True
        else:
            return False

    @staticmethod
    def obtener_requerimientos_visibles(usuario):
        try:
            trabajador = usuario.worker
            puesto_usuario = trabajador.puesto
            oficina_usuario = puesto_usuario.oficina
            if (((
                         oficina_usuario == oficina_administracion() or oficina_usuario == presupuesto()) and puesto_usuario.is_leadership) or
                    (oficina_usuario == logistica() and (puesto_usuario.is_leadership or puesto_usuario.is_assistant)) or
                    usuario.is_staff):
                queryset = Requerimiento.objects.all()
            elif puesto_usuario.is_leadership:
                queryset = Requerimiento.objects.requerimientos_oficina_usuario(oficina_usuario)
            else:
                queryset = Requerimiento.objects.requerimientos_activos_por_usuario(usuario, Requerimiento.STATUS.CANC)
        except (AttributeError, ObjectDoesNotExist):
            queryset = []
        return queryset

    @staticmethod
    def obtener_requerimientos_listos_transferencia():
        listado_requerimientos = []
        requerimientos = Requerimiento.objects.filter(
            approval__level__description="LOGISTICA",
            approval__is_active=True).prefetch_related('details')
        for requerimiento in requerimientos:
            total = requerimiento.total
            total_comprado = requerimiento.total_comprado
            if total_comprado == 0 or total_comprado < total:
                listado_requerimientos.append(requerimiento)
        return listado_requerimientos

    def eliminar_requerimiento(self):
        self.status = Requerimiento.STATUS.CANC
        self.save()

    def save(self, *args, **kwargs):
        es_nuevo = self.code == ''
        if es_nuevo:
            self.code = self.generar_code()
            puesto = self.solicitante.puesto
            if puesto is None:
                raise ValidationError(
                    'No se puede registrar el requerimiento: el solicitante %s no tiene un puesto asignado.'
                    % self.solicitante)
            self.oficina = puesto.oficina

        super(Requerimiento, self).save()

        if es_nuevo:
            self.crear_aprobacion_inicial(puesto)

    def crear_aprobacion_inicial(self, puesto):
        """Crea la aprobacion del primer level. Requiere que el requerimiento ya
        tenga pk, por eso se llama despues de guardar."""
        if (self.oficina == oficina_administracion() or self.oficina == operaciones()) and puesto.is_leadership:
            niveles_aprobacion = NivelAprobacion.objects.filter(description="JEFATURA")
            if niveles_aprobacion.count() > 0:
                AprobacionRequerimiento.objects.create(requerimiento=self,
                                                        level=niveles_aprobacion[0])
            return
        AprobacionRequerimiento.objects.create(requerimiento=self,
                                               level=puesto.establecer_nivel(self.oficina))


class DetalleRequerimiento(TimeStampedModel):
    line_number = models.IntegerField()
    requerimiento = models.ForeignKey(Requerimiento, on_delete=models.CASCADE, related_name='details')
    producto = models.ForeignKey(Producto, on_delete=models.CASCADE, related_name='requirement_details', null=True)
    use = models.TextField(null=True)
    quantity = models.DecimalField(max_digits=15, decimal_places=5)
    quoted_quantity = models.DecimalField(max_digits=15, decimal_places=5, default=0)
    purchased_quantity = models.DecimalField(max_digits=15, decimal_places=5, default=0)
    served_quantity = models.DecimalField(max_digits=15, decimal_places=5, default=0)
    STATUS = CHOICES_ESTADO_REQ
    status = models.CharField(choices=STATUS, default=STATUS.PEND, max_length=20)
    history = HistoricalRecords()

    class Meta:
        permissions = (('can_view', 'Can view Detalle Requerimiento'),)
        ordering = ['line_number']

    def __str__(self):
        return self.requerimiento.code + ' ' + str(self.line_number)

    def establecer_estado_cotizado(self):
        caso = clasificar(self.quoted_quantity, self.quantity)
        if caso == VACIO:
            estado = DetalleRequerimiento.STATUS.PEND
        elif caso == PARCIAL:
            estado = DetalleRequerimiento.STATUS.COTIZ_PARC
        else:
            estado = DetalleRequerimiento.STATUS.COTIZ
        self.status = estado
        return self.status

    def establecer_estado_comprado(self):
        caso = clasificar(self.purchased_quantity, self.quantity)
        if caso == VACIO:
            estado = self.establecer_estado_cotizado()
        elif caso == PARCIAL:
            estado = DetalleRequerimiento.STATUS.COMP_PARC
        else:
            estado = DetalleRequerimiento.STATUS.COMP
        self.status = estado
        return self.status

    def establecer_estado_atendido(self):
        caso = clasificar(self.served_quantity, self.quantity)
        if caso == VACIO:
            estado = self.establecer_estado_comprado()
        elif caso == PARCIAL:
            estado = DetalleRequerimiento.STATUS.ATEN_PARC
        else:
            estado = DetalleRequerimiento.STATUS.ATEN
        self.status = estado
        return self.status


class AprobacionRequerimiento(TimeStampedModel):
    requerimiento = models.OneToOneField(Requerimiento, on_delete=models.CASCADE, related_name='approval', primary_key=True)
    level = models.ForeignKey(NivelAprobacion, on_delete=models.CASCADE, related_name='approvals')
    is_active = models.BooleanField(default=True, verbose_name='Estado')
    rejection_reason = models.TextField(default='')
    received_date = models.DateField(null=True)
    history = HistoricalRecords()
    objects = AprobacionRequerimientoQuerySet.as_manager()

    class Meta:
        permissions = (('ver_tabla_aprobacion_requerimientos', 'Puede ver tabla de Aprobación de Requerimientos'),
                       ('ver_reporte_aprobacion_requerimientos_excel',
                        'Puede ver Reporte de Aprobación de Requerimientos en excel'),)

    def __str__(self):
        return str(self.pk)

    def verificar_acceso_aprobacion(self, usuario):
        puesto_usuario = usuario.worker.puesto
        oficina_requerimiento = self.requerimiento.oficina
        nivel_actual = puesto_usuario.establecer_nivel(oficina_requerimiento)
        nivel_anterior = nivel_actual.superior.all()[0]
        if ((self.level == nivel_actual or self.level == nivel_anterior) or
                (self.level.description == "JEFATURA" and nivel_actual.description == "GERENCIA ADMINISTRACION") or
                (
                        self.level.description == "USUARIO" and oficina_requerimiento == operaciones() and nivel_actual.description == "GERENCIA INMEDIATA")):
            return True
        else:
            return False

    def obtener_oficina_aprobacion_superior(self):
        level = self.level
        if level.description == "PRESUPUESTO":
            oficina = logistica()
        elif level.description == "GERENCIA ADMINISTRACION":
            oficina = presupuesto()
        elif level.description == "GERENCIA INMEDIATA":
            oficina = oficina_administracion()
        elif level.description == "JEFATURA":
            oficina = self.requerimiento.oficina.gerencia
        elif level.description == "USUARIO":
            oficina = self.requerimiento.oficina
        else:
            oficina = None
        return oficina

    @staticmethod
    def obtener_aprobaciones_pendientes(usuario):
        puesto_usuario = usuario.worker.puesto
        oficina_usuario = puesto_usuario.oficina
        queryset = []
        if oficina_usuario == logistica() and puesto_usuario.is_leadership:
            queryset = AprobacionRequerimiento.objects.filter(~Q(requerimiento__status=Requerimiento.STATUS.CANC),
                                                              level__description="USUARIO",
                                                              is_active=True)
        return queryset

    def save(self, *args, **kwargs):
        if self.level.description == "LOGISTICA" and self.is_active == True:
            self.requerimiento.received_date = date.today()
        super(AprobacionRequerimiento, self).save()
