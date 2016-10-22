# -*- coding: utf-8 -*- 
from django.contrib import admin
from contabilidad.models import Empresa, TipoExistencia

# Register your models here.
admin.site.register(Empresa)
admin.site.register(TipoExistencia)