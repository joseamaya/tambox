from model_utils.choices import Choices
from django.utils.translation import gettext as _
from contabilidad.models import Configuracion, Empresa

try:
    CONFIGURACION = Configuracion.objects.first()
    OPERACIONES = CONFIGURACION.operaciones
    OFICINA_ADMINISTRACION = CONFIGURACION.administracion
    PRESUPUESTO = CONFIGURACION.presupuesto
    LOGISTICA = CONFIGURACION.logistica
except:
    CONFIGURACION = None
    OPERACIONES = None
    OFICINA_ADMINISTRACION = None
    PRESUPUESTO = None
    LOGISTICA = None

try:
    EMPRESA = Empresa.load()
except:
    EMPRESA = None

CHOICES_MESES = Choices((1, _('ENERO')),
                        (2, _('FEBRERO')),
                        (3, _('MARZO')),
                        (4, _('ABRIL')),
                        (5, _('MAYO')),
                        (6, _('JUNIO')),
                        (7, _('JULIO')),
                        (8, _('AGOSTO')),
                        (9, _('SETIEMBRE')),
                        (10, _('OCTUBRE')),
                        (11, _('NOVIEMBRE')),
                        (12, _('DICIEMBRE')),
                        )

CHOICES_ESTADO_REQ = Choices(('PEND', _('PENDIENTE')),
                             ('COTIZ', _('COTIZADO')),
                             ('COTIZ_PARC', _('COTIZADO PARCIALMENTE')),
                             ('COMP', _('COMPRADO')),
                             ('COMP_PARC', _('COMPRADO PARCIALMENTE')),
                             ('ATEN', _('ATENDIDO')),
                             ('ATEN_PARC', _('ATENDIDO PARCIALMENTE')),
                             ('CANC', _('CANCELADO')),
                             )

CHOICES_JEFATURA = Choices(('APROB_JEF', _('APROBADO JEFATURA')),
                           ('DESAP_JEF', _('DESAPROBADO JEFATURA')))

CHOICES_GER_INM = Choices(('APROB_GER_INM', _('APROBADO GERENCIA INMEDIATA')),
                          ('DESAP_GER_INM', _('DESAPROBADO GERENCIA INMEDIATA')))

CHOICES_GER_ADM = Choices(('APROB_GER_ADM', _('APROBADO GERENCIA ADMINISTRACION')),
                          ('DESAP_GER_ADM', _('DESAPROBADO GERENCIA ADMINISTRACION')))

CHOICES_PRES = Choices(('APROB_PRES', _('APROBADO PRESUPUESTO')),
                       ('DESAP_PRES', _('DESAPROBADO PRESUPUESTO')))

CHOICES_LOG = Choices(('APROB_LOG', _('APROBADO LOGISTICA')),
                      ('DESAP_LOG', _('DESAPROBADO LOGISTICA')))

CHOICES_VACIA = Choices()

CHOICES_APROB = Choices(('APROB', _('APROBADO')),
                        ('DESAP', _('DESAPROBADO')))