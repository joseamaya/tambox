import csv
import os

from django.conf import settings


def leer_filas(docfile):
    """Recorre las filas del CSV que se acaba de subir.

    La codificacion es explicita: antes algunos importadores la omitian y
    quedaban dependiendo del locale del sistema, lo que da resultados distintos
    en Linux y en Windows.
    """
    ruta = os.path.join(settings.MEDIA_ROOT, 'archivos', str(docfile))
    with open(ruta, encoding='utf8') as archivo:
        for fila in csv.reader(archivo, delimiter=',', quotechar='"'):
            yield fila
