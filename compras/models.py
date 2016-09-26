# -*- coding: utf-8 -*- 
from django.db import models
from django.utils.encoding import smart_str
from model_utils import Choices
from django.utils.translation import gettext as _
from requerimientos.models import Requerimiento, DetalleRequerimiento
from model_utils.models import TimeStampedModel, StatusModel
from django.db.models import Max
from contabilidad.models import FormaPago
from productos.models import Producto

class DetalleOrdenCompraManager(models.Manager):
    
    def bulk_create(self, objs, cotizacion):
        if cotizacion is not None:
            self.guardar_detalles_con_referencia(objs, cotizacion)
        else:
            self.guardar_detalles_sin_referencia(objs)
        
    def guardar_detalles_con_referencia(self, objs, cotizacion):
        requerimiento = cotizacion.requerimiento
        for detalle in objs:
            detalle_cotizacion = detalle.detalle_cotizacion
            detalle_requerimiento = detalle_cotizacion.detalle_requerimiento 
            detalle_cotizacion.cantidad_comprada = detalle_cotizacion.cantidad_comprada + detalle.cantidad
            detalle_requerimiento.cantidad_comprada = detalle_requerimiento.cantidad_comprada + detalle_cotizacion.cantidad_comprada            
            detalle_cotizacion.establecer_estado()
            detalle_requerimiento.establecer_estado()
            if detalle_requerimiento.estado == DetalleRequerimiento.STATUS.PED:  
                DetalleCotizacion.objects.filter(detalle_requerimiento = detalle_requerimiento,
                                                 estado = DetalleCotizacion.STATUS.PEND).update(estado = DetalleCotizacion.STATUS.DESC)          
            detalle.save()                        
        requerimiento.establecer_estado()
        cotizacion.establecer_estado()
        cotizaciones = Cotizacion.objects.filter(estado = Cotizacion.STATUS.PEND)
        for cot in cotizaciones:
            cot.establecer_estado()
    
    def guardar_detalles_sin_referencia(self, objs):
        for detalle in objs:
            detalle.save()
        
class DetalleOrdenServiciosManager(models.Manager):
    
    def guardar_detalles_con_referencia(self, objs, cotizacion):
        requerimiento = cotizacion.requerimiento
        for detalle in objs:
            detalle_cotizacion = detalle.detalle_cotizacion
            detalle_requerimiento = detalle_cotizacion.detalle_requerimiento 
            detalle_cotizacion.cantidad_comprada = detalle_cotizacion.cantidad_comprada + detalle.cantidad
            detalle_requerimiento.cantidad_comprada = detalle_requerimiento.cantidad_comprada + detalle_cotizacion.cantidad_comprada            
            detalle_cotizacion.establecer_estado()
            detalle_requerimiento.establecer_estado()
            detalle_requerimiento.establecer_estado()
            if detalle_requerimiento.estado == DetalleRequerimiento.STATUS.PED:  
                DetalleCotizacion.objects.filter(detalle_requerimiento = detalle_requerimiento,
                                                 estado = DetalleCotizacion.STATUS.PEND).update(estado = DetalleCotizacion.STATUS.DESC)
            detalle.save()                        
        requerimiento.establecer_estado()
        cotizacion.establecer_estado()
        cotizaciones = Cotizacion.objects.filter(estado = Cotizacion.STATUS.PEND)
        for cot in cotizaciones:
            cot.establecer_estado()
        
    def guardar_detalles_sin_referencia(self, objs):
        for detalle in objs:
            detalle.save()
        
    def bulk_create(self, objs, referencia):
        if referencia is not None:
            self.guardar_detalles_con_referencia(objs, referencia)
        else:
            self.guardar_detalles_sin_referencia(objs)
            
class DetalleConformidadServicioManager(models.Manager):
    
    def bulk_create(self, objs, orden):
        requerimiento = orden.cotizacion.requerimiento
        for detalle in objs:
            detalle_orden = detalle.detalle_orden_servicios
            detalle_requerimiento = detalle_orden.detalle_cotizacion.detalle_requerimiento 
            detalle_orden.cantidad_conforme = detalle_orden.cantidad_conforme + detalle.cantidad
            detalle_requerimiento.cantidad_atendida = detalle_requerimiento.cantidad_atendida + detalle_orden.cantidad_conforme            
            detalle_orden.establecer_estado()
            detalle_requerimiento.establecer_estado_atendido()
            detalle.save()                        
        requerimiento.establecer_estado_atendido()
        orden.establecer_estado()        

