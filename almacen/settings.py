# -*- coding: utf-8 -*-
"""Constantes de almacen que no dependen de la base de datos.

Los valores que salen de la base de datos viven en tambox.config (con
cache) o son funciones de este modulo cuando deben leerse frescos, que es el
caso de las opciones de los formularios: se calculan al construir el formulario
y no al importar el modulo.
"""

from almacen.models import MovementType, Warehouse

PARAMETROS = (('F', 'POR FECHA',), ('M', 'POR MES',), ('A', 'POR AÑO',))

MONTHS = (
    ('01', 'ENERO'),
    ('02', 'FEBRERO'),
    ('03', 'MARZO'),
    ('04', 'ABRIL'),
    ('05', 'MAYO'),
    ('06', 'JUNIO'),
    ('07', 'JULIO'),
    ('08', 'AGOSTO'),
    ('09', 'SETIEMBRE'),
    ('10', 'OCTUBRE'),
    ('11', 'NOVIEMBRE'),
    ('12', 'DICIEMBRE'),
)

FORMATOS_SUNAT = (('S', 'ONES FISICAS',), ('V', 'VALORIZADO',))
FORMATOS = (('XLS', 'EXCEL',), ('PDF', 'PDF',))
SELECCION = (('T', 'TODOS LOS PRODUCTOS',), ('P', 'UN SOLO PRODUCTO',))
CHOICES_CONSOLIDADO = (('P', 'PRODUCTOS',), ('G', 'GRUPOS',))


def movement_type_choices():
    return [(tm.code, tm.description) for tm in MovementType.objects.all()]


def warehouse_choices():
    return [(alm.code, alm.description) for alm in Warehouse.objects.all()]
