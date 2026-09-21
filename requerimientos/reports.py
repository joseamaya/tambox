# -*- coding: utf-8 -*-
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Image, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY
from reportlab.platypus import Table
from reportlab.lib import colors
from reportlab.lib.units import cm
from reportlab.platypus.flowables import Spacer
from requerimientos.models import DetalleRequerimiento
from django.conf import settings
from administracion.models import Puesto
import os
from io import BytesIO
from tambox.configuracion import empresa, logistica


class ReporteRequerimiento():

    def __init__(self, pagesize, requerimiento):
        self.requerimiento = requerimiento
        self.buffer = BytesIO()
        if pagesize == 'A4':
            self.pagesize = A4
        elif pagesize == 'Letter':
            self.pagesize = letter
        self.width, self.height = self.pagesize

    def tabla_encabezado(self, styles):
        sp = ParagraphStyle('parrafos',
                            alignment=TA_CENTER,
                            fontSize=14,
                            fontName="Times-Roman")
        requerimiento = self.requerimiento
        try:
            archivo_imagen = os.path.join(settings.MEDIA_ROOT, str(empresa().logo))
            imagen = Image(archivo_imagen, width=90, height=50, hAlign='LEFT')
        except Exception:
            imagen = Paragraph(u"LOGO", sp)
        nro = Paragraph(u"REQUERIMIENTO DE BIENES Y SERVICIOS<br/>N°" + requerimiento.code, sp)
        encabezado = [[imagen, nro, '']]
        tabla_encabezado = Table(encabezado, colWidths=[4 * cm, 11 * cm, 4 * cm])
        tabla_encabezado.setStyle(TableStyle(
            [
                ('ALIGN', (0, 0), (1, 0), 'CENTER'),
                ('VALIGN', (0, 0), (1, 0), 'CENTER'),
            ]
        ))
        return tabla_encabezado

    def tabla_datos(self, styles):
        requerimiento = self.requerimiento
        izquierda = ParagraphStyle('parrafos',
                                   alignment=TA_LEFT,
                                   fontSize=10,
                                   fontName="Times-Roman")
        solicitado = Paragraph(u"SOLICITADO POR: " + requerimiento.solicitante.nombre_completo(), izquierda)
        oficina = Paragraph(u"OFICINA: " + requerimiento.oficina.name, izquierda)
        motivo = Paragraph(u"MOTIVO: " + requerimiento.motivo, izquierda)
        date = Paragraph(u"FECHA DE REQUERIMIENTO: " + requerimiento.date.strftime('%d/%m/%Y'), izquierda)
        mes = Paragraph(u"MES EN QUE SE NECESITA: " + requerimiento.get_mes_display(), izquierda)
        para_stock = Paragraph(u"AÑO EN QUE SE NECESITA: " + str(requerimiento.annio), izquierda)
        if requerimiento.entrega_directa_solicitante:
            entrega = Paragraph(u"ENTREGA DIRECTAMENTE AL SOLICITANTE: SI", izquierda)
        else:
            entrega = Paragraph(u"ENTREGA DIRECTAMENTE AL SOLICITANTE: NO", izquierda)
        datos = [[solicitado, oficina], [motivo], [date, mes], [para_stock, entrega]]
        tabla_datos = Table(datos, colWidths=[11 * cm, 9 * cm])
        style = TableStyle(
            [
                ('SPAN', (0, 1), (1, 1)),
            ]
        )
        tabla_datos.setStyle(style)
        return tabla_datos

    def tabla_detalle(self):
        requerimiento = self.requerimiento
        encabezados = ['Nro', 'Cantidad', 'Unidad', u'Descripción', 'Uso']
        detalles = DetalleRequerimiento.objects.filter(requerimiento=requerimiento)
        sp = ParagraphStyle('parrafos')
        sp.alignment = TA_JUSTIFY
        sp.fontSize = 8
        sp.fontName = "Times-Roman"
        lista_detalles = []
        for detalle in detalles:
            tupla_producto = [Paragraph(str(detalle.line_number), sp),
                              Paragraph(str(detalle.quantity), sp),
                              Paragraph(detalle.producto.unidad_medida.description, sp),
                              Paragraph(detalle.producto.description, sp),
                              Paragraph(detalle.uso, sp)]
            lista_detalles.append(tupla_producto)
        tabla_detalle = Table([encabezados] + lista_detalles, colWidths=[0.8 * cm, 2 * cm, 2.5 * cm, 7 * cm, 7.7 * cm])
        style = TableStyle(
            [
                ('ALIGN', (0, 0), (4, 0), 'CENTER'),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('FONTSIZE', (0, 0), (-1, -1), 7),
                ('ALIGN', (4, 1), (-1, -1), 'LEFT'),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ]
        )
        tabla_detalle.setStyle(style)
        return tabla_detalle

    def tabla_observaciones(self):
        requerimiento = self.requerimiento
        p = ParagraphStyle('parrafos')
        p.alignment = TA_JUSTIFY
        p.fontSize = 8
        p.fontName = "Times-Roman"
        obs = Paragraph("OBSERVACIONES: " + requerimiento.notes, p)
        notes = [[obs]]
        tabla_observaciones = Table(notes, colWidths=[20 * cm], rowHeights=1.8 * cm)
        tabla_observaciones.setStyle(TableStyle(
            [
                ('GRID', (0, 0), (0, 2), 1, colors.black),
                ('FONTSIZE', (0, 0), (-1, -1), 8),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ]
        ))
        return tabla_observaciones

    def obtener_firma(self, firma_trabajador):
        p = ParagraphStyle('parrafos',
                           alignment=TA_CENTER,
                           fontSize=8,
                           fontName="Times-Roman")
        if firma_trabajador != '':
            archivo_firma = os.path.join(settings.MEDIA_ROOT, str(firma_trabajador))
            firma = Image(archivo_firma, width=90, height=50, hAlign='CENTER')
        else:
            firma = Paragraph(u"Firma No Encontrada", p)
        return firma

    def obtener_puesto(self, oficina, requerimiento):
        try:
            jefatura = Puesto.objects.get(oficina=oficina,
                                          es_jefatura=True,
                                          start_date__lte=requerimiento.date,
                                          end_date=None)
        except Puesto.DoesNotExist:
            jefatura = Puesto.objects.get(oficina=oficina,
                                          es_jefatura=True,
                                          start_date__lte=requerimiento.date,
                                          end_date__gte=requerimiento.date)
        return jefatura

    def tabla_firmas(self):
        requerimiento = self.requerimiento
        solicitante = requerimiento.solicitante
        p = ParagraphStyle('parrafos',
                           alignment=TA_CENTER,
                           fontSize=8,
                           fontName="Times-Roman")
        encabezados = [(u'Recepción', '', '', '', '', '')]
        jefatura_logistica = self.obtener_puesto(logistica(), requerimiento)
        jefe_logistica = jefatura_logistica.trabajador
        firma_solicitante = self.obtener_firma(solicitante.firma)
        firma_jefe_oficina_logistica = self.obtener_firma(jefe_logistica.firma)
        solicitante = requerimiento.solicitante.nombre_completo()
        cuerpo = [('', '', '', '', '', '')]
        if requerimiento.approval.nivel.description == "USUARIO" and requerimiento.approval.is_active:
            cuerpo = [('', firma_solicitante, '', '', '', '')]
        elif requerimiento.approval.nivel.description == "LOGISTICA" and requerimiento.approval.is_active:
            cuerpo = [(firma_jefe_oficina_logistica, firma_solicitante, '', '', '', '')]

        try:
            received_date = requerimiento.received_date.strftime('%d/%m/%Y')
        except AttributeError:
            received_date = ''
        pie = [(Paragraph('Fecha: ' + received_date + "<br/>" + jefe_logistica.nombre_completo(), p),
                Paragraph("Solicitado por: <br/>" + solicitante, p),
                '',
                '',
                '',
                '')]
        tabla_firmas = Table(encabezados + cuerpo + pie,
                             colWidths=[3.3 * cm, 3.3 * cm, 3.3 * cm, 3.3 * cm, 3.4 * cm, 3.4 * cm],
                             rowHeights=[0.5 * cm, 2 * cm, 1.8 * cm])
        tabla_firmas.setStyle(TableStyle(
            [
                ('GRID', (0, 0), (5, 2), 1, colors.black),
                ('FONTSIZE', (0, 0), (-1, -1), 8),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('ALIGN', (0, 1), (5, 1), 'CENTER'),
                ('ALIGN', (0, 2), (5, 2), 'CENTER'),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ]
        ))
        return tabla_firmas

    def imprimir(self):
        buffer = self.buffer
        doc = SimpleDocTemplate(buffer,
                                rightMargin=50,
                                leftMargin=50,
                                topMargin=20,
                                bottomMargin=50,
                                pagesize=self.pagesize)

        elements = []
        styles = getSampleStyleSheet()
        elements.append(self.tabla_encabezado(styles))
        elements.append(Spacer(1, 0.25 * cm))
        elements.append(self.tabla_datos(styles))
        elements.append(Spacer(1, 0.25 * cm))
        elements.append(self.tabla_detalle())
        elements.append(Spacer(1, 0.25 * cm))
        elements.append(self.tabla_observaciones())
        elements.append(Spacer(1, 0.25 * cm))
        elements.append(self.tabla_firmas())
        doc.build(elements)
        pdf = buffer.getvalue()
        buffer.close()
        return pdf
