from django.core.mail import get_connection
from django.core.mail.message import EmailMessage
from contabilidad.models import Empresa

empresa = Empresa.load()

my_host = empresa.host_correo
my_port = empresa.puerto_correo
my_username = empresa.usuario
my_password = empresa.password
my_use_tls = empresa.usa_tls

connection = get_connection(host=my_host, 
                            port=my_port, 
                            username=my_username, 
                            password=my_password, 
                            use_tls=my_use_tls) 

def enviar_correo(destinatario,asunto,cuerpo):
    email = EmailMessage()
    email.subject = asunto
    email.body = cuerpo
    email.to = destinatario
    email.connection = connection 
    email.send()