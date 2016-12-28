# -*- coding:utf-8 -*-
from rest_framework import serializers
from administracion.models import Oficina

class AdministracionOficinaSerializer(serializers.ModelSerializer):
    class Meta:
        model=Oficina
        fields = '__all__'