class RepresentanteLegal(TimeStampedModel):
    documento = models.CharField(primary_key=True,max_length=11)
    nombre = models.CharField(max_length=150)
    cargo = models.CharField(max_length=50)
    
    class Meta:
        permissions = (('can_view', 'Can view Representante Legal'),
                       ('can_view_listado', 'Can view Listado Representante Legal'),
                       ('can_view_excel', 'Can view Representante Legal excel'),)
    
    def __str__(self):
        return self.nombre

class Proveedor(TimeStampedModel):
    ruc = models.CharField(unique=True,max_length=11)
    razon_social = models.CharField(max_length=150)
    direccion = models.CharField(max_length=200)
    telefono = models.CharField(max_length=15,null=True)
    correo = models.EmailField(null=True)
    estado_sunat = models.CharField(max_length=50)
    condicion = models.CharField(max_length=50)
    representantes = models.ManyToManyField(RepresentanteLegal)
    ciiu = models.CharField(max_length=250)
    fecha_alta = models.DateField()
    estado = models.BooleanField(default=True)
    
    class Meta:
        permissions = (('ver_detalle_proveedor', 'Puede ver detalle Proveedor'),
                       ('ver_tabla_proveedores', 'Puede ver tabla de Proveedores'),
                       ('ver_reporte_proveedores_excel', 'Puede ver Reporte Proveedores en excel'),)
        ordering = ['ruc']
    
    def anterior(self):
        try:
            sig = Proveedor.objects.filter(pk__lt=self.pk).order_by('-pk')[0]
        except:
            sig = Proveedor.objects.all().last()            
        return sig.pk
    
    def siguiente(self):
        try:
            ant = Proveedor.objects.filter(pk__gt=self.pk).order_by('pk')[0]            
        except:
            ant = Proveedor.objects.all().first()            
        return ant.pk
    
    def __str__(self):
        return smart_str(self.razon_social)
    
