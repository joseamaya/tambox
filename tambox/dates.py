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
