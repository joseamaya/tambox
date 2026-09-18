# -*- coding: utf-8 -*-

from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Image, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY
from reportlab.platypus import Table
from reportlab.lib import colors
# from reportlab.lib.pagesizes import cm
from reportlab.platypus.flowables import Spacer, ListFlowable
from reportlab.graphics.shapes import Line, Drawing
from django.conf import settings
import os
from io import BytesIO
from compras.models import DetalleOrdenCompra
from django.core.exceptions import ObjectDoesNotExist
from django.utils.encoding import force_str
from tambox.configuracion import empresa
from openpyxl import Workbook
from openpyxl.styles import Alignment
from openpyxl.styles import Border
from openpyxl.styles import Font
from openpyxl.styles import Side


class ReporteOrdenCompra():

    def __init__(self, pagesize, orden_compra):
        self.orden_compra = orden_compra
        self.buffer = BytesIO()
        if pagesize == 'A4':
            self.pagesize = A4
        elif pagesize == 'Letter':
            self.pagesize = letter
        self.width, self.height = self.pagesize

    def tabla_encabezado(self, styles):
        orden_compra = self.orden_compra
        sp = ParagraphStyle('parrafos',
                            alignment=TA_CENTER,
                            fontSize=14,
                            fontName="Times-Roman")
        try:
            archivo_imagen = os.path.join(settings.MEDIA_ROOT, str(empresa().logo))
            imagen = Image(archivo_imagen, width=90, height=50, hAlign='LEFT')
        except Exception:
            imagen = Paragraph(u"LOGO", sp)

        nro = Paragraph(u"ORDEN DE COMPRA", sp)
        ruc = Paragraph("R.U.C." + empresa().ruc, sp)
        encabezado = [[imagen, nro, ruc], ['', u"N°" + orden_compra.codigo,
                                           empresa().distrito + " " + orden_compra.fecha.strftime('%d de %b de %Y')]]
        tabla_encabezado = Table(encabezado, colWidths=[4 * cm, 9 * cm, 6 * cm])
        tabla_encabezado.setStyle(TableStyle(
            [
                ('ALIGN', (0, 0), (2, 1), 'CENTER'),
                ('VALIGN', (0, 0), (2, 0), 'CENTER'),
                ('VALIGN', (1, 1), (2, 1), 'TOP'),
                ('SPAN', (0, 0), (0, 1)),

            ]
        ))
        return tabla_encabezado

    def tabla_datos(self, styles):
        orden = self.orden_compra
        izquierda = ParagraphStyle('parrafos',
                                   alignment=TA_LEFT,
                                   fontSize=10,
                                   fontName="Times-Roman")
        cotizacion = orden.cotizacion
        if cotizacion is None:
            proveedor = orden.proveedor
        else:
            proveedor = orden.cotizacion.proveedor
        razon_social_proveedor = Paragraph(u"SEÑOR(ES): " + proveedor.razon_social, izquierda)
        ruc_proveedor = Paragraph(u"R.U.C.: " + proveedor.ruc, izquierda)
        direccion = Paragraph(u"DIRECCIÓN: " + proveedor.direccion, izquierda)
        try:
            telefono = Paragraph(u"TELÉFONO: " + proveedor.telefono, izquierda)
        except TypeError:
            telefono = Paragraph(u"TELÉFONO: -", izquierda)
        try:
            referencia = Paragraph(
                u"REFERENCIA: " + orden.cotizacion.requerimiento.codigo + " - " + orden.cotizacion.requerimiento.oficina.nombre,
                izquierda)
        except (ObjectDoesNotExist, AttributeError):
            referencia = Paragraph(u"REFERENCIA: ", izquierda)
        proceso = Paragraph(u"PROCESO: " + orden.proceso, izquierda)
        nota = Paragraph(u"Sírvase remitirnos según especificaciones que detallamos lo siguiente: ", izquierda)
        datos = [[razon_social_proveedor, ruc_proveedor], [direccion, telefono], [referencia, ''], [proceso, ''],
                 [nota, '']]
        tabla_detalle = Table(datos, colWidths=[11 * cm, 9 * cm])
        tabla_detalle.setStyle(TableStyle(
            [
                ('SPAN', (0, 2), (1, 2)),
            ]
        ))
        return tabla_detalle

    def tabla_detalle(self):
        orden = self.orden_compra
        encabezados = ['Item', 'Cantidad', 'Unidad', u'Descripción', 'Precio', 'Total']
        detalles = DetalleOrdenCompra.objects.filter(orden=orden).order_by('pk')
        sp = ParagraphStyle('parrafos')
        sp.alignment = TA_JUSTIFY
        sp.fontSize = 8
        sp.fontName = "Times-Roman"
        lista_detalles = []
        for detalle in detalles:
            try:
                tupla_producto = [Paragraph(str(detalle.nro_detalle), sp),
                                  Paragraph(str(detalle.cantidad), sp),
                                  Paragraph(
                                      detalle.detalle_cotizacion.detalle_requerimiento.producto.unidad_medida.descripcion,
                                      sp),
                                  Paragraph(detalle.detalle_cotizacion.detalle_requerimiento.producto.descripcion, sp),
                                  Paragraph(str(detalle.precio), sp),
                                  Paragraph(str(detalle.valor), sp)]
            except (ObjectDoesNotExist, AttributeError):
                tupla_producto = [Paragraph(str(detalle.nro_detalle), sp),
                                  Paragraph(str(detalle.cantidad), sp),
                                  Paragraph(detalle.producto.unidad_medida.descripcion, sp),
                                  Paragraph(detalle.producto.descripcion, sp),
                                  Paragraph(str(detalle.precio), sp),
                                  Paragraph(str(detalle.valor), sp)]
            lista_detalles.append(tupla_producto)
        adicionales = [('', '', '', '', '')] * (15 - len(lista_detalles))
        tabla_detalle = Table([encabezados] + lista_detalles + adicionales,
                              colWidths=[0.8 * cm, 2 * cm, 2.5 * cm, 10.2 * cm, 2 * cm, 2.5 * cm])
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

    def tabla_total_letras(self):
        orden = self.orden_compra
        total_letras = [("SON: " + orden.total_letras, '')]
        tabla_total_letras = Table(total_letras, colWidths=[17.5 * cm, 2.5 * cm])
        tabla_total_letras.setStyle(TableStyle(
            [
                ('GRID', (0, 0), (1, 0), 1, colors.black),
                ('FONTSIZE', (0, 0), (-1, -1), 8),
            ]
        ))
        return tabla_total_letras

    def tabla_otros(self):
        orden = self.orden_compra
        p = ParagraphStyle('parrafos',
                           alignment=TA_CENTER,
                           fontSize=8,
                           fontName="Times-Roman")
        sub_total = Paragraph(u"SUBTOTAL: ", p)
        igv = Paragraph(u"IGV: ", p)
        total = Paragraph(u"TOTAL: ", p)
        datos_otros = [
            [Paragraph(u"LUGAR DE ENTREGA", p), Paragraph(u"PLAZO DE ENTREGA", p), Paragraph(u"FORMA DE PAGO", p),
             sub_total, orden.subtotal],
            [Paragraph(empresa().direccion(), p), Paragraph(u"INMEDIATA", p), Paragraph(orden.forma_pago.descripcion, p),
             igv, str(orden.igv)],
            ['', '', '', total, str(orden.total)],
            ]
        tabla_otros = Table(datos_otros, colWidths=[5.5 * cm, 5 * cm, 5 * cm, 2 * cm, 2.5 * cm])
        tabla_otros.setStyle(TableStyle(
            [
                ('GRID', (0, 0), (2, 2), 1, colors.black),
                ('SPAN', (0, 1), (0, 2)),
                ('SPAN', (1, 1), (1, 2)),
                ('SPAN', (2, 1), (2, 2)),
                ('GRID', (4, 0), (4, 2), 1, colors.black),
                ('VALIGN', (0, 1), (2, 1), 'MIDDLE'),
            ]
        ))
        return tabla_otros

    def tabla_observaciones(self):
        orden = self.orden_compra
        p = ParagraphStyle('parrafos',
                           alignment=TA_JUSTIFY,
                           fontSize=8,
                           fontName="Times-Roman")
        obs = Paragraph("OBSERVACIONES: " + orden.observaciones, p)
        observaciones = [[obs]]
        tabla_observaciones = Table(observaciones, colWidths=[20 * cm], rowHeights=1.8 * cm)
        tabla_observaciones.setStyle(TableStyle(
            [
                ('GRID', (0, 0), (0, 2), 1, colors.black),
                ('FONTSIZE', (0, 0), (-1, -1), 8),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ]
        ))
        return tabla_observaciones

    def tabla_afectacion_presupuestal(self):
        orden = self.orden_compra
        p = ParagraphStyle('parrafos',
                           alignment=TA_JUSTIFY,
                           fontSize=8,
                           fontName="Times-Roman")
        hoja_afectacion = Paragraph(u"HOJA DE AFECTACIÓN PRESUPUESTAL: ", p)
        importante = Paragraph(u"IMPORTANTE: ", p)
        recibido = Paragraph(u"RECIBIDO POR: ", p)
        firma = Paragraph(u"FIRMA: ", p)
        nombre = Paragraph(u"NOMBRE: ", p)
        dni = Paragraph(u"DNI: ", p)
        lista = ListFlowable([
            Paragraph("""Consignar el número de la presente Orden de Compra en su Guía de Remisión y Factura. 
                          Facturar a nombre de """ + force_str(empresa().razon_social), p),
            Paragraph("El " + force_str(empresa().razon_social) + """, se reserva el derecho de devolver 
                          la mercaderia, sino se ajusta a las especificaciones requeridas, asimismo de anular la presente 
                          Orden de Compra.""", p),
            Paragraph("""El pago de toda factura se hará de acuerdo a las condiciones establecidas.""", p)
        ], bulletType='1'
        )
        datos_otros = [[hoja_afectacion, ''],
                       [importante, recibido],
                       [lista, ''],
                       ['', firma],
                       ['', nombre],
                       ['', dni],
                       ]
        tabla_afectacion_presupuestal = Table(datos_otros, colWidths=[10 * cm, 10 * cm])
        tabla_afectacion_presupuestal.setStyle(TableStyle(
            [
                ('ALIGN', (0, 1), (1, 1), 'CENTER'),
                ('SPAN', (0, 2), (0, 5)),
            ]
        ))
        return tabla_afectacion_presupuestal

    def imprimir(self):
        y = 300
        buffer = self.buffer
        izquierda = ParagraphStyle('parrafos',
                                   alignment=TA_LEFT,
                                   fontSize=10,
                                   fontName="Times-Roman")
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
        elements.append(self.tabla_total_letras())
        elements.append(Spacer(1, 0.25 * cm))
        elements.append(self.tabla_otros())
        elements.append(Spacer(1, 0.25 * cm))
        elements.append(self.tabla_observaciones())
        elements.append(Spacer(1, 0.25 * cm))
        elements.append(self.tabla_afectacion_presupuestal())
        linea_firma = Line(280, y - 250, 470, y - 250)
        d = Drawing(100, 1)
        d.add(linea_firma)
        elements.append(d)
        doc.build(elements)
        pdf = buffer.getvalue()
        buffer.close()
        return pdf