class Cotizacion(TimeStampedModel):
    codigo = models.CharField(primary_key=True, max_length=12)
    proveedor = models.ForeignKey(Proveedor)
    requerimiento = models.ForeignKey(Requerimiento, null=True)
    fecha = models.DateField()    
    observaciones = models.TextField(blank=True)
    STATUS = Choices(('PEND', _('PENDIENTE')),
                     ('ELEG', _('ELEGIDA')),
                     ('ELEG_PARC', _('ELEGIDA PARCIALMENTE')),
                     ('DESC', _('DESCARTADA')),
                     ('CANC', _('CANCELADO')),)
    estado = models.CharField(choices=STATUS, default=STATUS.PEND, max_length=20)
    
    def anterior(self):
        try:
            sig = Cotizacion.objects.filter(pk__lt=self.pk).order_by('-pk')[0]
        except:
            sig = Cotizacion.objects.all().last()            
        return sig.pk
    
    def siguiente(self):
        try:
            ant = Cotizacion.objects.filter(pk__gt=self.pk).order_by('pk')[0]            
        except:
            ant = Cotizacion.objects.all().first()            
        return ant.pk
    
    def eliminar_referencia(self):
        cotizacion = self
        DetalleCotizacion.objects.filter(cotizacion=cotizacion).delete()
        requerimiento = cotizacion.requerimiento        
        requerimiento.estado = Requerimiento.STATUS.PEND
        requerimiento.save()
        detalles = DetalleRequerimiento.objects.filter(requerimiento=requerimiento)
        for detalle in detalles:
            try:
                detalle.estado = DetalleRequerimiento.STATUS.PEND 
                detalle.save()
            except DetalleRequerimiento.DoesNotExist:
                pass
            
    def establecer_estado(self):
        cont_desc = 0
        cont_eleg = 0
        estado_cotizacion = Cotizacion.STATUS.PEND
        detalles_cotizacion = DetalleCotizacion.objects.filter(cotizacion = self)
        cont_det = detalles_cotizacion.count() 
        for detalle in detalles_cotizacion:
            if detalle.estado == DetalleCotizacion.STATUS.ELEG_PARC:
                estado_cotizacion = Cotizacion.STATUS.ELEG_PARC
                break
            elif detalle.estado == DetalleCotizacion.STATUS.DESC:
                cont_desc = cont_desc + 1
            elif detalle.estado == DetalleCotizacion.STATUS.ELEG:
                cont_eleg = cont_eleg + 1
        if cont_desc == cont_det:
            estado_cotizacion = Cotizacion.STATUS.DESC
        if cont_eleg == cont_det:
            estado_cotizacion = Cotizacion.STATUS.ELEG
        elif cont_eleg > 0:
            estado_cotizacion = Cotizacion.STATUS.ELEG_PARC
        self.estado = estado_cotizacion            
        self.save()
                    
    class Meta:
        unique_together = (('proveedor', 'requerimiento'),)
        permissions = (('ver_detalle_cotizacion', 'Puede ver detalle de Cotización'),
                       ('ver_tabla_cotizaciones', 'Puede ver tabla Cotizaciones'),
                       ('ver_reporte_cotizaciones_excel', 'Puede ver Reporte de Cotizaciones en excel'),
                       ('puede_hacer_transferencia_cotizacion', 'Puede hacer transferencia de Cotización'),)
    
    def save(self, *args, **kwargs):        
        if self.codigo == '':
            anio = self.fecha.year
            mov_ant = Cotizacion.objects.filter(fecha__year=anio).aggregate(Max('codigo'))
            id_ant=mov_ant['codigo__max']
            if id_ant is None:        
                aux = 1            
            else:            
                aux=int(id_ant[-6:])+1            
            correlativo = str(aux).zfill(6)
            self.codigo = 'CO'+str(anio)+correlativo
            self.requerimiento.estado = Requerimiento.STATUS.COTIZ
            self.requerimiento.save()
            DetalleRequerimiento.objects.filter(estado=self.STATUS.PEND,
                                                requerimiento=self.requerimiento).update(estado = DetalleRequerimiento.STATUS.COTIZ)
        super(Cotizacion, self).save()        
    
    def __str__(self):
        return self.codigo
    
class DetalleCotizacion(TimeStampedModel, StatusModel):
    nro_detalle = models.IntegerField()
    cotizacion = models.ForeignKey(Cotizacion)
    detalle_requerimiento = models.ForeignKey(DetalleRequerimiento, null=True)
    cantidad = models.DecimalField(max_digits=15, decimal_places=5)
    cantidad_comprada = models.DecimalField(max_digits=15, decimal_places=5,default=0)
    STATUS = Choices(('PEND', _('PENDIENTE')),
                     ('ELEG', _('ELEGIDA')),
                     ('ELEG_PARC', _('ELEGIDA PARCIALMENTE')),
                     ('DESC', _('DESCARTADA')),
                     ('CANC', _('CANCELADO')),)
    estado = models.CharField(choices=STATUS, default=STATUS.PEND, max_length=20)
    
    def establecer_estado(self):
        if self.cantidad_comprada < self.cantidad: 
            self.estado = DetalleCotizacion.STATUS.ELEG_PARC                
        elif self.cantidad_comprada >= self.cantidad:
            self.estado = DetalleCotizacion.STATUS.ELEG                
        self.save()
    
    class Meta:
        permissions = (('can_view', 'Can view Detalle Orden de Compra'),)
    
