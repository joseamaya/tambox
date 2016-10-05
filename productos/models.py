# -*- coding: utf-8 -*- 
from django.db import models
from model_utils.models import TimeStampedModel
from contabilidad.models import CuentaContable
from django.db.models import Max
from django.utils.encoding import smart_str

class UnidadMedida(TimeStampedModel):
    codigo = models.CharField(max_length=5, unique=True)
    descripcion = models.CharField(max_length=50)
    estado = models.BooleanField(default=True)
    
    class Meta:
        permissions = (('ver_detalle_unidad_medida', 'Puede ver detalle Unidad de Medida'),
                       ('ver_tabla_unidades_medida', 'Puede ver tabla de unidades de medida'),
                       ('ver_reporte_unidades_medida_excel', 'Puede ver Reporte Unidades de Medida en excel'),)
        ordering = ['codigo']   
    
    def anterior(self):
        try:
            sig = UnidadMedida.objects.filter(pk__lt=self.pk).order_by('-pk')[0]
        except:
            sig = UnidadMedida.objects.all().last()            
        return sig.pk
    
    def siguiente(self):
        try:
            ant = UnidadMedida.objects.filter(pk__gt=self.pk).order_by('pk')[0]            
        except:
            ant = UnidadMedida.objects.all().first()            
        return ant.pk
    
    def __str__(self):
        return self.descripcion

class GrupoProductos(TimeStampedModel):
    codigo = models.CharField(primary_key=True,max_length=6)
    descripcion = models.CharField(max_length=100)
    ctacontable = models.ForeignKey(CuentaContable)
    son_productos = models.BooleanField(default=True)
    estado = models.BooleanField(default=True)
    
    class Meta:
        permissions = (('ver_detalle_grupo_productos', 'Puede ver detalle Grupo de Productos'),
                       ('ver_tabla_grupos_productos', 'Puede ver tabla Grupos de Productos'),
                       ('ver_reporte_grupo_productos_excel', 'Puede ver Reporte de grupo de productos en excel'),)

    def save(self, *args, **kwargs):
        if self.codigo == '':
            grupo_ant = GrupoProductos.objects.all().aggregate(Max('codigo'))
            cod_ant=grupo_ant['codigo__max']        
            if cod_ant is None:
                aux = 1            
            else:
                aux=int(cod_ant)+1
            self.codigo=str(aux).zfill(6) 
        super(GrupoProductos, self).save()
        
    def anterior(self):
        try:
            sig = GrupoProductos.objects.filter(pk__lt=self.pk).order_by('-pk')[0]
        except:
            sig = GrupoProductos.objects.all().last()            
        return sig.pk
    
    def siguiente(self):
        try:
            ant = GrupoProductos.objects.filter(pk__gt=self.pk).order_by('pk')[0]            
        except:
            ant = GrupoProductos.objects.all().first()            
        return ant.pk

    def __str__(self):
        return self.descripcion
    


class Producto(TimeStampedModel):
    codigo = models.CharField(primary_key=True, max_length=10)
    grupo_productos = models.ForeignKey(GrupoProductos)
    descripcion = models.CharField(max_length=100, unique=True)
    desc_abreviada = models.CharField(max_length=40, blank=True)
    es_servicio = models.BooleanField(default=False)
    unidad_medida = models.ForeignKey(UnidadMedida, null=True)
    marca = models.CharField(max_length=40,blank=True)
    modelo = models.CharField(max_length=40,blank=True)
    precio = models.DecimalField(max_digits=15, decimal_places=5, default=0)    
    stock = models.DecimalField(max_digits=15, decimal_places=5,default=0) 
    stock_minimo = models.DecimalField(max_digits=15, decimal_places=5,default=0)
    imagen = models.ImageField(upload_to='productos', default='productos/sinimagen.png')
    estado = models.BooleanField(default=True)    
    
    class Meta:
        permissions = (('ver_bienvenida', 'Puede ver bienvenida a la aplicación'),
                       ('cargar_productos', 'Puede cargar Productos desde un archivo externo'),
                       ('ver_detalle_producto', 'Puede ver detalle de Productos'),
                       ('ver_tabla_productos', 'Puede ver tabla Productos'),
                       ('ver_reporte_productos_excel', 'Puede ver Reporte de Productos en excel'),
                       ('puede_hacer_busqueda_producto', 'Puede hacer busqueda Producto'),)
    
    def anterior(self):
        try:
            sig = Producto.objects.filter(pk__lt=self.pk,es_servicio=self.es_servicio).order_by('-pk')[0]
        except:
            sig = Producto.objects.filter(es_servicio=self.es_servicio).last()            
        return sig.pk
    
    def siguiente(self):
        try:
            ant = Producto.objects.filter(pk__gt=self.pk,es_servicio=self.es_servicio).order_by('pk')[0]            
        except:
            ant = Producto.objects.filter(es_servicio=self.es_servicio).first()            
        return ant.pk
    
    def save(self, *args, **kwargs):
        if self.codigo == '':
            prod_ant = Producto.objects.filter(grupo_productos=self.grupo_productos).aggregate(Max('codigo'))
            cod_ant=prod_ant['codigo__max']        
            if cod_ant is None:
                self.codigo=self.grupo_productos.codigo+'0001'
            else:
                aux=int(cod_ant)+1
                self.codigo=str(aux).zfill(10)                
            if self.es_servicio:
                self.unidad_medida = UnidadMedida.objects.get(codigo='SERV')                
        super(Producto, self).save()

    def __str__(self):
        return smart_str(self.descripcion)