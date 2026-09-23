"""Formatos del proyecto para es-PE.

Los inputs de fecha y hora son nativos (`type=date`/`type=time`), asi que el
formato ISO va primero: es el que el navegador envia y muestra. Los formatos
dd/mm/yyyy siguen aceptandose al escribir a mano.
"""

DATE_INPUT_FORMATS = [
    '%Y-%m-%d',
    '%d/%m/%Y',
    '%d/%m/%y',
]

DATETIME_INPUT_FORMATS = [
    '%Y-%m-%d',
    '%Y-%m-%d %H:%M:%S',
    '%Y-%m-%d %H:%M',
    '%d/%m/%Y',
    '%d/%m/%Y %H:%M:%S',
    '%d/%m/%Y %H:%M',
    '%d/%m/%y',
    '%d/%m/%y %H:%M:%S',
    '%d/%m/%y %H:%M',
]
