from django.db import models


class DetalleCotizacionManager(models.Manager):

    def bulk_create(self, objs, requerimiento, orden):
        if requerimiento is not None:
            self.guardar_detalles_con_referencia(objs, requerimiento, orden)
        else:
            self.guardar_detalles_sin_referencia(objs, orden)

    def guardar_detalle_orden_servicio(self, orden, detalle):
        from compras.models import DetalleOrdenServicios
        detalle_orden_servicios = DetalleOrdenServicios(orden=orden,
                                                        detalle_cotizacion=detalle,
                                                        nro_detalle=detalle.nro_detalle,
                                                        cantidad=detalle.cantidad,
                                                        precio=detalle.detalle_requerimiento.producto.precio)
        return detalle_orden_servicios

    def guardar_detalles_con_referencia(self, objs, requerimiento, orden):
        from compras.models import DetalleOrdenServicios
        detalles = []
        for detalle in objs:
            detalle_requerimiento = detalle.detalle_requerimiento
            detalle_requerimiento.cantidad_cotizada = detalle_requerimiento.cantidad_cotizada + detalle.cantidad
            detalle_requerimiento.establecer_estado_cotizado()
            detalle_requerimiento.save()
            detalle.save()
            if orden is not None:
                detalle_orden_servicios = self.guardar_detalle_orden_servicio(orden, detalle)
                detalles.append(detalle_orden_servicios)
        requerimiento.establecer_estado_cotizado()
        requerimiento.save()
        if orden is not None:
            DetalleOrdenServicios.objects.bulk_create(detalles, orden.cotizacion)

    def guardar_detalles_sin_referencia(self, objs, orden):
        for detalle in objs:
            detalle.save()
            if orden is not None:
                self.guardar_detalle_orden_servicio(orden, detalle)


class DetalleConformidadServicioManager(models.Manager):

    def bulk_create(self, objs, orden):
        if orden is not None:
            self.guardar_detalles_con_referencia(objs, orden)
        else:
            self.guardar_detalles_sin_referencia(objs)

    def guardar_detalles_con_referencia(self, objs, orden):
        try:
            requerimiento = orden.cotizacion.requerimiento
        except:
            requerimiento = None
        for detalle in objs:
            detalle_orden = detalle.detalle_orden_servicios
            detalle_orden.cantidad_conforme = detalle_orden.cantidad_conforme + detalle.cantidad
            detalle_orden.establecer_estado_atendido()
            detalle_orden.save()
            try:
                detalle_requerimiento = detalle_orden.detalle_cotizacion.detalle_requerimiento
            except:
                detalle_requerimiento = None
            if detalle_requerimiento is not None:
                detalle_requerimiento.cantidad_atendida = detalle_requerimiento.cantidad_atendida + detalle_orden.cantidad_conforme
                detalle_requerimiento.establecer_estado_atendido()
                detalle_requerimiento.save()
            detalle.save()
        if requerimiento is not None:
            requerimiento.establecer_estado_atendido()
            requerimiento.save()
        orden.establecer_estado()
        orden.save()

    def guardar_detalles_sin_referencia(self, objs):
        for detalle in objs:
            detalle.save()