def reporte_xls_orden_compra(orden):
    """Construye el libro de Excel de la orden de compra."""
    detalle_index = 0
    cotizacion = orden.cotizacion
    if cotizacion is None:
        proveedor = orden.proveedor
    else:
        proveedor = orden.cotizacion.proveedor
    wb = Workbook()
    ws = wb.active

    ws.column_dimensions['B'].width = 18
    ws.column_dimensions['E'].width = 15
    ws.column_dimensions['G'].width = 15
    ws.column_dimensions['I'].width = 15

    ws.merge_cells('B2:I2')
    ws['B2'].font = Font(name='Brush Script MT', size=20, color='0000ff', bold=True)
    ws['B2'].alignment = Alignment(horizontal="center", vertical="center")
    ws.row_dimensions[2].height = 25
    ws['B2'] = 'Asociación de Bananeros Orgánicos Solidarios  Salitral'
    ws.merge_cells('B3:I3')
    ws['B3'].font = Font(name='Lucida Bright', size=9, color='148918', bold=True, italic=True)
    ws['B3'].alignment = Alignment(horizontal="center", vertical="center")
    ws['B3'] = 'Inscrita en Partida Nº 11003959 de la Superintendencia Nacional de'
    ws.merge_cells('B4:I4')
    ws['B4'].font = Font(name='Lucida Bright', size=9, color='148918', bold=True, italic=True)
    ws['B4'].alignment = Alignment(horizontal="center", vertical="center")
    ws['B4'] = 'los Registros Públicos R.U.C. Nº 20484149748'
    ws.merge_cells('B5:I5')
    ws['B5'].font = Font(name='Lucida Bright', size=9, color='ff0000', bold=True, italic=True)
    ws['B5'].alignment = Alignment(horizontal="center", vertical="center")
    ws['B5'] = 'FLO Certified Banana Producer – FLO ID 2460'
    ws.merge_cells('B6:I6')
    ws['B6'].font = Font(name='Lucida Bright', size=9, color='ff0000', bold=True, italic=True)
    ws['B6'].alignment = Alignment(horizontal="center", vertical="center")
    ws['B6'] = 'Certificate Organic USDA-NOP, EU2092/91, JAS. Registration Nº CU 805878'
    ws.merge_cells('B10:I10')
    ws['B10'].font = Font(name='Calibri', size=12)
    ws['B10'].alignment = Alignment(horizontal="center", vertical="center")
    ws['B10'] = '"AÑO DEL BUEN SERVICIO AL CIUDADANO"'
    ws.merge_cells('D11:F11')
    ws['D11'].font = Font(name='Calibri', size=18, bold=True, underline="single")
    ws['D11'].alignment = Alignment(horizontal="center", vertical="center")
    ws.row_dimensions[11].height = 25
    ws['D11'] = 'ORDEN DE COMPRA'
    ws['G11'].font = Font(name='Calibri', size=11, bold=True, underline="single")
    ws['G11'].alignment = Alignment(horizontal="center", vertical="center")
    ws['G11'] = 'N°'

    ws['B13'].font = Font(size=11, bold=True)
    ws['B13'] = 'DATOS DEL CLIENTE Y DE LA FACTURA'
    ws['B14'].border = Border(left=Side(border_style="thin"), right=Side(border_style="thin"),
                              top=Side(border_style="thin"), bottom=Side(border_style="thin"))
    ws['B14'] = 'RAZÓN SOCIAL'
    ws.merge_cells('C14:G14')
    ws['C14'].alignment = Alignment(horizontal="center")
    ws['C14'].border = Border(left=Side(border_style="thin"), right=Side(border_style="thin"),
                              top=Side(border_style="thin"), bottom=Side(border_style="thin"))
    ws['C14'] = orden.proveedor.razon_social
    ws['H14'].border = Border(left=Side(border_style="thin"), right=Side(border_style="thin"),
                              top=Side(border_style="thin"), bottom=Side(border_style="thin"))
    ws['H14'] = 'FECHA'
    ws['I14'].border = Border(left=Side(border_style="thin"), right=Side(border_style="thin"),
                              top=Side(border_style="thin"), bottom=Side(border_style="thin"))
    ws['I14'] = orden.fecha
    ws['B15'].border = Border(left=Side(border_style="thin"), right=Side(border_style="thin"),
                              top=Side(border_style="thin"), bottom=Side(border_style="thin"))
    ws['B15'] = 'CONTACTO'
    ws.merge_cells('C15:G15')
    ws['C15'].border = Border(left=Side(border_style="thin"), right=Side(border_style="thin"),
                              top=Side(border_style="thin"), bottom=Side(border_style="thin"))
    ws['C15'].alignment = Alignment(horizontal="center")
    ws['C15'] = ''
    ws['H15'].border = Border(left=Side(border_style="thin"), right=Side(border_style="thin"),
                              top=Side(border_style="thin"), bottom=Side(border_style="thin"))
    ws['H15'] = 'RUC/NIT'
    ws['I15'].border = Border(left=Side(border_style="thin"), right=Side(border_style="thin"),
                              top=Side(border_style="thin"), bottom=Side(border_style="thin"))
    ws['I15'] = proveedor.ruc
    ws['B16'].border = Border(left=Side(border_style="thin"), right=Side(border_style="thin"),
                              top=Side(border_style="thin"), bottom=Side(border_style="thin"))
    ws['B16'] = 'DIRECCIÓN'
    ws.merge_cells('C16:G16')
    ws['C16'].alignment = Alignment(horizontal="center")
    ws['C16'].border = Border(left=Side(border_style="thin"), right=Side(border_style="thin"),
                              top=Side(border_style="thin"), bottom=Side(border_style="thin"))
    ws['C16'] = proveedor.direccion
    ws['H16'].border = Border(left=Side(border_style="thin"), right=Side(border_style="thin"),
                              top=Side(border_style="thin"), bottom=Side(border_style="thin"))
    ws['H16'] = 'TELÉFONO'
    ws['I16'].border = Border(left=Side(border_style="thin"), right=Side(border_style="thin"),
                              top=Side(border_style="thin"), bottom=Side(border_style="thin"))
    try:
        ws['I16'] = proveedor.telefono
    except TypeError:
        ws['I16'] = '-'
    ws['B17'].border = Border(left=Side(border_style="thin"), right=Side(border_style="thin"),
                              top=Side(border_style="thin"), bottom=Side(border_style="thin"))
    ws['B17'] = 'E-MAIL'
    ws.merge_cells('C17:G17')
    ws['C14'].alignment = Alignment(horizontal="center")
    ws['C17'].border = Border(left=Side(border_style="thin"), right=Side(border_style="thin"),
                              top=Side(border_style="thin"), bottom=Side(border_style="thin"))
    ws['C17'] = proveedor.correo
    ws['H17'].border = Border(left=Side(border_style="thin"), right=Side(border_style="thin"),
                              top=Side(border_style="thin"), bottom=Side(border_style="thin"))
    ws['H17'] = 'RPM/RPC'
    ws['I17'].border = Border(left=Side(border_style="thin"), right=Side(border_style="thin"),
                              top=Side(border_style="thin"), bottom=Side(border_style="thin"))
    ws['I17'] = ''

    ws['B19'].font = Font(size=11, bold=True)
    ws['B19'] = 'DATOS DE ENTREGA'
    ws.merge_cells('B20:C20')
    ws['B20'].border = Border(left=Side(border_style="thin"), right=Side(border_style="thin"),
                              top=Side(border_style="thin"), bottom=Side(border_style="thin"))
    ws['B20'] = 'DIRECCIÓN DE ENTREGA'
    ws.merge_cells('D20:F20')
    ws['D20'].alignment = Alignment(horizontal="center")
    ws['D20'].border = Border(left=Side(border_style="thin"), right=Side(border_style="thin"),
                              top=Side(border_style="thin"), bottom=Side(border_style="thin"))
    ws['D20'] = str(empresa().direccion())
    ws.merge_cells('G20:H20')
    ws['G20'].border = Border(left=Side(border_style="thin"), right=Side(border_style="thin"),
                              top=Side(border_style="thin"), bottom=Side(border_style="thin"))
    ws['G20'] = 'DEPARTAMENTO'
    ws['I20'].border = Border(left=Side(border_style="thin"), right=Side(border_style="thin"),
                              top=Side(border_style="thin"), bottom=Side(border_style="thin"))
    ws['I20'] = str(empresa().departamento)
    ws.merge_cells('B21:C22')
    ws['B21'].alignment = Alignment(horizontal="center", vertical="center")
    ws['B21'].border = Border(left=Side(border_style="thin"), right=Side(border_style="thin"),
                              top=Side(border_style="thin"), bottom=Side(border_style="thin"))
    ws['B21'] = 'PERSONAS AUTORIZADAS'
    ws.merge_cells('D21:F21')
    ws['D21'].alignment = Alignment(horizontal="center")
    ws['D21'].border = Border(left=Side(border_style="thin"), right=Side(border_style="thin"),
                              top=Side(border_style="thin"), bottom=Side(border_style="thin"))
    ws['D21'] = ''
    ws.merge_cells('D22:F22')
    ws['D22'].alignment = Alignment(horizontal="center")
    ws['D22'].border = Border(left=Side(border_style="thin"), right=Side(border_style="thin"),
                              top=Side(border_style="thin"), bottom=Side(border_style="thin"))
    ws['D22'] = ''
    ws.merge_cells('G21:H21')
    ws['G21'].border = Border(left=Side(border_style="thin"), right=Side(border_style="thin"),
                              top=Side(border_style="thin"), bottom=Side(border_style="thin"))
    ws['G21'] = 'PROVINCIA'
    ws['I21'].border = Border(left=Side(border_style="thin"), right=Side(border_style="thin"),
                              top=Side(border_style="thin"), bottom=Side(border_style="thin"))
    ws['I21'] = str(empresa().provincia)
    ws.merge_cells('G22:H22')
    ws['G22'].border = Border(left=Side(border_style="thin"), right=Side(border_style="thin"),
                              top=Side(border_style="thin"), bottom=Side(border_style="thin"))
    ws['G22'] = 'DISTRITO'
    ws['I22'].border = Border(left=Side(border_style="thin"), right=Side(border_style="thin"),
                              top=Side(border_style="thin"), bottom=Side(border_style="thin"))
    ws['I22'] = str(empresa().distrito)
    ws.merge_cells('B23:C24')
    ws['B23'].alignment = Alignment(horizontal="center", vertical="center")
    ws['B23'].border = Border(left=Side(border_style="thin"), right=Side(border_style="thin"),
                              top=Side(border_style="thin"), bottom=Side(border_style="thin"))
    ws['B23'] = 'TELÉFONOS'
    ws.merge_cells('D23:F23')
    ws['D23'].alignment = Alignment(horizontal="center")
    ws['D23'].border = Border(left=Side(border_style="thin"), right=Side(border_style="thin"),
                              top=Side(border_style="thin"), bottom=Side(border_style="thin"))
    ws['D23'] = ''
    ws.merge_cells('G23:H23')
    ws['G23'].border = Border(left=Side(border_style="thin"), right=Side(border_style="thin"),
                              top=Side(border_style="thin"), bottom=Side(border_style="thin"))
    ws['G23'] = 'COMENTARIO:'
    ws['I23'].border = Border(left=Side(border_style="thin"), right=Side(border_style="thin"),
                              top=Side(border_style="thin"), bottom=Side(border_style="thin"))
    ws['I23'] = ''
    ws['B24'].border = Border(bottom=Side(border_style="thin"))
    ws.merge_cells('D24:F24')
    ws['D24'].alignment = Alignment(horizontal="center")
    ws['D24'].border = Border(left=Side(border_style="thin"), right=Side(border_style="thin"),
                              top=Side(border_style="thin"), bottom=Side(border_style="thin"))
    ws['D24'] = ''
    ws.merge_cells('G24:I24')
    ws['D24'].alignment = Alignment(horizontal="center")
    ws['G24'].border = Border(left=Side(border_style="thin"), right=Side(border_style="thin"),
                              top=Side(border_style="thin"), bottom=Side(border_style="thin"))
    ws['G24'] = ''
    ws['J24'].border = Border(left=Side(border_style="thin"))
    ws.merge_cells('G25:I25')
    ws['G25'].border = Border(left=Side(border_style="thin"), right=Side(border_style="thin"),
                              top=Side(border_style="thin"), bottom=Side(border_style="thin"))
    ws['G25'] = ''
    ws['J25'].border = Border(left=Side(border_style="thin"))
    ws.merge_cells('G26:I26')
    ws['G26'].border = Border(left=Side(border_style="thin"), right=Side(border_style="thin"),
                              top=Side(border_style="thin"), bottom=Side(border_style="thin"))
    ws['G26'] = ''
    ws['J26'].border = Border(left=Side(border_style="thin"))

    ws['B28'].font = Font(size=11, bold=True)
    ws['B28'] = 'DATOS DEL PRODUCTO A ADQUIRIR'
    ws.merge_cells('B29:B30')
    ws['B29'].alignment = Alignment(horizontal="center", vertical="center")
    ws['B29'].border = Border(left=Side(border_style="thin"), right=Side(border_style="thin"),
                              top=Side(border_style="thin"), bottom=Side(border_style="thin"))
    ws['B29'] = 'UNIDAD MEDIDA'
    ws.merge_cells('C29:F30')
    ws['C29'].alignment = Alignment(horizontal="center", vertical="center")
    ws['C29'].border = Border(left=Side(border_style="thin"), right=Side(border_style="thin"),
                              top=Side(border_style="thin"), bottom=Side(border_style="thin"))
    ws['C29'] = 'DESCRIPCIÓN DEL PRODUCTO'
    ws.merge_cells('G29:G30')
    ws['G29'].alignment = Alignment(horizontal="center", vertical="center")
    ws['G29'].border = Border(left=Side(border_style="thin"), right=Side(border_style="thin"),
                              top=Side(border_style="thin"), bottom=Side(border_style="thin"))
    ws['G29'] = 'CANT.'
    ws['H29'].alignment = Alignment(horizontal="center")
    ws['H29'].border = Border(left=Side(border_style="thin"), right=Side(border_style="thin"),
                              top=Side(border_style="thin"), bottom=Side(border_style="thin"))
    ws['H29'] = 'PRECIO'
    ws['I29'].alignment = Alignment(horizontal="center")
    ws['I29'].border = Border(left=Side(border_style="thin"), right=Side(border_style="thin"),
                              top=Side(border_style="thin"), bottom=Side(border_style="thin"))
    ws['I29'] = 'PRECIO'
    ws['H30'].alignment = Alignment(horizontal="center")
    ws['H30'].border = Border(left=Side(border_style="thin"), right=Side(border_style="thin"),
                              top=Side(border_style="thin"), bottom=Side(border_style="thin"))
    ws['H30'] = 'UNITARIO'
    ws['I30'].alignment = Alignment(horizontal="center")
    ws['I30'].border = Border(left=Side(border_style="thin"), right=Side(border_style="thin"),
                              top=Side(border_style="thin"), bottom=Side(border_style="thin"))
    ws['I30'] = 'TOTAL'

    for item in DetalleOrdenCompra.objects.filter(orden=orden):
        fila = 31 + detalle_index
        ws['B' + str(fila)].alignment = Alignment(horizontal="center")
        ws['B' + str(fila)].border = Border(left=Side(border_style="thin"), right=Side(border_style="thin"),
                                            top=Side(border_style="thin"), bottom=Side(border_style="thin"))
        ws['B' + str(fila)] = item.producto.unidad_medida.descripcion
        ws.merge_cells('C' + str(fila) + ':F' + str(fila))
        ws['C' + str(fila)].alignment = Alignment(horizontal="center")
        ws['C' + str(fila)].border = Border(left=Side(border_style="thin"), right=Side(border_style="thin"),
                                            top=Side(border_style="thin"), bottom=Side(border_style="thin"))
        ws['C' + str(fila)] = item.producto.descripcion
        ws['G' + str(fila)].border = Border(left=Side(border_style="thin"), right=Side(border_style="thin"),
                                            top=Side(border_style="thin"), bottom=Side(border_style="thin"))
        ws['G' + str(fila)] = item.cantidad
        ws['H' + str(fila)].border = Border(left=Side(border_style="thin"), right=Side(border_style="thin"),
                                            top=Side(border_style="thin"), bottom=Side(border_style="thin"))
        ws['H' + str(fila)] = item.precio
        ws['I' + str(fila)].border = Border(left=Side(border_style="thin"), right=Side(border_style="thin"),
                                            top=Side(border_style="thin"), bottom=Side(border_style="thin"))
        ws['I' + str(fila)] = item.cantidad * item.precio
        detalle_index += 1

    fila_total = 31 + detalle_index
    ws.merge_cells('G' + str(fila_total) + ':H' + str(fila_total))
    ws['G' + str(fila_total)].alignment = Alignment(horizontal="center")
    ws['G' + str(fila_total)].border = Border(left=Side(border_style="thin"), right=Side(border_style="thin"),
                                              top=Side(border_style="thin"), bottom=Side(border_style="thin"))
    ws['G' + str(fila_total)] = 'SUBTOTAL'
    ws['I' + str(fila_total)].border = Border(left=Side(border_style="thin"), right=Side(border_style="thin"),
                                              top=Side(border_style="thin"), bottom=Side(border_style="thin"))
    ws['I' + str(fila_total)] = orden.subtotal
    ws.merge_cells('G' + str(fila_total + 1) + ':H' + str(fila_total + 1))
    ws['G' + str(fila_total + 1)].alignment = Alignment(horizontal="center")
    ws['G' + str(fila_total + 1)].border = Border(left=Side(border_style="thin"), right=Side(border_style="thin"),
                                                  top=Side(border_style="thin"), bottom=Side(border_style="thin"))
    ws['G' + str(fila_total + 1)] = 'IMPUESTO 18% IGV'
    ws['I' + str(fila_total + 1)].border = Border(left=Side(border_style="thin"), right=Side(border_style="thin"),
                                                  top=Side(border_style="thin"), bottom=Side(border_style="thin"))
    ws['I' + str(fila_total + 1)] = orden.impuesto
    ws.merge_cells('G' + str(fila_total + 2) + ':H' + str(fila_total + 2))
    ws['G' + str(fila_total + 2)].alignment = Alignment(horizontal="center")
    ws['G' + str(fila_total + 2)].border = Border(left=Side(border_style="thin"), right=Side(border_style="thin"),
                                                  top=Side(border_style="thin"), bottom=Side(border_style="thin"))
    ws['G' + str(fila_total + 2)] = 'TOTAL'
    ws['I' + str(fila_total + 2)].border = Border(left=Side(border_style="thin"), right=Side(border_style="thin"),
                                                  top=Side(border_style="thin"), bottom=Side(border_style="thin"))
    ws['I' + str(fila_total + 2)] = orden.total

    ws['B' + str(fila_total + 7)] = 'SON:'
    ws.merge_cells('C' + str(fila_total + 7) + ':I' + str(fila_total + 7))
    ws['C' + str(fila_total + 7)].font = Font(underline="single")
    ws['C' + str(fila_total + 7)].alignment = Alignment(horizontal="center")
    ws['C' + str(fila_total + 7)] = orden.total_letras

    fila_pago = fila_total + 9
    ws.merge_cells('E' + str(fila_pago) + ':F' + str(fila_pago))
    ws['E' + str(fila_pago)] = 'FORMA DE PAGO'

    ws.merge_cells('G' + str(fila_pago) + ':I' + str(fila_pago))
    ws['G' + str(fila_pago)].alignment = Alignment(horizontal="center")
    ws['G' + str(fila_pago)].border = Border(bottom=Side(border_style="thin"))
    ws['G' + str(fila_pago)] = orden.forma_pago.descripcion
    ws.merge_cells('E' + str(fila_pago + 1) + ':F' + str(fila_pago + 1))
    ws['E' + str(fila_pago + 1)] = 'BANCO'
    ws.merge_cells('G' + str(fila_pago + 1) + ':I' + str(fila_pago + 1))
    ws['G' + str(fila_pago + 1)].alignment = Alignment(horizontal="center")
    ws['G' + str(fila_pago + 1)].border = Border(bottom=Side(border_style="thin"))
    ws['G' + str(fila_pago + 1)] = ''

    ws.merge_cells('E' + str(fila_pago + 2) + ':F' + str(fila_pago + 2))
    ws['E' + str(fila_pago + 2)] = 'NÚMERO DE CTA:'
    ws.merge_cells('G' + str(fila_pago + 2) + ':I' + str(fila_pago + 2))
    ws['G' + str(fila_pago + 2)].alignment = Alignment(horizontal="center")
    ws['G' + str(fila_pago + 2)].border = Border(bottom=Side(border_style="thin"))
    ws['G' + str(fila_pago + 2)] = ''

    ws.merge_cells('E' + str(fila_pago + 3) + ':F' + str(fila_pago + 3))
    ws['E' + str(fila_pago + 3)] = 'TIPO DE CUENTA'
    ws.merge_cells('G' + str(fila_pago + 3) + ':I' + str(fila_pago + 3))
    ws['G' + str(fila_pago + 3)].alignment = Alignment(horizontal="center")
    ws['G' + str(fila_pago + 3)].border = Border(bottom=Side(border_style="thin"))
    ws['G' + str(fila_pago + 3)] = ''

    ws.merge_cells('E' + str(fila_pago + 4) + ':F' + str(fila_pago + 4))
    ws['E' + str(fila_pago + 4)] = 'MONEDA'
    ws.merge_cells('G' + str(fila_pago + 4) + ':I' + str(fila_pago + 4))
    ws['G' + str(fila_pago + 4)].alignment = Alignment(horizontal="center")
    ws['G' + str(fila_pago + 4)].border = Border(bottom=Side(border_style="thin"))
    ws['G' + str(fila_pago + 4)] = ''

    ws.merge_cells('E' + str(fila_pago + 5) + ':F' + str(fila_pago + 5))
    ws['E' + str(fila_pago + 5)] = 'CCI'
    ws.merge_cells('G' + str(fila_pago + 5) + ':I' + str(fila_pago + 5))
    ws['G' + str(fila_pago + 5)].alignment = Alignment(horizontal="center")
    ws['G' + str(fila_pago + 5)].border = Border(bottom=Side(border_style="thin"))
    ws['G' + str(fila_pago + 5)] = ''

    fila_firmas = fila_pago + 11
    ws.merge_cells('C' + str(fila_firmas) + ':E' + str(fila_firmas))
    ws['C' + str(fila_firmas)].alignment = Alignment(horizontal="center")
    ws['C' + str(fila_firmas)].border = Border(top=Side(border_style="thin"))
    ws['C' + str(fila_firmas)] = 'RESPONSABLE'
    ws.merge_cells('G' + str(fila_firmas) + ':I' + str(fila_firmas))
    ws['G' + str(fila_firmas)].alignment = Alignment(horizontal="center")
    ws['G' + str(fila_firmas)].border = Border(top=Side(border_style="thin"))
    ws['G' + str(fila_firmas)] = 'APROBADO POR'
    return wb
