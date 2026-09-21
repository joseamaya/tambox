from django.core.management.base import BaseCommand

from almacen.models import Kardex, Movement


class Command(BaseCommand):
    help = "Elimina los kardex de los movimientos cancelados"

    def handle(self, *args, **options):
        movimientos = Kardex.objects.filter(movement__status=Movement.STATUS.CANC)
        for movement in movimientos:
            self.stdout.write("Eliminando kardex: " + movement.movement.movement_id)
            movement.delete()
        self.stdout.write("Se han eliminado los kardex con problemas")
