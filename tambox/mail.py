import logging

from django.core.mail import get_connection
from django.core.mail.message import EmailMessage
from contabilidad.models import Empresa

logger = logging.getLogger(__name__)

try:
    empresa = Empresa.load()
    my_host = empresa.mail_host
    my_port = empresa.mail_port
    my_username = empresa.usuario
    my_password = empresa.password
    my_use_tls = empresa.uses_tls
    connection = get_connection(host=my_host,
                                port=my_port,
                                username=my_username,
                                password=my_password,
                                use_tls=my_use_tls)
except Exception as exc:
    logger.warning("No se pudo configurar el servidor de correo: %s", exc)
    empresa = None
    connection = None


def enviar_correo(destinatario, asunto, cuerpo):
    email = EmailMessage()
    email.subject = asunto
    email.body = cuerpo
    email.to = destinatario
    email.connection = connection
    try:
        email.send()
    except Exception:
        logger.exception("No se pudo enviar el correo a %s", destinatario)
