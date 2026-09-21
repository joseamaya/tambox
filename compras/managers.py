from django.core.exceptions import ObjectDoesNotExist
from django.db import models


class DetalleCotizacionManager(models.Manager):

    def bulk_create(self, objs, requirement, order):
        if requirement is not None:
            self.guardar_detalles_con_referencia(objs, requirement, order)
        else:
            self.guardar_detalles_sin_referencia(objs, order)

    def guardar_detalle_orden_servicio(self, order, detalle):
        from compras.models import DetalleOrdenServicios
        service_order_detail = DetalleOrdenServicios(order=order,
                                                        quotation_detail=detalle,
                                                        line_number=detalle.line_number,
                                                        quantity=detalle.quantity,
                                                        price=detalle.requirement_detail.product.price)
        return service_order_detail

    def guardar_detalles_con_referencia(self, objs, requirement, order):
        from compras.models import DetalleOrdenServicios
        detalles = []
        for detalle in objs:
            requirement_detail = detalle.requirement_detail
            requirement_detail.quoted_quantity = requirement_detail.quoted_quantity + detalle.quantity
            requirement_detail.establecer_estado_cotizado()
            requirement_detail.save()
            detalle.save()
            if order is not None:
                service_order_detail = self.guardar_detalle_orden_servicio(order, detalle)
                detalles.append(service_order_detail)
        requirement.establecer_estado_cotizado()
        requirement.save()
        if order is not None:
            DetalleOrdenServicios.objects.bulk_create(detalles, order.quotation)

    def guardar_detalles_sin_referencia(self, objs, order):
        for detalle in objs:
            detalle.save()
            if order is not None:
                self.guardar_detalle_orden_servicio(order, detalle)


class DetalleConformidadServicioManager(models.Manager):

    def bulk_create(self, objs, order):
        if order is not None:
            self.guardar_detalles_con_referencia(objs, order)
        else:
            self.guardar_detalles_sin_referencia(objs)

    def guardar_detalles_con_referencia(self, objs, order):
        try:
            requirement = order.quotation.requirement
        except ObjectDoesNotExist:
            requirement = None
        for detalle in objs:
            detalle_orden = detalle.service_order_detail
            detalle_orden.conformed_quantity = detalle_orden.conformed_quantity + detalle.quantity
            detalle_orden.establecer_estado_atendido()
            detalle_orden.save()
            try:
                requirement_detail = detalle_orden.quotation_detail.requirement_detail
            except ObjectDoesNotExist:
                requirement_detail = None
            if requirement_detail is not None:
                requirement_detail.served_quantity = requirement_detail.served_quantity + detalle_orden.conformed_quantity
                requirement_detail.establecer_estado_atendido()
                requirement_detail.save()
            detalle.save()
        if requirement is not None:
            requirement.establecer_estado_atendido()
            requirement.save()
        order.establecer_estado()
        order.save()

    def guardar_detalles_sin_referencia(self, objs):
        for detalle in objs:
            detalle.save()
