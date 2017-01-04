# -*- coding: utf-8 -*-
from model_utils.choices import Choices
from django.utils.translation import gettext as _
from contabilidad.models import Configuracion, Empresa

try:
    CONFIGURACION = Configuracion.objects.first()
    IMPUESTO_COMPRA = CONFIGURACION.impuesto_compra
except:
    CONFIGURACION = None
    IMPUESTO_COMPRA = None

try:
    EMPRESA = Empresa.load()
except:
    EMPRESA = None
    
PARAMETROS_BUSQUEDA = (('F', 'POR FECHA',), ('M', 'POR MES',), ('A', 'POR AÑO',))

MESES = (
    (1, 'ENERO'),
    (2, 'FEBRERO'),
    (3, 'MARZO'),
    (4, 'ABRIL'),
    (5, 'MAYO'),
    (6, 'JUNIO'),
    (7, 'JULIO'),
    (8, 'AGOSTO'),
    (9, 'SETIEMBRE'),
    (10, 'OCTUBRE'),
    (11, 'NOVIEMBRE'),
    (12, 'DICIEMBRE'),
)

CHOICES_ESTADO_COTIZ = Choices(('PEND', _('PENDIENTE')),
                               ('ELEG', _('ELEGIDA')),
                               ('ELEG_PARC', _('ELEGIDA PARCIALMENTE')),
                               ('DESC', _('DESCARTADA')),
                               ('CANC', _('CANCELADO')),)