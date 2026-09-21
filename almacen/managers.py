# -*- coding: utf-8 -*- 
from django.db import models


class MovementDetailManager(models.Manager):

    def save_details_with_reference(self, objs, order):
        requirement = None
        if order.quotation is not None:
            requirement = order.quotation.requirement
        for detail in objs:
            detalle_orden = detail.purchase_order_detail
            if detalle_orden.quotation_detail is not None:
                requirement_detail = detalle_orden.quotation_detail.requirement_detail
                requirement_detail.served_quantity = requirement_detail.served_quantity + detail.quantity
                requirement_detail.set_status_served()
                requirement_detail.save()
            detalle_orden.received_quantity = detalle_orden.received_quantity + detail.quantity
            detalle_orden.set_status()
            detalle_orden.save()
            detail.save()
        if requirement is not None:
            requirement.set_status_served()
            requirement.save()
        order.set_status()
        order.save()

    def save_detail_with_order(self, objs, order):
        for detail in objs:
            order_detail = detail.order_detail
            order_detail.served_quantity = order_detail.served_quantity + detail.quantity
            order_detail.set_status_served()
            order_detail.save()
            detail.save()
        order.set_status_served()
        order.save()

    def save_details_without_reference(self, objs):
        cont = 1
        for detail in objs:
            detail.save()
            cont = cont + 1

    def bulk_create(self, objs, reference, order):
        if reference is not None:
            self.save_details_with_reference(objs, reference)
        elif order is not None:
            self.save_detail_with_order(objs, order)
        else:
            self.save_details_without_reference(objs)
