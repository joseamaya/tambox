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
    codigo = models.CharField(unique=True, max_length=12)
    solicitante = models.ForeignKey(Trabajador, on_delete=models.CASCADE)
    oficina = models.ForeignKey(Oficina, on_delete=models.CASCADE)
    motivo = models.CharField(max_length=100, blank=True)
    fecha = models.DateField()
    fecha_recepcion = models.DateField(null=True)
    mes = models.IntegerField(choices=CHOICES_MESES)
    annio = models.PositiveIntegerField(validators=[MaxValueValidator(9999)])
    observaciones = models.TextField()
    informe = models.FileField(upload_to='informes', null=True)
    entrega_directa_solicitante = models.BooleanField(default=False)
    STATUS = CHOICES_ESTADO_REQ
    estado = models.CharField(choices=STATUS, default=STATUS.PEND, max_length=20)
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
            self._total_calculado = sum(detalle.cantidad
                                        for detalle in self.detallerequerimiento_set.all())
        return self._total_calculado

    @property
    def total_cotizado(self):
        if not hasattr(self, '_total_cotizado_calculado'):
            self._total_cotizado_calculado = sum(detalle.cantidad_cotizada
                                                 for detalle in self.detallerequerimiento_set.all())
        return self._total_cotizado_calculado

    @property
    def total_comprado(self):
        if not hasattr(self, '_total_comprado_calculado'):
            self._total_comprado_calculado = sum(detalle.cantidad_comprada
                                                 for detalle in self.detallerequerimiento_set.all())
        return self._total_comprado_calculado

    def __str__(self):
        return self.codigo

    def establecer_estado_cotizado(self):
        caso = clasificar(self.total_cotizado, self.total)
        if caso == VACIO:
            estado = Requerimiento.STATUS.PEND
        elif caso == PARCIAL:
            estado = Requerimiento.STATUS.COTIZ_PARC
        else:
            estado = Requerimiento.STATUS.COTIZ
        self.estado = estado
        return self.estado

    def establecer_estado_comprado(self):
        caso = clasificar(self.total_comprado, self.total)
        if caso == VACIO:
            estado = self.establecer_estado_cotizado()
        elif caso == PARCIAL:
            estado = Requerimiento.STATUS.COMP_PARC
        else:
            estado = Requerimiento.STATUS.COMP
        self.estado = estado
        return self.estado

    def establecer_estado_atendido(self):
        total = 0
        total_atendido = 0
        detalles = DetalleRequerimiento.objects.filter(requerimiento=self)
        for detalle in detalles:
            total = total + detalle.cantidad
            total_atendido = total_atendido + detalle.cantidad_atendida
        caso = clasificar(total_atendido, total)
        if caso == VACIO:
            estado = self.establecer_estado_comprado()
        elif caso == PARCIAL:
            estado = Requerimiento.STATUS.ATEN_PARC
        else:
            estado = Requerimiento.STATUS.ATEN
        self.estado = estado
        return self.estado

    def generar_codigo(self):
        anio = self.created.year
        req_ant = Requerimiento.objects.requerimiento_anterior(anio)
        id_ant = req_ant['codigo__max']
        if id_ant is None:
            aux = 1
        else:
            aux = int(id_ant[-6:]) + 1
        correlativo = str(aux).zfill(6)
        codigo = 'RQ' + str(anio) + correlativo
        return codigo

    def verificar_acceso(self, usuario, oficina_administracion, logistica, presupuesto):
        solicitante = self.solicitante
        trabajador = usuario.trabajador
        puesto_usuario = trabajador.puesto
        oficina_usuario = puesto_usuario.oficina
        if (usuario.is_staff
                or solicitante == trabajador
                or (oficina_usuario == self.oficina and puesto_usuario.es_jefatura)
                or ((oficina_usuario == self.oficina.gerencia
                     or oficina_usuario == oficina_administracion
                     or oficina_usuario == logistica
                     or oficina_usuario == presupuesto) and puesto_usuario.es_jefatura)):
            return True
        else:
            return False

    @staticmethod
    def obtener_requerimientos_visibles(usuario):
        try:
            trabajador = usuario.trabajador
            puesto_usuario = trabajador.puesto
            oficina_usuario = puesto_usuario.oficina
            if (((
                         oficina_usuario == oficina_administracion() or oficina_usuario == presupuesto()) and puesto_usuario.es_jefatura) or
                    (oficina_usuario == logistica() and (puesto_usuario.es_jefatura or puesto_usuario.es_asistente)) or
                    usuario.is_staff):
                queryset = Requerimiento.objects.all()
            elif puesto_usuario.es_jefatura:
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
            aprobacionrequerimiento__nivel__descripcion="LOGISTICA",
            aprobacionrequerimiento__estado=True).prefetch_related('detallerequerimiento_set')
        for requerimiento in requerimientos:
            total = requerimiento.total
            total_comprado = requerimiento.total_comprado
            if total_comprado == 0 or total_comprado < total:
                listado_requerimientos.append(requerimiento)
        return listado_requerimientos

    def eliminar_requerimiento(self):
        self.estado = Requerimiento.STATUS.CANC
        self.save()

    def save(self, *args, **kwargs):
        es_nuevo = self.codigo == ''
        if es_nuevo:
            self.codigo = self.generar_codigo()
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
        """Crea la aprobacion del primer nivel. Requiere que el requerimiento ya
        tenga pk, por eso se llama despues de guardar."""
        if (self.oficina == oficina_administracion() or self.oficina == operaciones()) and puesto.es_jefatura:
            niveles_aprobacion = NivelAprobacion.objects.filter(descripcion="JEFATURA")
            if niveles_aprobacion.count() > 0:
                AprobacionRequerimiento.objects.create(requerimiento=self,
                                                        nivel=niveles_aprobacion[0])
            return
        AprobacionRequerimiento.objects.create(requerimiento=self,
                                               nivel=puesto.establecer_nivel(self.oficina))


