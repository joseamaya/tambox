# -*- coding: utf-8 -*- 
from django.db import models


class DetalleMovimientoManager(models.Manager):

    def guardar_detalles_con_referencia(self, objs, order):
        requirement = None
        if order.quotation is not None:
            requirement = order.quotation.requirement
        for detalle in objs:
            detalle_orden = detalle.purchase_order_detail
            if detalle_orden.quotation_detail is not None:
                requirement_detail = detalle_orden.quotation_detail.requirement_detail
                requirement_detail.served_quantity = requirement_detail.served_quantity + detalle.quantity
                requirement_detail.establecer_estado_atendido()
                requirement_detail.save()
            detalle_orden.received_quantity = detalle_orden.received_quantity + detalle.quantity
            detalle_orden.establecer_estado()
            detalle_orden.save()
            detalle.save()
        if requirement is not None:
            requirement.establecer_estado_atendido()
            requirement.save()
        order.establecer_estado()
        order.save()

    def guardar_detalle_con_pedido(self, objs, order):
        for detalle in objs:
            order_detail = detalle.order_detail
            order_detail.served_quantity = order_detail.served_quantity + detalle.quantity
            order_detail.establecer_estado_atendido()
            order_detail.save()
            detalle.save()
        order.establecer_estado_atendido()
        order.save()

    def guardar_detalles_sin_referencia(self, objs):
        cont = 1
        for detalle in objs:
            detalle.save()
            cont = cont + 1

    def bulk_create(self, objs, reference, order):
        if reference is not None:
            self.guardar_detalles_con_referencia(objs, reference)
        elif order is not None:
            self.guardar_detalle_con_pedido(objs, order)
        else:
            self.guardar_detalles_sin_referencia(objs)
