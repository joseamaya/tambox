"""Tests de los helpers de `tambox`.

Son funciones puras o casi puras, de las que dependen los reportes y los
importadores; hasta ahora no tenian ninguna prueba y `to_word` llegaba a
levantar una excepcion en la rama de moneda.
"""
import datetime
import os
import tempfile
from unittest import mock

from django.core import mail
from django.test import TestCase, override_settings
from django.utils import timezone
from model_bakery import baker

from tambox.config import administration_office, clear_cache, company, configuration
from tambox.dates import aware
from tambox.imports import read_rows
from tambox.mail import send_mail
from tambox.statuses import COMPLETE, EMPTY, PARTIAL, classify
from tambox.util import hundreds_word, to_word
from warehouse.models import Warehouse


class ToWordTest(TestCase):

    def test_zero(self):
        self.assertEqual(' y 00/100 nuevos soles', to_word(0))

    def test_units(self):
        self.assertEqual('Un y 00/100 nuevos soles', to_word(1))
        self.assertEqual('Cinco y 00/100 nuevos soles', to_word(5))

    def test_tens_and_hundreds(self):
        self.assertEqual('Ventiun y 00/100 nuevos soles', to_word(21))
        self.assertEqual('Treinta Y Un y 00/100 nuevos soles', to_word(31))
        self.assertEqual('Ciento Ventitres y 00/100 nuevos soles', to_word(123))

    def test_thousands_and_millions(self):
        self.assertEqual('Mil y 00/100 nuevos soles', to_word(1000))
        self.assertEqual('Mil Cuatrocientos Ochenta Y Un y 00/100 nuevos soles', to_word(1481))
        self.assertEqual('Millon y 00/100 nuevos soles', to_word(1000000))
        self.assertEqual('Dos Millones y 00/100 nuevos soles', to_word(2000000))

    def test_big_number(self):
        self.assertEqual(
            'Cincuenta Y Tres Mil Seiscientos Venticinco Millones Novecientos '
            'Noventa Y Nueve Mil Quinientos Sesenta Y Siete y 00/100 nuevos soles',
            to_word(53625999567))

    def test_currency_singular_and_plural(self):
        # La frase entera pasa por `.title()`, por eso el singular y el plural
        # salen capitalizados palabra a palabra.
        self.assertIn('Euro', to_word(1, 'EUR'))
        self.assertIn('Euros', to_word(2, 'EUR'))

    def test_currency_without_decimals(self):
        """Las monedas sin `decimalsingular` no pueden reventar con KeyError."""
        self.assertIn('Dólares', to_word(5, 'USD'))

    def test_invalid_currency(self):
        self.assertEqual('Tipo de moneda inválida', to_word(5, 'XXX'))

    def test_hundreds_word_limits(self):
        self.assertEqual('No es posible convertir el numero a letras', hundreds_word(0))
        self.assertEqual('No es posible convertir el numero a letras', hundreds_word(1000))

    def test_hundreds_word_values(self):
        self.assertEqual('Cien', hundreds_word(100))
        self.assertEqual('Un', hundreds_word(1))
        self.assertEqual('Ciento Ventitres', hundreds_word(123))


class DatesTest(TestCase):

    def test_date_becomes_aware_datetime(self):
        result = aware(datetime.date(2026, 3, 15))
        self.assertTrue(timezone.is_aware(result))
        self.assertEqual((2026, 3, 15, 0, 0), (result.year, result.month, result.day,
                                                result.hour, result.minute))

    def test_naive_datetime_becomes_aware(self):
        naive = datetime.datetime(2026, 3, 15, 10, 30)
        result = aware(naive)
        self.assertTrue(timezone.is_aware(result))
        self.assertEqual(10, result.hour)

    def test_aware_datetime_is_left_alone(self):
        original = timezone.make_aware(datetime.datetime(2026, 3, 15, 10, 30))
        self.assertIs(original, aware(original))


class ReadRowsTest(TestCase):

    def test_reads_quoted_csv(self):
        with tempfile.TemporaryDirectory() as media:
            with override_settings(MEDIA_ROOT=media):
                folder = os.path.join(media, 'archivos')
                os.makedirs(folder)
                with open(os.path.join(folder, 'datos.csv'), 'w', encoding='utf8') as file:
                    file.write('codigo,descripcion\n001,"UNO, DOS"\n')

                rows = list(read_rows('datos.csv'))

        self.assertEqual([['codigo', 'descripcion'], ['001', 'UNO, DOS']], rows)


class SendMailTest(TestCase):

    def test_sends_the_message(self):
        send_mail(['destino@example.com'], 'Asunto', 'Cuerpo')

        self.assertEqual(1, len(mail.outbox))
        self.assertEqual('Asunto', mail.outbox[0].subject)
        self.assertEqual(['destino@example.com'], mail.outbox[0].to)

    def test_failure_is_logged_and_not_raised(self):
        with mock.patch('tambox.mail.EmailMessage.send', side_effect=Exception('sin smtp')):
            with self.assertLogs('tambox.mail', level='ERROR') as logs:
                send_mail(['destino@example.com'], 'Asunto', 'Cuerpo')

        self.assertIn('sin smtp', logs.output[0])


class ConfigTest(TestCase):

    def setUp(self):
        clear_cache()

    def tearDown(self):
        clear_cache()

    def test_without_configuration_returns_none(self):
        self.assertIsNone(configuration())
        self.assertIsNone(administration_office())

    def test_company_is_a_singleton(self):
        """`Company.load()` crea la fila si no existe, por eso nunca es None."""
        first = company()
        clear_cache()
        self.assertEqual(first.pk, company().pk)

    def test_reads_the_configuration(self):
        office = baker.make('administration.Office')
        baker.make('accounting.Configuration', administration=office)

        clear_cache()

        self.assertEqual(office, administration_office())


class StatusesTest(TestCase):

    def test_classify(self):
        self.assertEqual(EMPTY, classify(0, 10))
        self.assertEqual(PARTIAL, classify(5, 10))
        self.assertEqual(COMPLETE, classify(10, 10))


class NavigableQuerySetTest(TestCase):

    def setUp(self):
        self.first = baker.make(Warehouse)
        self.middle = baker.make(Warehouse)
        self.last = baker.make(Warehouse)

    def test_last_record(self):
        self.assertEqual(self.last.pk, Warehouse.objects.last_record().pk)

    def test_previous_wraps_around(self):
        self.assertEqual(self.last.pk, Warehouse.objects.previous(self.first).pk)

    def test_next_wraps_around(self):
        self.assertEqual(self.first.pk, Warehouse.objects.next(self.last).pk)

    def test_previous_and_next_in_the_middle(self):
        self.assertEqual(self.first.pk, Warehouse.objects.previous(self.middle).pk)
        self.assertEqual(self.last.pk, Warehouse.objects.next(self.middle).pk)


class ProductionSettingsTest(TestCase):
    """Los flags de seguridad que no trae Django por defecto y que, si se
    pierden, dejan el sitio sin forzar HTTPS ni cookies seguras."""

    def test_security_flags(self):
        from tambox.settings import production

        self.assertFalse(production.DEBUG)
        self.assertEqual(('HTTP_X_FORWARDED_PROTO', 'https'),
                         production.SECURE_PROXY_SSL_HEADER)
        self.assertTrue(production.SESSION_COOKIE_SECURE)
        self.assertTrue(production.CSRF_COOKIE_SECURE)

    def test_manifest_storage_for_static(self):
        from tambox.settings import production

        self.assertEqual('whitenoise.storage.CompressedManifestStaticFilesStorage',
                         production.STORAGES['staticfiles']['BACKEND'])
