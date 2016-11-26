# -*- coding: utf-8 -*-
from almacen.models import TipoMovimiento, Almacen, Kardex
PARAMETROS = (('F', 'POR FECHA',), ('M', 'POR MES',), ('A', 'POR AÑO',))

MESES = (
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

FORMATOS = (('S', 'UNIDADES FISICAS',), ('V', 'VALORIZADO',))

CHOICES_TIPOS_MOVIMIENTO = [(tm.codigo, tm.descripcion) for tm in TipoMovimiento.objects.all()]
CHOICES_ALMACENES = [(alm.codigo, alm.descripcion) for alm in Almacen.objects.all()]
CHOICES_MESES = [(str(mes.month).zfill(2), str(mes.month).zfill(2)) for mes in Kardex.objects.datetimes('fecha_operacion', 'month')]
CHOICES_ANNIOS = [(anio.year, anio.year) for anio in Kardex.objects.datetimes('fecha_operacion', 'year')]