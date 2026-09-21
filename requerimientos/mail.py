# -*- coding: utf-8 -*-
from tambox.mail import send_mail


def requirement_creation_mail(destinatario, requirement):
    asunto = u'TAMBOX - Requerimiento Pendiente de Aprobar'
    cuerpo = u'''Tiene un requerimiento pendiente de aprobar:\n
    Nro: %s \n
    Solicitante: %s \n
    Fecha: %s \n
    Por favor ingrese a TAMBOX para hacer la aprobación correspondiente.\n
    http://IP/tambox \n
    Saludos. 
    ''' % (
    requirement.code, requirement.requester.full_name(), requirement.created.strftime('%d/%m/%Y'))
    send_mail([destinatario], asunto, cuerpo)
