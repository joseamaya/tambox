import logging

from django.core.mail import get_connection
from django.core.mail.message import EmailMessage
from contabilidad.models import Company

logger = logging.getLogger(__name__)

try:
    company = Company.load()
    my_host = company.mail_host
    my_port = company.mail_port
    my_username = company.username
    my_password = company.password
    my_use_tls = company.uses_tls
    connection = get_connection(host=my_host,
                                port=my_port,
                                username=my_username,
                                password=my_password,
                                use_tls=my_use_tls)
except Exception as exc:
    logger.warning("No se pudo configurar el servidor de correo: %s", exc)
    company = None
    connection = None


def send_mail(destinatario, asunto, cuerpo):
    email = EmailMessage()
    email.subject = asunto
    email.body = cuerpo
    email.to = destinatario
    email.connection = connection
    try:
        email.send()
    except Exception:
        logger.exception("No se pudo enviar el correo a %s", destinatario)
