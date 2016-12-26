# -*- coding: utf-8 -*-
from django.db import models


class DetalleMovimientoManager(models.Manager):
    def guardar_detalles_con_referencia(self, objs, orden):
        try:
            requerimiento = orden.cotizacion.requerimiento
        except:
            requerimiento = None
        for detalle in objs:
            detalle_orden = detalle.detalle_orden_compra
            try:
                detalle_requerimiento = detalle_orden.detalle_cotizacion.detalle_requerimiento
            except:
                detalle_requerimiento = None
            detalle_orden.cantidad_ingresada = detalle_orden.cantidad_ingresada + detalle.cantidad
            if detalle_requerimiento is not None:
                detalle_requerimiento.cantidad_atendida = detalle_requerimiento.cantidad_atendida + detalle_orden.cantidad_ingresada
            detalle_orden.establecer_estado()
            if detalle_requerimiento is not None:
                detalle_requerimiento.establecer_estado_atendido()
            detalle.save()
        if requerimiento is not None:
            requerimiento.establecer_estado_atendido()
        orden.establecer_estado()

    def guardar_detalle_con_pedido(self, objs, pedido):
        for detalle in objs:
            detalle_pedido = detalle.detalle_pedido
            detalle_pedido.cantidad_atendida = detalle_pedido.cantidad_atendida + detalle.cantidad
            detalle_pedido.establecer_estado_atendido()
            detalle_pedido.save()
            detalle.save()
        pedido.establecer_estado_atendido()
        pedido.save()

    def guardar_detalles_sin_referencia(self, objs):
        cont = 1
        for detalle in objs:
            detalle.save()
            cont = cont + 1

    def bulk_create(self, objs, referencia, pedido):
        if referencia is not None:
            self.guardar_detalles_con_referencia(objs, referencia)
        if pedido is not None:
            self.guardar_detalle_con_pedido(objs, pedido)