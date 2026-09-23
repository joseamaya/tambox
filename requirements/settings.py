"""Constantes de requerimientos que no dependen de la base de datos.

Los valores que salen de la base de datos viven en tambox.config.
"""

from model_utils.choices import Choices
from django.utils.translation import gettext as _

MONTH_CHOICES = Choices((1, _('ENERO')),
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

REQUIREMENT_STATUS_CHOICES = Choices(('PEND', _('PENDIENTE')),
                             ('COTIZ', _('COTIZADO')),
                             ('COTIZ_PARC', _('COTIZADO PARCIALMENTE')),
                             ('COMP', _('COMPRADO')),
                             ('COMP_PARC', _('COMPRADO PARCIALMENTE')),
                             ('ATEN', _('ATENDIDO')),
                             ('ATEN_PARC', _('ATENDIDO PARCIALMENTE')),
                             ('CANC', _('CANCELADO')),
                             )

LEADERSHIP_CHOICES = Choices(('APROB_JEF', _('APROBADO JEFATURA')),
                           ('DESAP_JEF', _('DESAPROBADO JEFATURA')))
