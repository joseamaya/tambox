from django.core.management.base import BaseCommand

from almacen.models import Kardex, Movimiento


class Command(BaseCommand):
    help = "Elimina los kardex de los movimientos cancelados"
 
    def handle(self, *args, **options):
        movimientos = Kardex.objects.filter(movimiento__estado=Movimiento.STATUS.CANC)
        for movimiento in movimientos:
            print "Eliminando kardex: " + movimiento.movimiento.id_movimiento
            movimiento.delete()
        print "Se han eliminado los kardex con problemas"