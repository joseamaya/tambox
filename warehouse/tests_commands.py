"""El comando que limpia los kardex de movimientos cancelados."""
from django.core.management import call_command
from django.test import TestCase
from model_bakery import baker

from warehouse.models import Kardex, Movement


class DeleteCancelledKardexCommandTest(TestCase):

    def test_deletes_only_cancelled_kardex(self):
        cancelled = baker.make(Movement, status=Movement.STATUS.CANC)
        cancelled_kardex = baker.make(Kardex, movement=cancelled)
        active = baker.make(Movement, status=Movement.STATUS.ACT)
        active_kardex = baker.make(Kardex, movement=active)

        call_command('delete_cancelled_kardex')

        self.assertFalse(Kardex.objects.filter(pk=cancelled_kardex.pk).exists())
        self.assertTrue(Kardex.objects.filter(pk=active_kardex.pk).exists())
