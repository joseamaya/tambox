# -*- coding: utf-8 -*-
"""Constantes de compras que no dependen de la base de datos.

Los valores que salen de la base de datos viven en tambox.config.
"""

from model_utils.choices import Choices
from django.utils.translation import gettext as _

SEARCH_PARAMETERS = (('F', 'POR FECHA',), ('M', 'POR MES',), ('A', 'POR AÑO',))

MONTHS = (
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

QUOTATION_STATUS_CHOICES = Choices(('PEND', _('PENDIENTE')),
                               ('ELEG', _('ELEGIDA')),
                               ('ELEG_PARC', _('ELEGIDA PARCIALMENTE')),
                               ('DESC', _('DESCARTADA')),
                               ('CANC', _('CANCELADO')), )
