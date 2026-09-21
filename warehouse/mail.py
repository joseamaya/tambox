# -*- coding: utf-8 -*-
from tambox.mail import send_mail


def order_creation_mail(destinatario, order):
    asunto = u'SIAD - Pedido Pendiente de Aprobar - Logística'
    cuerpo = u'''Tiene un pedido pendiente de aprobar:\n
    Nro: %s \n
    Solicitante: %s \n
    Fecha: %s \n
    Por favor ingrese a TAMBOX para hacer la aprobación correspondiente.\n
    http://172.20.30.29/tambox \n
    Saludos. 
    ''' % (order.code, order.requester.full_name(), order.date.strftime('%d/%m/%Y'))
    send_mail([destinatario], asunto, cuerpo)
