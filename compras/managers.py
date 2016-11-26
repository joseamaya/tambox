from django.db import models
from requerimientos.models import DetalleRequerimiento

class DetalleCotizacionManager(models.Manager):
    
    def bulk_create(self, objs, requerimiento):
        if requerimiento is not None:
            self.guardar_detalles_con_referencia(objs, requerimiento)
        else:
            self.guardar_detalles_sin_referencia(objs)
        
    def guardar_detalles_con_referencia(self, objs, requerimiento):
        for detalle in objs:
            detalle_requerimiento = self.detalle_requerimiento
            detalle_requerimiento.cantidad_cotizada = self.cantidad
            detalle_requerimiento.establecer_estado_cotizado()
            detalle_requerimiento.save()
            detalle.save()                        
        requerimiento.establecer_estado_cotizado()
        requerimiento.save()        
    
    def guardar_detalles_sin_referencia(self, objs):
        for detalle in objs:
            detalle.save()
            
class DetalleConformidadServicioManager(models.Manager):
    
    def bulk_create(self, objs, orden):
        requerimiento = orden.cotizacion.requerimiento
        for detalle in objs:
            detalle_orden = detalle.detalle_orden_servicios             
            detalle_orden.cantidad_conforme = detalle_orden.cantidad_conforme + detalle.cantidad
            detalle_orden.establecer_estado_atendido()
            detalle_orden.save()
            detalle_requerimiento = detalle_orden.detalle_cotizacion.detalle_requerimiento
            detalle_requerimiento.cantidad_atendida = detalle_requerimiento.cantidad_atendida + detalle_orden.cantidad_conforme
            detalle_requerimiento.establecer_estado_atendido()
            detalle_requerimiento.save()
            detalle.save()                        
        requerimiento.establecer_estado_atendido()
        orden.establecer_estado()