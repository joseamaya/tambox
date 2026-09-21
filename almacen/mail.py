# -*- coding: utf-8 -*-
from tambox.mail import enviar_correo


def correo_creacion_pedido(destinatario, order):
    asunto = u'SIAD - Pedido Pendiente de Aprobar - Logística'
    cuerpo = u'''Tiene un pedido pendiente de aprobar:\n
    Nro: %s \n
    Solicitante: %s \n
    Fecha: %s \n
    Por favor ingrese a TAMBOX para hacer la aprobación correspondiente.\n
    http://172.20.30.29/tambox \n
    Saludos. 
    ''' % (order.code, order.requester.nombre_completo(), order.date.strftime('%d/%m/%Y'))
    enviar_correo([destinatario], asunto, cuerpo)
