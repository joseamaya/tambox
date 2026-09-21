import csv
import os

from django.conf import settings


def read_rows(docfile):
    """Recorre las rows del CSV que se acaba de subir.

    La codificacion es explicita: antes algunos importadores la omitian y
    quedaban dependiendo del locale del sistema, lo que da resultados distintos
    en Linux y en Windows.
    """
    path = os.path.join(settings.MEDIA_ROOT, 'archivos', str(docfile))
    with open(path, encoding='utf8') as file:
        for row in csv.reader(file, delimiter=',', quotechar='"'):
            yield row
