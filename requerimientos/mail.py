# -*- coding: utf-8 -*-
import tambox.mail

def correo_creacion_requerimiento(destinatario,requerimiento):    
    asunto = u'TAMBOX - Requerimiento Pendiente de Aprobar'
    cuerpo = u'''Tiene un requerimiento pendiente de aprobar:\n
    Nro: %s \n
    Solicitante: %s \n
    Fecha: %s \n
    Por favor ingrese a TAMBOX para hacer la aprobación correspondiente.\n
    http://IP/siad \n
    Saludos. 
    ''' % (requerimiento.codigo, requerimiento.solicitante.nombre_completo(),requerimiento.created.strftime('%d/%m/%Y'))
    tambox.mail.enviar_correo(destinatario, asunto, cuerpo)