class DetalleRequerimiento(TimeStampedModel):
    nro_detalle = models.IntegerField()
    requerimiento = models.ForeignKey(Requerimiento, on_delete=models.CASCADE)
    producto = models.ForeignKey(Producto, on_delete=models.CASCADE, null=True)
    uso = models.TextField(null=True)
    cantidad = models.DecimalField(max_digits=15, decimal_places=5)
    cantidad_cotizada = models.DecimalField(max_digits=15, decimal_places=5, default=0)
    cantidad_comprada = models.DecimalField(max_digits=15, decimal_places=5, default=0)
    cantidad_atendida = models.DecimalField(max_digits=15, decimal_places=5, default=0)
    STATUS = CHOICES_ESTADO_REQ
    estado = models.CharField(choices=STATUS, default=STATUS.PEND, max_length=20)
    history = HistoricalRecords()

    class Meta:
        permissions = (('can_view', 'Can view Detalle Requerimiento'),)
        ordering = ['nro_detalle']

    def __str__(self):
        return self.requerimiento.codigo + ' ' + str(self.nro_detalle)

    def establecer_estado_cotizado(self):
        caso = clasificar(self.cantidad_cotizada, self.cantidad)
        if caso == VACIO:
            estado = DetalleRequerimiento.STATUS.PEND
        elif caso == PARCIAL:
            estado = DetalleRequerimiento.STATUS.COTIZ_PARC
        else:
            estado = DetalleRequerimiento.STATUS.COTIZ
        self.estado = estado
        return self.estado

    def establecer_estado_comprado(self):
        caso = clasificar(self.cantidad_comprada, self.cantidad)
        if caso == VACIO:
            estado = self.establecer_estado_cotizado()
        elif caso == PARCIAL:
            estado = DetalleRequerimiento.STATUS.COMP_PARC
        else:
            estado = DetalleRequerimiento.STATUS.COMP
        self.estado = estado
        return self.estado

    def establecer_estado_atendido(self):
        caso = clasificar(self.cantidad_atendida, self.cantidad)
        if caso == VACIO:
            estado = self.establecer_estado_comprado()
        elif caso == PARCIAL:
            estado = DetalleRequerimiento.STATUS.ATEN_PARC
        else:
            estado = DetalleRequerimiento.STATUS.ATEN
        self.estado = estado
        return self.estado


class AprobacionRequerimiento(TimeStampedModel):
    requerimiento = models.OneToOneField(Requerimiento, on_delete=models.CASCADE, primary_key=True)
    nivel = models.ForeignKey(NivelAprobacion, on_delete=models.CASCADE)
    estado = models.BooleanField(default=True)
    motivo_desaprobacion = models.TextField(default='')
    fecha_recepcion = models.DateField(null=True)
    history = HistoricalRecords()
    objects = AprobacionRequerimientoQuerySet.as_manager()

    class Meta:
        permissions = (('ver_tabla_aprobacion_requerimientos', 'Puede ver tabla de Aprobación de Requerimientos'),
                       ('ver_reporte_aprobacion_requerimientos_excel',
                        'Puede ver Reporte de Aprobación de Requerimientos en excel'),)

    def __str__(self):
        return str(self.pk)

    def verificar_acceso_aprobacion(self, usuario):
        puesto_usuario = usuario.trabajador.puesto
        oficina_requerimiento = self.requerimiento.oficina
        nivel_actual = puesto_usuario.establecer_nivel(oficina_requerimiento)
        nivel_anterior = nivel_actual.superior.all()[0]
        if ((self.nivel == nivel_actual or self.nivel == nivel_anterior) or
                (self.nivel.descripcion == "JEFATURA" and nivel_actual.descripcion == "GERENCIA ADMINISTRACION") or
                (
                        self.nivel.descripcion == "USUARIO" and oficina_requerimiento == operaciones() and nivel_actual.descripcion == "GERENCIA INMEDIATA")):
            return True
        else:
            return False

    def obtener_oficina_aprobacion_superior(self):
        nivel = self.nivel
        if nivel.descripcion == "PRESUPUESTO":
            oficina = logistica()
        elif nivel.descripcion == "GERENCIA ADMINISTRACION":
            oficina = presupuesto()
        elif nivel.descripcion == "GERENCIA INMEDIATA":
            oficina = oficina_administracion()
        elif nivel.descripcion == "JEFATURA":
            oficina = self.requerimiento.oficina.gerencia
        elif nivel.descripcion == "USUARIO":
            oficina = self.requerimiento.oficina
        else:
            oficina = None
        return oficina

    @staticmethod
    def obtener_aprobaciones_pendientes(usuario):
        puesto_usuario = usuario.trabajador.puesto
        oficina_usuario = puesto_usuario.oficina
        queryset = []
        if oficina_usuario == logistica() and puesto_usuario.es_jefatura:
            queryset = AprobacionRequerimiento.objects.filter(~Q(requerimiento__estado=Requerimiento.STATUS.CANC),
                                                              nivel__descripcion="USUARIO",
                                                              estado=True)
        return queryset

    def save(self, *args, **kwargs):
        if self.nivel.descripcion == "LOGISTICA" and self.estado == True:
            self.requerimiento.fecha_recepcion = date.today()
        super(AprobacionRequerimiento, self).save()
