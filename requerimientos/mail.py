# -*- coding: utf-8 -*-
from tambox.mail import enviar_correo


def correo_creacion_requerimiento(destinatario, requirement):
    asunto = u'TAMBOX - Requerimiento Pendiente de Aprobar'
    cuerpo = u'''Tiene un requerimiento pendiente de aprobar:\n
    Nro: %s \n
    Solicitante: %s \n
    Fecha: %s \n
    Por favor ingrese a TAMBOX para hacer la aprobación correspondiente.\n
    http://IP/tambox \n
    Saludos. 
    ''' % (
    requirement.code, requirement.requester.nombre_completo(), requirement.created.strftime('%d/%m/%Y'))
    enviar_correo([destinatario], asunto, cuerpo)
