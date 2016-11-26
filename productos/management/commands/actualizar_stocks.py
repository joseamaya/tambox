from django.core.management.base import BaseCommand
from almacen.models import ControlProductoAlmacen
from productos.models import Producto
from django.db.models import Sum

class Command(BaseCommand):
    help = "Actualiza los stocks de todos los productos"
 
    def handle(self, *args, **options):
        productos = Producto.objects.all()
        for producto in productos:
            print "Actualizando producto: " +producto.descripcion
            lista_productos_control = ControlProductoAlmacen.objects.filter(producto = producto).aggregate(stock=Sum('stock'))
            stock = lista_productos_control['stock']
            if stock is not None:
                producto.stock = stock    
                producto.save()
        print "Se han actualizado los stocks de los productos"