class OrdenCompra(TimeStampedModel):
    codigo = models.CharField(primary_key=True, max_length=12)
    cotizacion = models.ForeignKey(Cotizacion, null=True)
    proveedor = models.ForeignKey(Proveedor, null=True)
    proceso = models.CharField(max_length=50, default='')
    fecha = models.DateField()    
    forma_pago = models.ForeignKey(FormaPago)
    subtotal = models.DecimalField(max_digits=15, decimal_places=5)
    igv = models.DecimalField(max_digits=15, decimal_places=5)    
    total = models.DecimalField(max_digits=15, decimal_places=5)
    total_letras = models.CharField(max_length=150)
    observaciones = models.TextField(default='')
    STATUS = Choices(('PEND', _('PENDIENTE')),
                     ('ING', _('INGRESADA')),
                     ('ING_PARC', _('INGRESADA PARCIALMENTE')),
                     ('CANC', _('CANCELADA')),
                     )
    estado = models.CharField(choices=STATUS, default=STATUS.PEND, max_length=20)
    
    def anterior(self):
        try:
            sig = OrdenCompra.objects.filter(pk__lt=self.pk).order_by('-pk')[0]
        except:
            sig = OrdenCompra.objects.all().last()            
        return sig.pk
    
    def siguiente(self):
        try:
            ant = OrdenCompra.objects.filter(pk__gt=self.pk).order_by('pk')[0]            
        except:
            ant = OrdenCompra.objects.all().first()            
        return ant.pk
    
    def eliminar_referencia(self):
        referencia = self.cotizacion        
        referencia.estado = Cotizacion.STATUS.PEND
        referencia.save()
        detalles = DetalleOrdenCompra.objects.filter(orden=self)
        for detalle in detalles:
            try:
                detalle_requerimiento = detalle.detalle_cotizacion.detalle_requerimiento
                detalle_requerimiento.estado = DetalleCotizacion.STATUS.PEND 
                detalle_requerimiento.save()
            except DetalleRequerimiento.DoesNotExist:
                pass
        DetalleOrdenCompra.objects.filter(orden = self).delete()
        
    def establecer_estado(self):
        estado_orden = OrdenCompra.STATUS.ING
        detalles_orden = DetalleOrdenCompra.objects.filter(orden = self)
        for detalle in detalles_orden:
            if detalle.estado == DetalleOrdenCompra.STATUS.ING_PARC or detalle.estado == DetalleOrdenCompra.STATUS.PEND:
                estado_orden = OrdenCompra.STATUS.ING_PARC
                break            
        self.estado = estado_orden            
        self.save()
    
    class Meta:
        permissions = (('ver_detalle_orden_compra', 'Puede ver detalle de Orden de Compra'),
                       ('ver_tabla_ordenes_compra', 'Puede ver tabla Ordenes de Compra'),
                       ('ver_reporte_ordenes_compra_excel', 'Puede ver Reporte de Ordenes de Compra en excel'),
                       ('puede_hacer_transferencia_orden_compra', 'Puede hacer transferencia de Orden de Compra'),)
    
    def save(self, *args, **kwargs):
        if self.codigo == '':
            anio = self.fecha.year
            mov_ant = OrdenCompra.objects.filter(fecha__year=anio).aggregate(Max('codigo'))
            id_ant=mov_ant['codigo__max']
            if id_ant is None:        
                aux = 1            
            else:            
                aux=int(id_ant[-6:])+1            
            correlativo = str(aux).zfill(6)
            self.codigo = 'OC'+str(anio)+correlativo
        super(OrdenCompra, self).save()
    
    def __str__(self):
        return self.codigo
    
class DetalleOrdenCompra(TimeStampedModel):
    objects = DetalleOrdenCompraManager()
    nro_detalle = models.IntegerField()
    orden = models.ForeignKey(OrdenCompra)
    detalle_cotizacion = models.ForeignKey(DetalleCotizacion, null=True)
    producto = models.ForeignKey(Producto, null=True)
    cantidad = models.DecimalField(max_digits=15, decimal_places=5)
    cantidad_ingresada = models.DecimalField(max_digits=15, decimal_places=5,default=0)
    precio = models.DecimalField(max_digits=15, decimal_places=5)
    valor = models.DecimalField(max_digits=15, decimal_places=5, blank=True, null=True)
    impuesto = models.DecimalField(max_digits=15, decimal_places=5, blank=True, null=True)
    STATUS = Choices(('PEND', _('PENDIENTE')),
                     ('ING', _('INGRESADO')),
                     ('ING_PARC', _('INGRESADO PARCIALMENTE')),
                     ('CANC', _('CANCELADO')),
                     )
    estado = models.CharField(choices=STATUS, default=STATUS.PEND, max_length=20)
    
    def establecer_estado(self):
        if self.cantidad_ingresada < self.cantidad: 
            self.estado = DetalleOrdenCompra.STATUS.ING_PARC                
        elif self.cantidad_ingresada >= self.cantidad:
            self.estado = DetalleOrdenCompra.STATUS.ING                
        self.save()
    
    class Meta:
        permissions = (('can_view', 'Can view Detalle Orden de Compra'),)
        
