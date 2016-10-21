# -*- coding: utf-8 -*-
from siad.mail import enviar_correo

def correo_creacion_pedido(destinatario, pedido):
    asunto = u'SIAD - Pedido Pendiente de Aprobar - Logística'
    cuerpo = u'''Tiene un pedido pendiente de aprobar:\n
    Nro: %s \n
    Solicitante: %s \n
    Fecha: %s \n
    Por favor ingrese a SIAD para hacer la aprobación correspondiente.\n
    http://IP/siad \n
    Saludos. 
    ''' % (pedido.codigo, pedido.solicitante.nombre_completo(),pedido.fecha.strftime('%d/%m/%Y'))
    enviar_correo(destinatario, asunto, cuerpo)