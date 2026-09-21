# -*- coding: utf-8 -*-
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Image, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY
from reportlab.platypus import Table
from reportlab.lib import colors
from reportlab.lib.units import cm
from reportlab.platypus.flowables import Spacer
from requerimientos.models import RequirementDetail
from django.conf import settings
from administracion.models import Position
import os
from io import BytesIO
from tambox.config import company, logistics


class RequirementReport():

    def __init__(self, pagesize, requirement):
        self.requirement = requirement
        self.buffer = BytesIO()
        if pagesize == 'A4':
            self.pagesize = A4
        elif pagesize == 'Letter':
            self.pagesize = letter
        self.width, self.height = self.pagesize

    def header_table(self, styles):
        sp = ParagraphStyle('parrafos',
                            alignment=TA_CENTER,
                            fontSize=14,
                            fontName="Times-Roman")
        requirement = self.requirement
        try:
            archivo_imagen = os.path.join(settings.MEDIA_ROOT, str(company().logo))
            image = Image(archivo_imagen, width=90, height=50, hAlign='LEFT')
        except Exception:
            image = Paragraph(u"LOGO", sp)
        nro = Paragraph(u"REQUERIMIENTO DE BIENES Y SERVICIOS<br/>N°" + requirement.code, sp)
        encabezado = [[image, nro, '']]
        header_table = Table(encabezado, colWidths=[4 * cm, 11 * cm, 4 * cm])
        header_table.setStyle(TableStyle(
            [
                ('ALIGN', (0, 0), (1, 0), 'CENTER'),
                ('VALIGN', (0, 0), (1, 0), 'CENTER'),
            ]
        ))
        return header_table

    def data_table(self, styles):
        requirement = self.requirement
        izquierda = ParagraphStyle('parrafos',
                                   alignment=TA_LEFT,
                                   fontSize=10,
                                   fontName="Times-Roman")
        solicitado = Paragraph(u"SOLICITADO POR: " + requirement.requester.full_name(), izquierda)
        office = Paragraph(u"OFICINA: " + requirement.office.name, izquierda)
        reason = Paragraph(u"MOTIVO: " + requirement.reason, izquierda)
        date = Paragraph(u"FECHA DE REQUERIMIENTO: " + requirement.date.strftime('%d/%m/%Y'), izquierda)
        month = Paragraph(u"MES EN QUE SE NECESITA: " + requirement.get_mes_display(), izquierda)
        para_stock = Paragraph(u"AÑO EN QUE SE NECESITA: " + str(requirement.year), izquierda)
        if requirement.direct_delivery_to_requester:
            entrega = Paragraph(u"ENTREGA DIRECTAMENTE AL SOLICITANTE: SI", izquierda)
        else:
            entrega = Paragraph(u"ENTREGA DIRECTAMENTE AL SOLICITANTE: NO", izquierda)
        datos = [[solicitado, office], [reason], [date, month], [para_stock, entrega]]
        data_table = Table(datos, colWidths=[11 * cm, 9 * cm])
        style = TableStyle(
            [
                ('SPAN', (0, 1), (1, 1)),
            ]
        )
        data_table.setStyle(style)
        return data_table

    def tabla_detalle(self):
        requirement = self.requirement
        encabezados = ['Nro', 'Cantidad', 'Unidad', u'Descripción', 'Uso']
        detalles = RequirementDetail.objects.filter(requirement=requirement)
        sp = ParagraphStyle('parrafos')
        sp.alignment = TA_JUSTIFY
        sp.fontSize = 8
        sp.fontName = "Times-Roman"
        lista_detalles = []
        for detail in detalles:
            tupla_producto = [Paragraph(str(detail.line_number), sp),
                              Paragraph(str(detail.quantity), sp),
                              Paragraph(detail.product.unit_of_measure.description, sp),
                              Paragraph(detail.product.description, sp),
                              Paragraph(detail.use, sp)]
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

    def notes_table(self):
        requirement = self.requirement
        p = ParagraphStyle('parrafos')
        p.alignment = TA_JUSTIFY
        p.fontSize = 8
        p.fontName = "Times-Roman"
        obs = Paragraph("OBSERVACIONES: " + requirement.notes, p)
        notes = [[obs]]
        notes_table = Table(notes, colWidths=[20 * cm], rowHeights=1.8 * cm)
        notes_table.setStyle(TableStyle(
            [
                ('GRID', (0, 0), (0, 2), 1, colors.black),
                ('FONTSIZE', (0, 0), (-1, -1), 8),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ]
        ))
        return notes_table

    def get_signature(self, firma_trabajador):
        p = ParagraphStyle('parrafos',
                           alignment=TA_CENTER,
                           fontSize=8,
                           fontName="Times-Roman")
        if firma_trabajador != '':
            archivo_firma = os.path.join(settings.MEDIA_ROOT, str(firma_trabajador))
            signature = Image(archivo_firma, width=90, height=50, hAlign='CENTER')
        else:
            signature = Paragraph(u"Firma No Encontrada", p)
        return signature

    def get_position(self, office, requirement):
        try:
            jefatura = Position.objects.get(office=office,
                                          is_leadership=True,
                                          start_date__lte=requirement.date,
                                          end_date=None)
        except Position.DoesNotExist:
            jefatura = Position.objects.get(office=office,
                                          is_leadership=True,
                                          start_date__lte=requirement.date,
                                          end_date__gte=requirement.date)
        return jefatura

    def signatures_table(self):
        requirement = self.requirement
        requester = requirement.requester
        p = ParagraphStyle('parrafos',
                           alignment=TA_CENTER,
                           fontSize=8,
                           fontName="Times-Roman")
        encabezados = [(u'Recepción', '', '', '', '', '')]
        jefatura_logistica = self.get_position(logistics(), requirement)
        jefe_logistica = jefatura_logistica.worker
        firma_solicitante = self.get_signature(requester.signature)
        firma_jefe_oficina_logistica = self.get_signature(jefe_logistica.signature)
        requester = requirement.requester.full_name()
        cuerpo = [('', '', '', '', '', '')]
        if requirement.approval.level.description == "USUARIO" and requirement.approval.is_active:
            cuerpo = [('', firma_solicitante, '', '', '', '')]
        elif requirement.approval.level.description == "LOGISTICA" and requirement.approval.is_active:
            cuerpo = [(firma_jefe_oficina_logistica, firma_solicitante, '', '', '', '')]

        try:
            received_date = requirement.received_date.strftime('%d/%m/%Y')
        except AttributeError:
            received_date = ''
        pie = [(Paragraph('Fecha: ' + received_date + "<br/>" + jefe_logistica.full_name(), p),
                Paragraph("Solicitado por: <br/>" + requester, p),
                '',
                '',
                '',
                '')]
        signatures_table = Table(encabezados + cuerpo + pie,
                             colWidths=[3.3 * cm, 3.3 * cm, 3.3 * cm, 3.3 * cm, 3.4 * cm, 3.4 * cm],
                             rowHeights=[0.5 * cm, 2 * cm, 1.8 * cm])
        signatures_table.setStyle(TableStyle(
            [
                ('GRID', (0, 0), (5, 2), 1, colors.black),
                ('FONTSIZE', (0, 0), (-1, -1), 8),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('ALIGN', (0, 1), (5, 1), 'CENTER'),
                ('ALIGN', (0, 2), (5, 2), 'CENTER'),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ]
        ))
        return signatures_table

    def render(self):
        buffer = self.buffer
        doc = SimpleDocTemplate(buffer,
                                rightMargin=50,
                                leftMargin=50,
                                topMargin=20,
                                bottomMargin=50,
                                pagesize=self.pagesize)

        elements = []
        styles = getSampleStyleSheet()
        elements.append(self.header_table(styles))
        elements.append(Spacer(1, 0.25 * cm))
        elements.append(self.data_table(styles))
        elements.append(Spacer(1, 0.25 * cm))
        elements.append(self.tabla_detalle())
        elements.append(Spacer(1, 0.25 * cm))
        elements.append(self.notes_table())
        elements.append(Spacer(1, 0.25 * cm))
        elements.append(self.signatures_table())
        doc.build(elements)
        pdf = buffer.getvalue()
        buffer.close()
        return pdf