class OrdenServicios(TimeStampedModel):
    codigo = models.CharField(primary_key=True, max_length=12)
    forma_pago = models.ForeignKey(FormaPago)
    proceso = models.CharField(max_length=50, default='')
    cotizacion = models.ForeignKey(Cotizacion, null=True)
    subtotal = models.DecimalField(max_digits=15, decimal_places=5)
    igv = models.DecimalField(max_digits=15, decimal_places=5, default=0)
    total = models.DecimalField(max_digits=15, decimal_places=5)
    total_letras = models.CharField(max_length=150)
    fecha = models.DateField()
    observaciones = models.TextField(default='')
    STATUS = Choices(('PEND', _('PENDIENTE')),
                     ('CONF', _('CONFORME')),
                     ('CONF_PARC', _('CONFORME PARCIALMENTE')),
                     ('CANC', _('CANCELADA')),
                     )
    estado = models.CharField(choices=STATUS, default=STATUS.PEND, max_length=20)
        
    def anterior(self):
        try:
            sig = OrdenServicios.objects.filter(pk__lt=self.pk).order_by('-pk')[0]
        except:
            sig = OrdenServicios.objects.all().last()            
        return sig.pk
    
    def siguiente(self):
        try:
            ant = OrdenServicios.objects.filter(pk__gt=self.pk).order_by('pk')[0]            
        except:
            ant = OrdenServicios.objects.all().first()            
        return ant.pk
    
    def eliminar_referencia(self):
        referencia = self.cotizacion        
        referencia.estado = Cotizacion.STATUS.PEND
        referencia.save()
        detalles = DetalleOrdenServicios.objects.filter(orden=self)
        for detalle in detalles:
            try:
                detalle_requerimiento = detalle.detalle_cotizacion.detalle_requerimiento
                detalle_requerimiento.estado = DetalleCotizacion.STATUS.PEND 
                detalle_requerimiento.save()
            except DetalleRequerimiento.DoesNotExist:
                pass
        DetalleOrdenServicios.objects.filter(orden = self).delete()
        
    def establecer_estado(self):
        estado_orden = OrdenServicios.STATUS.CONF
        detalles_orden = DetalleOrdenServicios.objects.filter(orden = self)
        for detalle in detalles_orden:
            if detalle.estado == DetalleOrdenServicios.STATUS.CONF_PARC or detalle.estado == DetalleOrdenServicios.STATUS.PEND:
                estado_orden = OrdenServicios.STATUS.CONF_PARC
                break            
        self.estado = estado_orden            
        self.save()
    
    class Meta:
        permissions = (('ver_detalle_orden_servicios', 'Puede ver detalle de Orden de Servicios'),
                       ('ver_tabla_ordenes_servicios', 'Puede ver tabla de Ordenes de Servicios'),
                       ('ver_reporte_ordenes_servicios_excel', 'Puede ver Reporte de Ordenes de Servicios en excel'),)
    
    def save(self, *args, **kwargs):        
        if self.codigo == '':
            anio = self.fecha.year
            mov_ant = OrdenServicios.objects.filter(fecha__year=anio).aggregate(Max('codigo'))
            id_ant=mov_ant['codigo__max']
            if id_ant is None:        
                aux = 1            
            else:            
                aux=int(id_ant[-6:])+1            
            correlativo = str(aux).zfill(6)
            self.codigo = 'OS'+str(anio)+correlativo            
        super(OrdenServicios, self).save()
    
    def __str__(self):
        return self.codigo
    
