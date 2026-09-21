from django.core.management.base import BaseCommand

from almacen.models import Kardex, Movimiento


class Command(BaseCommand):
    help = "Elimina los kardex de los movimientos cancelados"

    def handle(self, *args, **options):
        movimientos = Kardex.objects.filter(movimiento__status=Movimiento.STATUS.CANC)
        for movimiento in movimientos:
            self.stdout.write("Eliminando kardex: " + movimiento.movimiento.movement_id)
            movimiento.delete()
        self.stdout.write("Se han eliminado los kardex con problemas")
