# -*- coding: utf-8 -*-
from django.core.mail.message import EmailMessage

def enviar_correo(destinatario,asunto,cuerpo):
    email = EmailMessage()
    email.subject = asunto
    email.body = cuerpo
    email.to = destinatario
    email.send()
    
def correo_creacion_requerimiento(destinatario,requerimiento):    
    asunto = u'Tambox - Requerimiento Pendiente de Aprobar'
    cuerpo = u'''Tiene un requerimiento pendiente de aprobar:\n
    Nro: %s \n
    Solicitante: %s \n
    Fecha: %s \n
    Por favor ingrese a Tambox para hacer la aprobación correspondiente.\n
    http://IP/tambox \n
    Saludos. 
    ''' % (requerimiento.codigo, requerimiento.solicitante.nombre_completo(),requerimiento.created.strftime('%d/%m/%Y'))
    enviar_correo(destinatario, asunto, cuerpo)
    
    
    
