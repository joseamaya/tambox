"""Fechas conscientes de zona horaria.

Con `USE_TZ = True`, filtrar un `DateTimeField` con un `date` suelto dispara
`RuntimeWarning: received a naive datetime`. Django lo interpreta igual -en la
zona del proyecto-, asi que el resultado no cambia, pero ensucia los logs de cada
report. Esta conversion vive aqui para que sea una sola.
"""
import datetime

from django.utils import timezone


def aware(value):
    """Un `date` o un `datetime` naive, interpretado en la zona del proyecto."""
    if isinstance(value, datetime.datetime):
        if timezone.is_aware(value):
            return value
        return timezone.make_aware(value)
    return timezone.make_aware(datetime.datetime.combine(value, datetime.time.min))


def parse_date(value):
    """Un `date` desde ISO (input nativo) o dd/mm/yyyy (a mano)."""
    for fmt in ('%Y-%m-%d', '%d/%m/%Y', '%d/%m/%y'):
        try:
            return datetime.datetime.strptime(value, fmt).date()
        except (TypeError, ValueError):
            continue
    raise ValueError('Fecha invalida: %r' % (value,))


def parse_time(value):
    """Una `time` desde HH:MM:SS/HH:MM o HH : MM : SS (wickedpicker viejo)."""
    value = value.replace(' ', '')
    for fmt in ('%H:%M:%S', '%H:%M'):
        try:
            return datetime.datetime.strptime(value, fmt).time()
        except (TypeError, ValueError):
            continue
    raise ValueError('Hora invalida: %r' % (value,))