class DetalleOrdenServicios(TimeStampedModel):
    objects = DetalleOrdenCompraManager()
    nro_detalle = models.IntegerField()
    orden = models.ForeignKey(OrdenServicios)
    detalle_cotizacion = models.ForeignKey(DetalleCotizacion, null=True)
    cantidad = models.DecimalField(max_digits=15, decimal_places=5)
    cantidad_conforme = models.DecimalField(max_digits=15, decimal_places=5,default=0)
    precio = models.DecimalField(max_digits=15, decimal_places=5)
    valor = models.DecimalField(max_digits=15, decimal_places=5, blank=True, null=True)
    impuesto = models.DecimalField(max_digits=15, decimal_places=5,default=0)
    STATUS = Choices(('PEND', _('PENDIENTE')),
                     ('CONF', _('CONFORME')),
                     ('CONF_PARC', _('CONFORME PARCIALMENTE')),
                     ('CANC', _('CANCELADA')),
                     )
    estado = models.CharField(choices=STATUS, default=STATUS.PEND, max_length=20)
    
    class Meta:
        permissions = (('ver_detalle_orden_servicios', 'Puede ver Detalle Orden de Servicios'),)
        ordering = ['nro_detalle']

    def establecer_estado(self):
        if self.cantidad_conforme < self.cantidad: 
            self.estado = DetalleOrdenServicios.STATUS.CONF_PARC                
        elif self.cantidad_conforme >= self.cantidad:
            self.estado = DetalleOrdenServicios.STATUS.CONF                
        self.save()
        
class ConformidadServicio(TimeStampedModel):
    codigo = models.CharField(primary_key=True, max_length=12)
    orden_servicios = models.ForeignKey(OrdenServicios)
    doc_sustento = models.CharField(max_length=12)
    fecha = models.DateField()
    total = models.DecimalField(max_digits=15, decimal_places=5)
    total_letras = models.CharField(max_length=150)
    estado = models.BooleanField(default=True)
    
    class Meta:
        permissions = (('ver_detalle_conformidad_servicio', 'Puede ver detalle de Conformidad de Servicio'),
                       ('ver_tabla_conformidades_servicio', 'Puede ver tabla de Conformidades de Servicio'),
                       ('ver_reporte_conformidades_servicio_excel', 'Puede ver Reporte de Conformidades de Servicio en excel'),)
    
    def anterior(self):
        try:
            sig = ConformidadServicio.objects.filter(pk__lt=self.pk).order_by('-pk')[0]
        except:
            sig = ConformidadServicio.objects.all().last()            
        return sig.pk
    
    def siguiente(self):
        try:
            ant = ConformidadServicio.objects.filter(pk__gt=self.pk).order_by('pk')[0]            
        except:
            ant = ConformidadServicio.objects.all().first()            
        return ant.pk
    
    def eliminar_referencia(self, orden_compra):        
        referencia = orden_compra.cotizacion        
        referencia.abierta = True
        referencia.save()
        detalles = DetalleOrdenCompra.objects.filter(orden=orden_compra)
        for detalle in detalles:
            try:
                detalle_requerimiento = detalle.detalle_requerimiento
                detalle_requerimiento.cantidad_atendida = detalle_requerimiento.cantidad_atendida - detalle.cantidad
                detalle_requerimiento.abierta = True 
                detalle_requerimiento.save()
            except DetalleRequerimiento.DoesNotExist:
                pass
    
    def save(self, *args, **kwargs):
        if self.codigo == '':
            anio = self.fecha.year
            mov_ant = OrdenServicios.objects.filter(fecha__year=anio).aggregate(Max('codigo'))
            id_ant=mov_ant['codigo__max']
            if id_ant is None:        
                aux = 1            
            else:            
                aux=int(id_ant[-6:])+1            
            correlativo = str(aux).zfill(6)
            self.codigo = 'CS'+str(anio)+correlativo
        super(ConformidadServicio, self).save()
        
    def __str__(self):
        return self.codigo
    
class DetalleConformidadServicio(TimeStampedModel):
    objects = DetalleConformidadServicioManager()
    nro_detalle = models.IntegerField()
    conformidad = models.ForeignKey(ConformidadServicio)
    detalle_orden_servicios = models.ForeignKey(DetalleOrdenServicios, null=True)
    cantidad = models.DecimalField(max_digits=15, decimal_places=5,default=0)