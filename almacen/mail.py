# -*- coding: utf-8 -*-
from django.core.mail.message import EmailMessage

def correo_creacion_pedido(destinatario, pedido):
    asunto = u'TAMBOX - Pedido Pendiente de Aprobar - Logística'
    cuerpo = u'''Tiene un pedido pendiente de aprobar:\n
    Nro: %s \n
    Solicitante: %s \n
    Fecha: %s \n
    Por favor ingrese a TAMBOX para hacer la aprobación correspondiente.\n
    http://IP/tambox \n
    Saludos. 
    ''' % (pedido.codigo, pedido.solicitante.nombre_completo(),pedido.fecha.strftime('%d/%m/%Y'))
    enviar_correo(destinatario, asunto, cuerpo)
        
def enviar_correo(destinatario,asunto,cuerpo):
    email = EmailMessage()
    email.subject = asunto
    email.body = cuerpo
    email.to = destinatario
    email.send()