# -*- coding: utf-8 -*-
import math
from reportlab.lib.pagesizes import letter, A4, landscape
from reportlab.platypus import SimpleDocTemplate, Paragraph, Image, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY
from reportlab.platypus import Table
from reportlab.lib import colors
from reportlab.lib.units import cm
from reportlab.platypus.flowables import Spacer, PageBreak
from django.conf import settings
import os
from io import BytesIO
from almacen.models import MovementDetail, Kardex
from tambox.config import company, administration_office, logistics
from productos.models import Product, ProductGroup
from openpyxl.styles import Alignment
from openpyxl.styles import Border
from openpyxl.styles import Font
from openpyxl.styles import PatternFill
from openpyxl.styles import Side
from openpyxl import Workbook
from django.core.exceptions import ObjectDoesNotExist


def initial_kardex_of(report, product, warehouse, start_date):
    """Saldo inicial de un producto: el ultimo kardex anterior a `start_date`.

    Los informes que recorren el catalogo precargan el lote entero en
    `report.kardex_iniciales` (una sola consulta); los que exportan un solo
    producto no lo hacen y aqui se consulta ese producto. Antes cada row
    lanzaba un `latest('operation_date')`, que ademas revienta con
    MultipleObjectsReturned si dos movimientos comparten date.
    """
    from tambox.dates import aware

    start_date = aware(start_date)
    iniciales = getattr(report, 'kardex_iniciales', None)
    if iniciales is None:
        return (Kardex.objects.filter(product=product, warehouse=warehouse,
                                      operation_date__lt=start_date)
                .order_by('-operation_date', '-pk')
                .first())
    return iniciales.get(product.pk)


def kardex_for_period(report, objeto, warehouse, start_date, end_date, by_group=False):
    """Kardex del periodo, con sus totales, del lote que el informe precargo.

    Los informes que recorren el catalogo llenan `report.kardex_batch` -o
    `kardex_batch_groups`- con dos consultas para todo el lote; los que exportan
    un solo producto lo dejan vacio y aqui se resuelve ese producto, que es lo
    que hacian todos antes. Un producto sin movimientos en el periodo no tiene
    clave en el lote, y su valor es el mismo que devolvia `get_kardex()`.
    """
    batch = getattr(report, 'kardex_batch_groups' if by_group else 'kardex_batch', None)
    if batch is None:
        return objeto.get_kardex(warehouse, start_date, end_date)
    return batch.get(objeto.pk, ([], 0, 0, 0, 0))


class MovementReport():

    def __init__(self, pagesize, movement):
        self.movement = movement
        self.buffer = BytesIO()
        if pagesize == 'A4':
            self.pagesize = A4
        elif pagesize == 'Letter':
            self.pagesize = letter
        self.width, self.height = self.pagesize

    def header_table(self, styles):
        movement = self.movement
        sp = ParagraphStyle('parrafos',
                            alignment=TA_CENTER,
                            fontSize=14,
                            fontName="Times-Roman")
        try:
            image_file = os.path.join(settings.MEDIA_ROOT, str(company().logo))
            image = Image(image_file, width=90, height=50, hAlign='LEFT')
        except Exception:
            image = Paragraph(u"LOGO", sp)

        if movement.movement_type.increases:
            nota = Paragraph(u"NOTA DE INGRESO N°", sp)
        else:
            nota = Paragraph(u"NOTA DE SALIDA N°", sp)
        movement_id = Paragraph(movement.movement_id, sp)
        date = Paragraph("FECHA: " + movement.operation_date.strftime('%d/%m/%y'), sp)
        encabezado = [[image, nota, date],
                      ['', movement_id, '']
                      ]
        header_table = Table(encabezado, colWidths=[4 * cm, 9 * cm, 6 * cm])
        header_table.setStyle(TableStyle(
            [
                ('VALIGN', (0, 0), (2, 0), 'CENTER'),
                ('VALIGN', (1, 1), (2, 1), 'TOP'),
                ('SPAN', (0, 0), (0, 1)),
            ]
        ))
        return header_table

    def data_table(self, styles):
        movement = self.movement
        izquierda = ParagraphStyle('parrafos',
                                   alignment=TA_LEFT,
                                   fontSize=10,
                                   fontName="Times-Roman")
        try:
            if movement.reference.quotation is not None:
                supplier = Paragraph(u"PROVEEDOR: " + movement.reference.quotation.supplier.business_name,
                                      izquierda)
            else:
                supplier = Paragraph(u"PROVEEDOR: " + movement.reference.supplier.business_name, izquierda)
        except (ObjectDoesNotExist, AttributeError):
            supplier = Paragraph(u"PROVEEDOR:", izquierda)
        operacion = Paragraph(u"OPERACIÓN: " + movement.movement_type.description, izquierda)
        warehouse = Paragraph(u"ALMACÉN: " + movement.warehouse.code + "-" + movement.warehouse.description, izquierda)
        try:
            purchase_order = Paragraph(u"ORDEN DE COMPRA: " + movement.reference.code, izquierda)
        except (ObjectDoesNotExist, AttributeError):
            purchase_order = Paragraph(u"REFERENCIA: -", izquierda)
        try:
            document = Paragraph(
                u"DOCUMENTO: " + movement.document_type.description + " SERIE:" + movement.series + u" NÚMERO:" + movement.number,
                izquierda)
        except (ObjectDoesNotExist, TypeError):
            document = ""
        try:
            order = Paragraph(u"PEDIDO: " + movement.order.code, izquierda)
        except (ObjectDoesNotExist, AttributeError):
            order = ""
        encabezado = [[operacion, ''],
                      [warehouse, ''],
                      [supplier, ''],
                      [purchase_order, ''],
                      [document, ''],
                      [order, '']]
        data_table = Table(encabezado, colWidths=[11 * cm, 9 * cm])
        data_table.setStyle(TableStyle(
            [

            ]
        ))
        return data_table

    def detail_table(self):
        movement = self.movement
        encabezados = ['Item', 'Cantidad', 'Unidad', u'Descripción', 'Precio', 'Total']
        details = MovementDetail.objects.filter(movement=movement).order_by('pk')
        sp = ParagraphStyle('parrafos')
        sp.alignment = TA_JUSTIFY
        sp.fontSize = 8
        sp.fontName = "Times-Roman"
        detail_list = []
        for detail in details:
            product_tuple = [str(detail.line_number),
                              format(detail.quantity, '.5f'),
                              str(detail.product.unit_of_measure.code),
                              detail.product.description,
                              format(detail.price, '.5f'),
                              format(detail.amount, '.5f')]
            detail_list.append(product_tuple)
        detail_table = Table([encabezados] + detail_list,
                              colWidths=[1.5 * cm, 2.5 * cm, 1.5 * cm, 10 * cm, 2 * cm, 2.5 * cm])
        style = TableStyle(
            [
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('FONTSIZE', (0, 0), (-1, -1), 8),
                ('ALIGN', (4, 0), (-1, -1), 'RIGHT'),
            ]
        )
        detail_table.setStyle(style)
        return detail_table

    def total_table(self):
        movement = self.movement
        izquierda = ParagraphStyle('parrafos',
                                   alignment=TA_LEFT,
                                   fontSize=10,
                                   fontName="Times-Roman")

        total_text = Paragraph("Total: ", izquierda)
        total = Paragraph(str(round(movement.total, 2)), izquierda)
        total = [['', total_text, total]]
        total_table = Table(total, colWidths=[15.5 * cm, 2 * cm, 2.5 * cm])
        total_table.setStyle(TableStyle(
            [
                ('GRID', (2, 0), (2, 0), 1, colors.black),
                ('FONTSIZE', (0, 0), (-1, -1), 8),
                ('ALIGN', (0, 0), (-1, -1), 'RIGHT'),
            ]
        ))
        return total_table

    def notes_table(self):
        movement = self.movement
        p = ParagraphStyle('parrafos',
                           alignment=TA_JUSTIFY,
                           fontSize=8,
                           fontName="Times-Roman")
        obs = Paragraph("OBSERVACIONES: " + movement.notes, p)
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

    def signatures_table(self):
        movement = self.movement
        izquierda = ParagraphStyle('parrafos',
                                   alignment=TA_CENTER,
                                   fontSize=8,
                                   fontName="Times-Roman")
        administration_office_name = Paragraph(administration_office().name, izquierda)
        logistics_office_name = Paragraph(logistics().name, izquierda)
        if movement.movement_type.increases:
            total = [[administration_office_name, '', logistics_office_name]]
            signatures_table = Table(total, colWidths=[7 * cm, 4 * cm, 7 * cm])
            signatures_table.setStyle(TableStyle(
                [
                    ("LINEABOVE", (0, 0), (0, 0), 1, colors.black),
                    ("LINEABOVE", (2, 0), (2, 0), 1, colors.black),
                    ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ]
            ))
        else:
            requester = Paragraph('SOLICITANTE', izquierda)
            total = [[administration_office_name, '', logistics_office_name, '', requester]]
            signatures_table = Table(total, colWidths=[5 * cm, 1 * cm, 5 * cm, 1 * cm, 5 * cm])
            signatures_table.setStyle(TableStyle(
                [
                    ("LINEABOVE", (0, 0), (0, 0), 1, colors.black),
                    ("LINEABOVE", (2, 0), (2, 0), 1, colors.black),
                    ("LINEABOVE", (4, 0), (4, 0), 1, colors.black),
                    # ("LINEABOVE", (2,0), (2,0), 1, colors.black),
                    ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ]
            ))

        return signatures_table

    def footer(self, canvas, doc):
        canvas.saveState()
        canvas.setFont('Times-Roman', 10)
        canvas.drawCentredString(300, 20, company().address())
        canvas.restoreState()

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
        elements.append(self.detail_table())
        elements.append(Spacer(1, 0.25 * cm))
        elements.append(self.total_table())
        elements.append(Spacer(1, 0.25 * cm))
        elements.append(self.notes_table())
        elements.append(Spacer(1, 4 * cm))
        elements.append(self.signatures_table())
        doc.build(elements, onFirstPage=self.footer, onLaterPages=self.footer)
        pdf = buffer.getvalue()
        buffer.close()
        return pdf


class KardexPdfReport():

    def __init__(self, pagesize, start_date, end_date, warehouse, groups):
        self.start_date = start_date
        self.end_date = end_date
        self.warehouse = warehouse
        self.groups = groups
        self.total_pages = 0
        self.buffer = BytesIO()
        if pagesize == 'A4':
            self.pagesize = landscape(A4)
        elif pagesize == 'Letter':
            self.pagesize = letter
        self.width, self.height = self.pagesize

    def header_table(self, valued):
        sp = ParagraphStyle('parrafos',
                            alignment=TA_CENTER,
                            fontSize=14,
                            fontName="Times-Roman")
        try:
            image_file = os.path.join(settings.MEDIA_ROOT, str(company().logo))
            image = Image(image_file, width=90, height=50, hAlign='LEFT')
        except Exception:
            image = Paragraph(u"LOGO", sp)
        if valued:
            titulo = Paragraph(u"REGISTRO DEL INVENTARIO PERMANENTE VALORIZADO", sp)
        else:
            titulo = Paragraph(u"REGISTRO DEL INVENTARIO PERMANENTE EN UNIDADES FÍSICAS", sp)

        encabezado = [[image, titulo]]
        header_table = Table(encabezado, colWidths=[2 * cm, 23 * cm])
        return header_table

    def consolidated_header_table(self, groups):
        sp = ParagraphStyle('parrafos',
                            alignment=TA_CENTER,
                            fontSize=14,
                            fontName="Times-Roman")
        try:
            image_file = os.path.join(settings.MEDIA_ROOT, str(company().logo))
            image = Image(image_file, width=90, height=50, hAlign='LEFT')
        except Exception:
            image = Paragraph(u"LOGO", sp)
        if groups:
            titulo = Paragraph(u"RESUMEN MENSUAL DE ALMACÉN POR GRUPOS Y CUENTAS", sp)
        else:
            titulo = Paragraph(u"RESUMEN MENSUAL DE ALMACÉN POR PRODUCTOS", sp)

        encabezado = [[image, titulo]]
        header_table = Table(encabezado, colWidths=[2 * cm, 23 * cm])
        style = TableStyle(
            [
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ]
        )
        header_table.setStyle(style)
        return header_table

    def physical_units_detail_table(self, product, start_date, end_date, warehouse):
        table = []
        encab_prim = [u"DOCUMENTO DE TRASLADO, COMPROBANTE DE PAGO,\n DOCUMENTO INTERNO O SIMILAR",
                      "",
                      "",
                      "",
                      u"TIPO DE \n OPERACIÓN \n (TABLA 12)",
                      u"ENTRADAS",
                      u"SALIDAS",
                      u"SALDO FINAL"]
        table.append(encab_prim)
        encab_seg = ["FECHA", "TIPO (TABLA 10)", "SERIE", "NÚMERO", "", "", "", ""]
        table.append(encab_seg)
        try:
            kardex_inicial = initial_kardex_of(self, product, warehouse, start_date)
            opening_quantity = kardex_inicial.total_quantity
        except AttributeError:
            opening_quantity = 0
        opening_balance = [start_date.strftime('%d/%m/%Y'), '00', 'SALDO', 'INICIAL', '16', format(0, '.2f'), format(0, '.2f'),
                         format(opening_quantity, '.2f')]
        total_quantity = opening_quantity
        table.append(opening_balance)
        listado_kardex, in_quantity, in_amount, out_quantity, out_amount = kardex_for_period(
            self, product, warehouse, start_date, end_date)

        for kardex in listado_kardex:
            try:
                document_type = kardex.movement.document_type.sunat_code
            except ObjectDoesNotExist:
                document_type = '-'
            try:
                movement_type = kardex.movement.movement_type.sunat_code
            except ObjectDoesNotExist:
                movement_type = "-"

            total_quantity = kardex.total_quantity

            table.append([kardex.operation_date.strftime('%d/%m/%Y'),
                          document_type,
                          kardex.movement.series,
                          kardex.movement.number,
                          movement_type,
                          format(kardex.in_quantity, '.2f'),
                          format(kardex.out_quantity, '.2f'),
                          format(total_quantity, '.2f')])
        totales = ['', '', '', '', "TOTALES", format(in_quantity, '.2f'), format(out_quantity, '.2f'),
                   format(total_quantity, '.2f')]
        table.append(totales)

        self.total_pages += 1;
        total_product_records = len(listado_kardex) + 2
        if total_product_records > 11:
            self.total_pages += int(math.ceil((total_product_records - 11) / 21.0))

        detail_table = Table(table, repeatRows=2,
                              colWidths=[3 * cm, 4 * cm, 3 * cm, 3 * cm, 3 * cm, 3.5 * cm, 3.5 * cm, 3.5 * cm])
        style = TableStyle(
            [
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('TEXTFONT', (0, 1), (-1, 1), 'Times-Roman'),
                ('ALIGN', (5, 1), (7, -1), 'RIGHT'),
                ('ALIGN', (0, 0), (7, 1), 'CENTER'),
                ('VALIGN', (0, 0), (7, 1), 'MIDDLE'),
                ('FONTSIZE', (0, 0), (-1, -1), 12),
                ('SPAN', (0, 0), (3, 0)),
                ('SPAN', (4, 0), (4, 1)),
                ('SPAN', (5, 0), (5, 1)),
                ('SPAN', (6, 0), (6, 1)),
                ('SPAN', (7, 0), (7, 1)),
            ]
        )
        detail_table.setStyle(style)
        return detail_table

    def consolidated_product_detail_table(self, productos):
        warehouse = self.warehouse
        start_date = self.start_date
        end_date = self.end_date
        table = []
        encabezado1 = ["CODIGO", u"DENOMINACIÓN", u"UNIDAD", u"CUENTA", u"SALDO INICIAL", u"", u"INGRESOS", u"",
                       u"SALIDAS", u"", u"SALDO",
                       u""]
        encabezado2 = [u"", u"", u"", u"", u"CANTIDAD", u"VALOR", u"CANTIDAD", u"VALOR",
                       u"CANTIDAD", u"VALOR", u"CANTIDAD", u"VALOR"]
        table.append(encabezado1)
        table.append(encabezado2)
        total_opening_quantity = 0
        total_opening_amount = 0
        total_in_quantity = 0
        total_in_amount = 0
        total_out_quantity = 0
        total_out_amount = 0
        total_total_quantity = 0
        total_total_amount = 0
        self.total_pages = int(math.ceil(productos.count() / 22.0))
        iniciales = Kardex.last_by_product(productos, before=start_date, warehouse=warehouse)
        self.kardex_batch = Product.kardex_by_batch(productos, warehouse, start_date, end_date)
        for product in productos:
            try:
                kardex_inicial = iniciales.get(product.pk)
                opening_quantity = kardex_inicial.total_quantity
                opening_amount = kardex_inicial.total_amount
            except AttributeError:
                opening_quantity = 0
                opening_amount = 0

            listado_kardex, in_quantity, in_amount, out_quantity, out_amount = kardex_for_period(
                self, product, warehouse, start_date, end_date)
            total_quantity = opening_quantity + in_quantity - out_quantity
            total_amount = opening_amount + in_amount - out_amount

            total_opening_quantity += opening_quantity
            total_opening_amount += opening_amount
            total_in_quantity += in_quantity
            total_in_amount += in_amount
            total_out_quantity += out_quantity
            total_out_amount += out_amount
            total_total_quantity += total_quantity
            total_total_amount += total_amount

            temp_opening_amount = format(opening_amount, '.3f')
            if temp_opening_amount == '-0.000':
                opening_amount = format(abs(opening_amount), '.3f')
            else:
                opening_amount = format(opening_amount, '.3f')

            temp_total_amount = format(total_amount, '.3f')
            if temp_total_amount == '-0.000':
                total_amount = format(abs(total_amount), '.3f')
            else:
                total_amount = format(total_amount, '.3f')

            registro = [product.code,
                        product.description,
                        product.unit_of_measure.description,
                        product.product_group.account,
                        format(opening_quantity, '.3f'),
                        opening_amount,
                        format(in_quantity, '.3f'),
                        format(in_amount, '.3f'),
                        format(out_quantity, '.3f'),
                        format(out_amount, '.3f'),
                        format(total_quantity, '.3f'),
                        total_amount]
            table.append(registro)

        totales = ["", "", "", "TOTALES",
                   format(total_opening_quantity, '.3f'), format(total_opening_amount, '.3f'),
                   format(total_in_quantity, '.3f'), format(total_in_amount, '.3f'),
                   format(total_out_quantity, '.3f'), format(total_out_amount, '.3f'),
                   format(total_total_quantity, '.3f'), format(total_total_amount, '.3f')]
        table.append(totales)
        detail_table = Table(table,
                              repeatRows=2)  # ,colWidths=[2 * cm, 7 * cm, 2.2 * cm, 1.5 * cm,2.3 * cm, 2.3 * cm,2.3 * cm, 2.4 * cm,2.3 * cm, 2.5 * cm])
        style = TableStyle(
            [
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('ALIGN', (0, 0), (11, 1), 'CENTER'),
                ('ALIGN', (4, 2), (11, -1), 'RIGHT'),
                ('TEXTFONT', (0, 0), (-1, -1), 'Times-Roman'),
                ('FONTSIZE', (0, 0), (-1, -1), 6.5),
                ('SPAN', (0, 0), (0, 1)),
                ('SPAN', (1, 0), (1, 1)),
                ('SPAN', (1, 0), (1, 1)),
                ('SPAN', (2, 0), (2, 1)),
                ('SPAN', (3, 0), (3, 1)),
                ('SPAN', (4, 0), (5, 0)),
                ('SPAN', (6, 0), (7, 0)),
                ('SPAN', (8, 0), (9, 0)),
                ('SPAN', (10, 0), (11, 0)),
            ]
        )
        detail_table.setStyle(style)
        return detail_table

    def consolidated_group_detail_table(self, groups):
        warehouse = self.warehouse
        start_date = self.start_date
        end_date = self.end_date
        table = []
        encabezado1 = ["CODIGO", "NOMBRE", "CUENTA", u"SALDO INICIAL", u"", u"INGRESOS", u"", u"SALIDAS", u"", u"SALDO",
                       u""]
        encabezado2 = [u"", u"", u"", u"CANTIDAD", u"VALOR", u"CANTIDAD", u"VALOR",
                       u"CANTIDAD", u"VALOR", u"CANTIDAD", u"VALOR"]
        table.append(encabezado1)
        table.append(encabezado2)
        total_opening_quantity = 0
        total_opening_amount = 0
        total_in_quantity = 0
        total_in_amount = 0
        total_out_quantity = 0
        total_out_amount = 0
        total_total_quantity = 0
        total_total_amount = 0
        self.total_pages = int(math.ceil(groups.count() / 22.0))
        self.kardex_batch_groups = ProductGroup.kardex_by_batch(groups, warehouse, start_date, end_date)
        for group in groups:
            opening_quantity = 0
            opening_amount = 0
            productos = Product.objects.filter(product_group=group)
            iniciales = Kardex.last_by_product(productos, before=start_date, warehouse=warehouse)
            for product in productos:
                try:
                    kardex_inicial = iniciales.get(product.pk)
                    opening_quantity_product = kardex_inicial.total_quantity
                    opening_amount_product = kardex_inicial.total_amount
                except AttributeError:
                    opening_quantity_product = 0
                    opening_amount_product = 0
                opening_quantity += opening_quantity_product
                opening_amount += opening_amount_product

            listado_kardex, in_quantity, in_amount, out_quantity, out_amount = kardex_for_period(
                self, group, warehouse, start_date, end_date, by_group=True)
            total_quantity = opening_quantity + in_quantity - out_quantity
            total_amount = opening_amount + in_amount - out_amount

            total_opening_quantity += opening_quantity
            total_opening_amount += opening_amount
            total_in_quantity += in_quantity
            total_in_amount += in_amount
            total_out_quantity += out_quantity
            total_out_amount += out_amount
            total_total_quantity += total_quantity
            total_total_amount += total_amount

            temp_opening_amount = format(opening_amount, '.5f')
            if temp_opening_amount == '-0.00000':
                opening_amount = format(abs(opening_amount), '.5f')
            else:
                opening_amount = format(opening_amount, '.5f')

            temp_total_amount = format(total_amount, '.5f')
            if temp_total_amount == '-0.00000':
                total_amount = format(abs(total_amount), '.5f')
            else:
                total_amount = format(total_amount, '.5f')

            registro = [group.code,
                        group.description,
                        group.account.account_number,
                        format(opening_quantity, '.5f'),
                        opening_amount,
                        format(in_quantity, '.5f'),
                        format(in_amount, '.5f'),
                        format(out_quantity, '.5f'),
                        format(out_amount, '.5f'),
                        format(total_quantity, '.5f'),
                        total_amount]
            table.append(registro)

        totales = ["", "", "TOTALES",
                   format(total_opening_quantity, '.5f'), format(total_opening_amount, '.5f'),
                   format(total_in_quantity, '.5f'), format(total_in_amount, '.5f'),
                   format(total_out_quantity, '.5f'), format(total_out_amount, '.5f'),
                   format(total_total_quantity, '.5f'), format(total_total_amount, '.5f')]
        table.append(totales)
        detail_table = Table(table, repeatRows=2,
                              colWidths=[1.4 * cm, 7 * cm, 1.8 * cm, 2.2 * cm, 2.3 * cm, 2.3 * cm, 2.3 * cm, 2.3 * cm,
                                         2.4 * cm, 2.3 * cm, 2.5 * cm])
        style = TableStyle(
            [
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('ALIGN', (0, 0), (10, 1), 'CENTER'),
                ('ALIGN', (3, 2), (10, -1), 'RIGHT'),
                ('TEXTFONT', (0, 0), (-1, -1), 'Times-Roman'),
                ('FONTSIZE', (0, 0), (-1, -1), 8),
                ('SPAN', (0, 0), (0, 1)),
                ('SPAN', (1, 0), (1, 1)),
                ('SPAN', (2, 0), (2, 1)),
                ('SPAN', (3, 0), (4, 0)),
                ('SPAN', (5, 0), (6, 0)),
                ('SPAN', (7, 0), (8, 0)),
                ('SPAN', (9, 0), (10, 0)),
            ]
        )
        detail_table.setStyle(style)
        return detail_table

    def valued_detail_table(self, product, start_date, end_date, warehouse):
        table = []
        encab_prim = [u"DOCUMENTO DE TRASLADO, COMPROBANTE DE PAGO,\n DOCUMENTO INTERNO O SIMILAR",
                      "", "", "",
                      u"TIPO DE \n OPERACIÓN \n (TABLA 12)",
                      u"ENTRADAS", "", "",
                      u"SALIDAS", "", "",
                      u"SALDO FINAL", "", ""]
        table.append(encab_prim)
        encab_seg = ["", "", "", "", "",
                     "CANTIDAD", "COSTO\nUNITARIO", "TOTAL",
                     "CANTIDAD", "COSTO\nUNITARIO", "TOTAL",
                     "CANTIDAD", "COSTO\nUNITARIO", "TOTAL"]
        table.append(encab_seg)
        encab_terc = ["FECHA", "TIPO\n(TABLA 10)", "SERIE", "NÚMERO",
                      "", "", "",
                      "", "", "",
                      "", "", ""]
        table.append(encab_terc)

        try:
            kardex_inicial = initial_kardex_of(self, product, warehouse, start_date)
            opening_quantity = kardex_inicial.total_quantity
            opening_price = kardex_inicial.total_price
            opening_amount = kardex_inicial.total_amount
        except AttributeError:
            opening_quantity = 0
            opening_price = 0
            opening_amount = 0

        opening_quantity = format(opening_quantity, '.2f')
        opening_price = format(opening_price, '.2f')
        temp_opening_amount = format(opening_amount, '.2f')
        if temp_opening_amount == '-0.00':
            opening_amount = format(abs(opening_amount), '.2f')
        else:
            opening_amount = format(opening_amount, '.2f')

        opening_balance = [start_date.strftime('%d/%m/%Y'), '00', 'SALDO', 'INICIAL', '16',
                         format(0, '.2f'), format(0, '.2f'), format(0, '.2f'),
                         format(0, '.2f'), format(0, '.2f'), format(0, '.2f'),
                         opening_quantity, opening_price, opening_amount]
        table.append(opening_balance)

        total_quantity = opening_quantity
        total_price = opening_price
        total_amount = opening_amount

        listado_kardex, in_quantity, in_amount, out_quantity, out_amount = kardex_for_period(
            self, product, warehouse, start_date, end_date)

        for kardex in listado_kardex:
            try:
                document_type = kardex.movement.document_type.sunat_code
            except ObjectDoesNotExist:
                document_type = '-'
            try:
                movement_type = kardex.movement.movement_type.sunat_code
            except ObjectDoesNotExist:
                movement_type = "-"

            total_quantity = format(kardex.total_quantity, '.2f')
            total_price = format(kardex.total_price, '.2f')
            total_amount = format(kardex.total_amount, '.2f')
            if total_amount == '-0.00':
                total_amount = format(abs(kardex.total_amount), '.2f')

            table.append([kardex.operation_date.strftime('%d/%m/%Y'),
                          document_type,
                          kardex.movement.series,
                          kardex.movement.number,
                          movement_type,
                          format(kardex.in_quantity, '.2f'),
                          format(kardex.in_price, '.2f'),
                          format(kardex.in_amount, '.2f'),
                          format(kardex.out_quantity, '.2f'),
                          format(kardex.out_price, '.2f'),
                          format(kardex.out_amount, '.2f'),
                          total_quantity,
                          total_price,
                          total_amount])

        totales = ['', '', '', '', "TOTALES",
                   format(in_quantity, '.2f'), "", format(in_amount, '.2f'),
                   format(out_quantity, '.2f'), "", format(out_amount, '.2f'),
                   total_quantity, total_price, total_amount]
        table.append(totales)

        self.total_pages += 1;
        total_product_records = len(listado_kardex) + 2
        if total_product_records > 10:
            self.total_pages += int(math.ceil((total_product_records - 10) / 20.0))

        detail_table = Table(table, repeatRows=3)
        style = TableStyle(
            [
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('TEXTFONT', (0, 1), (-1, 1), 'Times-Roman'),
                ('ALIGN', (5, 1), (13, -1), 'RIGHT'),
                ('ALIGN', (0, 0), (13, 2), 'CENTER'),
                ('VALIGN', (0, 0), (13, 2), 'MIDDLE'),
                ('FONTSIZE', (0, 0), (-1, -1), 8.5),
                ('SPAN', (0, 0), (3, 1)),
                ('SPAN', (4, 0), (4, 2)),
                ('SPAN', (5, 0), (7, 0)),
                ('SPAN', (8, 0), (10, 0)),
                ('SPAN', (11, 0), (13, 0)),
                ('SPAN', (5, 1), (5, 2)),
                ('SPAN', (6, 1), (6, 2)),
                ('SPAN', (7, 1), (7, 2)),
                ('SPAN', (8, 1), (8, 2)),
                ('SPAN', (9, 1), (9, 2)),
                ('SPAN', (10, 1), (10, 2)),
                ('SPAN', (11, 1), (11, 2)),
                ('SPAN', (12, 1), (12, 2)),
                ('SPAN', (13, 1), (13, 2)),
            ]
        )
        detail_table.setStyle(style)
        return detail_table

    def render_sunat_physical_units_product_format(self, product):
        start_date = self.start_date
        end_date = self.end_date
        warehouse = self.warehouse
        buffer = self.buffer
        self.valued = False
        izquierda = ParagraphStyle('parrafos',
                                   alignment=TA_LEFT,
                                   fontSize=11,
                                   fontName="Times-Roman")
        doc = SimpleDocTemplate(buffer,
                                rightMargin=50,
                                leftMargin=50,
                                topMargin=100,
                                bottomMargin=50,
                                pagesize=self.pagesize)

        elements = []
        periodo = Paragraph("PERIODO: " + start_date.strftime('%d/%m/%Y') + ' - ' + end_date.strftime('%d/%m/%Y'), izquierda)
        elements.append(periodo)
        elements.append(Spacer(1, 0.25 * cm))
        tax_id = Paragraph(u"RUC:" + company().tax_id, izquierda)
        elements.append(tax_id)
        elements.append(Spacer(1, 0.25 * cm))
        business_name = Paragraph(u"APELLIDOS Y NOMBRES, DENOMINACIÓN O RAZÓN SOCIAL: " + company().business_name,
                                 izquierda)
        elements.append(business_name)
        elements.append(Spacer(1, 0.25 * cm))
        address = Paragraph(u"ESTABLECIMIENTO (1): " + company().address(), izquierda)
        elements.append(address)
        elements.append(Spacer(1, 0.25 * cm))
        code = Paragraph(u"CÓDIGO DE LA EXISTENCIA: " + product.code, izquierda)
        elements.append(code)
        elements.append(Spacer(1, 0.25 * cm))
        type = Paragraph(u"TIPO: B - EXISTENCIA", izquierda)
        """type = Paragraph(u"TIPO (TABLA 5): " + product.stock_type.sunat_code + " - " + product.stock_type.description,
                         izquierda)"""
        elements.append(type)
        elements.append(Spacer(1, 0.25 * cm))
        description = Paragraph(u"DESCRIPCIÓN: " + product.description, izquierda)
        elements.append(description)
        elements.append(Spacer(1, 0.25 * cm))
        unit = Paragraph(
            u"CÓDIGO DE LA UNIDAD DE MEDIDA (TABLA 6): " + product.unit_of_measure.sunat_code + " - " + product.unit_of_measure.description,
            izquierda)
        elements.append(unit)
        elements.append(Spacer(1, 0.25 * cm))
        unit = Paragraph(u"MÉTODO DE VALUACIÓN: PEPS",
                           izquierda)
        elements.append(unit)
        elements.append(Spacer(1, 0.5 * cm))
        elements.append(self.physical_units_detail_table(product, start_date, end_date, warehouse))
        doc.build(elements, onFirstPage=self._header, onLaterPages=self._header)
        pdf = buffer.getvalue()
        buffer.close()
        return pdf

    def render_sunat_valued_product_format(self, product):
        start_date = self.start_date
        end_date = self.end_date
        warehouse = self.warehouse
        buffer = self.buffer
        self.valued = True
        izquierda = ParagraphStyle('parrafos',
                                   alignment=TA_LEFT,
                                   fontSize=12,
                                   fontName="Times-Roman")
        doc = SimpleDocTemplate(buffer,
                                rightMargin=50,
                                leftMargin=50,
                                topMargin=100,
                                bottomMargin=50,
                                pagesize=self.pagesize)

        elements = []
        periodo = Paragraph("PERIODO: " + start_date.strftime('%d/%m/%Y') + ' - ' + end_date.strftime('%d/%m/%Y'), izquierda)
        elements.append(periodo)
        elements.append(Spacer(1, 0.25 * cm))
        tax_id = Paragraph(u"RUC:" + company().tax_id, izquierda)
        elements.append(tax_id)
        elements.append(Spacer(1, 0.25 * cm))
        business_name = Paragraph(u"APELLIDOS Y NOMBRES, DENOMINACIÓN O RAZÓN SOCIAL: " + company().business_name,
                                 izquierda)
        elements.append(business_name)
        elements.append(Spacer(1, 0.25 * cm))
        address = Paragraph(u"ESTABLECIMIENTO (1): " + company().address(), izquierda)
        elements.append(address)
        elements.append(Spacer(1, 0.25 * cm))
        code = Paragraph(u"CÓDIGO DE LA EXISTENCIA: " + product.code, izquierda)
        elements.append(code)
        elements.append(Spacer(1, 0.25 * cm))
        type = Paragraph(u"TIPO: B - EXISTENCIA", izquierda)
        """type = Paragraph(u"TIPO (TABLA 5): " + product.stock_type.sunat_code + " - " + product.stock_type.description,
                         izquierda)"""
        elements.append(type)
        elements.append(Spacer(1, 0.25 * cm))
        description = Paragraph(u"DESCRIPCIÓN: " + product.description, izquierda)
        elements.append(description)
        elements.append(Spacer(1, 0.25 * cm))
        unit = Paragraph(
            u"CÓDIGO DE LA UNIDAD DE MEDIDA (TABLA 6): " + product.unit_of_measure.sunat_code + " - " + product.unit_of_measure.description,
            izquierda)
        elements.append(unit)
        elements.append(Spacer(1, 0.25 * cm))
        unit = Paragraph(u"MÉTODO DE VALUACIÓN: PEPS",
                           izquierda)
        elements.append(unit)
        elements.append(Spacer(1, 0.5 * cm))
        elements.append(self.valued_detail_table(product, start_date, end_date, warehouse))
        doc.build(elements, onFirstPage=self._header, onLaterPages=self._header)
        pdf = buffer.getvalue()
        buffer.close()
        return pdf

    def render_sunat_physical_units_all_format(self):
        start_date = self.start_date
        end_date = self.end_date
        warehouse = self.warehouse
        buffer = self.buffer
        self.valued = False
        izquierda = ParagraphStyle('parrafos',
                                   alignment=TA_LEFT,
                                   fontSize=12,
                                   fontName="Times-Roman")
        doc = SimpleDocTemplate(buffer,
                                rightMargin=50,
                                leftMargin=50,
                                topMargin=100,
                                bottomMargin=50,
                                pagesize=self.pagesize)

        elements = []
        product_kardex = Kardex.objects.exclude(in_quantity=0, out_quantity=0).order_by().values(
            'product').distinct()
        productos = Product.objects.filter(pk__in=product_kardex).order_by(
            'description').select_related('unit_of_measure', 'stock_type')
        self.kardex_iniciales = Kardex.last_by_product(productos, before=start_date, warehouse=warehouse)
        self.kardex_batch = Product.kardex_by_batch(productos, warehouse, start_date, end_date)
        for product in productos:
            periodo = Paragraph("PERIODO: " + start_date.strftime('%d/%m/%Y') + ' - ' + end_date.strftime('%d/%m/%Y'),
                                izquierda)
            elements.append(periodo)
            elements.append(Spacer(1, 0.25 * cm))
            tax_id = Paragraph(u"RUC:" + company().tax_id, izquierda)
            elements.append(tax_id)
            elements.append(Spacer(1, 0.25 * cm))
            business_name = Paragraph(u"APELLIDOS Y NOMBRES, DENOMINACIÓN O RAZÓN SOCIAL: " + company().business_name,
                                     izquierda)
            elements.append(business_name)
            elements.append(Spacer(1, 0.25 * cm))
            address = Paragraph(u"ESTABLECIMIENTO (1): " + company().address(), izquierda)
            elements.append(address)
            elements.append(Spacer(1, 0.25 * cm))
            code = Paragraph(u"CÓDIGO DE LA EXISTENCIA: " + product.code, izquierda)
            elements.append(code)
            elements.append(Spacer(1, 0.25 * cm))
            type = Paragraph(u"TIPO: B - EXISTENCIA", izquierda)
            """type = Paragraph(u"TIPO (TABLA 5): " + product.stock_type.sunat_code + " - " + product.stock_type.description,
                             izquierda)"""
            elements.append(type)
            elements.append(Spacer(1, 0.25 * cm))
            description = Paragraph(u"DESCRIPCIÓN: " + product.description, izquierda)
            elements.append(description)
            elements.append(Spacer(1, 0.25 * cm))
            unit = Paragraph(
                u"CÓDIGO DE LA UNIDAD DE MEDIDA (TABLA 6): " + product.unit_of_measure.sunat_code + " - " + product.unit_of_measure.description,
                izquierda)
            elements.append(unit)
            elements.append(Spacer(1, 0.25 * cm))
            unit = Paragraph(u"MÉTODO DE VALUACIÓN: PEPS",
                               izquierda)
            elements.append(unit)
            elements.append(Spacer(1, 0.5 * cm))
            elements.append(self.physical_units_detail_table(product, start_date, end_date, warehouse))
            elements.append(PageBreak())
        doc.build(elements, onFirstPage=self._header, onLaterPages=self._header)
        pdf = buffer.getvalue()
        buffer.close()
        return pdf

    def render_consolidated_products_format(self):
        buffer = self.buffer
        doc = SimpleDocTemplate(buffer,
                                rightMargin=50,
                                leftMargin=50,
                                topMargin=100,
                                bottomMargin=50,
                                pagesize=self.pagesize)

        elements = []
        productos = Product.objects.all().order_by('description')
        elements.append(self.consolidated_product_detail_table(productos))
        doc.build(elements, onFirstPage=self._header_footer, onLaterPages=self._header_footer)
        pdf = buffer.getvalue()
        buffer.close()
        return pdf

    def _header_footer(self, canvas, doc):
        canvas.saveState()
        sp = ParagraphStyle('parrafos',
                            alignment=TA_CENTER,
                            fontSize=14,
                            fontName="Times-Roman")
        try:
            image_file = os.path.join(settings.MEDIA_ROOT, str(company().logo))
            image = Image(image_file, width=90, height=50, hAlign='LEFT')
        except Exception:
            image = Paragraph(u"LOGO", sp)
        company_tax_id = "RUC: " + company().tax_id
        if self.groups:
            titulo = Paragraph(u"RESUMEN MENSUAL DE ALMACÉN POR GRUPOS Y CUENTAS", sp)
        else:
            titulo = Paragraph(u"RESUMEN MENSUAL DE ALMACÉN", sp)
        periodo = "PERIODO: " + self.start_date.strftime('%d/%m/%Y') + ' - ' + self.end_date.strftime('%d/%m/%Y')
        page = u"Página " + str(doc.page) + " de " + str(self.total_pages)
        encabezado = [[image, titulo, page], [company_tax_id, periodo, ""]]
        header_table = Table(encabezado, colWidths=[3 * cm, 20 * cm, 3 * cm])
        style = TableStyle(
            [
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ]
        )
        header_table.setStyle(style)
        header_table.wrapOn(canvas, 50, 510)
        header_table.drawOn(canvas, 50, 510)
        canvas.restoreState()

    def _header(self, canvas, doc):
        canvas.saveState()

        sp = ParagraphStyle('parrafos',
                            alignment=TA_CENTER,
                            fontSize=14,
                            fontName="Times-Roman")
        try:
            image_file = os.path.join(settings.MEDIA_ROOT, str(company().logo))
            image = Image(image_file, width=90, height=50, hAlign='LEFT')
        except Exception:
            image = Paragraph(u"LOGO", sp)
        company_tax_id = "RUC: " + company().tax_id
        if self.valued:
            titulo = Paragraph(u"REGISTRO DEL INVENTARIO PERMANENTE VALORIZADO", sp)
        else:
            titulo = Paragraph(u"REGISTRO DEL INVENTARIO PERMANENTE EN UNIDADES FÍSICAS", sp)
        page = u"Página " + str(doc.page) + " de " + str(self.total_pages)
        encabezado = [[image, titulo, page], [company_tax_id, "", ""]]
        header_table = Table(encabezado, colWidths=[3 * cm, 20 * cm, 3 * cm])
        style = TableStyle(
            [
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ]
        )
        header_table.setStyle(style)
        header_table.wrapOn(canvas, 50, 510)
        header_table.drawOn(canvas, 50, 510)
        canvas.restoreState()

    def render_consolidated_groups_format(self):
        buffer = self.buffer
        doc = SimpleDocTemplate(buffer,
                                rightMargin=50,
                                leftMargin=50,
                                topMargin=100,
                                bottomMargin=50,
                                pagesize=self.pagesize)

        elements = []
        groups = ProductGroup.objects.filter(is_active=True,
                                               contains_products=True).order_by('description')
        elements.append(self.consolidated_group_detail_table(groups))

        doc.build(elements, onFirstPage=self._header_footer, onLaterPages=self._header_footer)
        pdf = buffer.getvalue()
        buffer.close()
        return pdf

    def render_sunat_valued_all_format(self):
        start_date = self.start_date
        end_date = self.end_date
        warehouse = self.warehouse
        buffer = self.buffer
        self.valued = True
        izquierda = ParagraphStyle('parrafos',
                                   alignment=TA_LEFT,
                                   fontSize=12,
                                   fontName="Times-Roman")
        doc = SimpleDocTemplate(buffer,
                                rightMargin=50,
                                leftMargin=50,
                                topMargin=100,
                                bottomMargin=50,
                                pagesize=self.pagesize)

        elements = []
        product_kardex = Kardex.objects.exclude(in_quantity=0,
                                                  out_quantity=0).order_by().values('product').distinct()
        productos = Product.objects.filter(pk__in=product_kardex).order_by(
            'description').select_related('unit_of_measure', 'stock_type')
        self.kardex_iniciales = Kardex.last_by_product(productos, before=start_date, warehouse=warehouse)
        self.kardex_batch = Product.kardex_by_batch(productos, warehouse, start_date, end_date)
        for product in productos:
            periodo = Paragraph("PERIODO: " + start_date.strftime('%d/%m/%Y') + ' - ' + end_date.strftime('%d/%m/%Y'),
                                izquierda)
            elements.append(periodo)
            elements.append(Spacer(1, 0.25 * cm))
            tax_id = Paragraph(u"RUC:" + company().tax_id, izquierda)
            elements.append(tax_id)
            elements.append(Spacer(1, 0.25 * cm))
            business_name = Paragraph(u"APELLIDOS Y NOMBRES, DENOMINACIÓN O RAZÓN SOCIAL: " + company().business_name,
                                     izquierda)
            elements.append(business_name)
            elements.append(Spacer(1, 0.25 * cm))
            address = Paragraph(u"ESTABLECIMIENTO (1): " + company().address(), izquierda)
            elements.append(address)
            elements.append(Spacer(1, 0.25 * cm))
            code = Paragraph(u"CÓDIGO DE LA EXISTENCIA: " + product.code, izquierda)
            elements.append(code)
            elements.append(Spacer(1, 0.25 * cm))
            type = Paragraph(u"TIPO: B - EXISTENCIA", izquierda)
            """type = Paragraph(u"TIPO (TABLA 5): " + product.stock_type.sunat_code + " - " + product.stock_type.description,
                             izquierda)"""
            elements.append(type)
            elements.append(Spacer(1, 0.25 * cm))
            description = Paragraph(u"DESCRIPCIÓN: " + product.description, izquierda)
            elements.append(description)
            elements.append(Spacer(1, 0.25 * cm))
            unit = Paragraph(
                u"CÓDIGO DE LA UNIDAD DE MEDIDA (TABLA 6): " + product.unit_of_measure.sunat_code + " - " + product.unit_of_measure.description,
                izquierda)
            elements.append(unit)
            elements.append(Spacer(1, 0.25 * cm))
            unit = Paragraph(u"MÉTODO DE VALUACIÓN: PEPS",
                               izquierda)
            elements.append(unit)
            elements.append(Spacer(1, 0.5 * cm))
            elements.append(self.valued_detail_table(product, start_date, end_date, warehouse))
            elements.append(PageBreak())
        doc.build(elements, onFirstPage=self._header, onLaterPages=self._header)
        pdf = buffer.getvalue()
        buffer.close()
        return pdf


class KardexExcelReport():

    def get_sunat_physical_units_product(self, product, start_date, end_date, warehouse):
        wb = Workbook()
        ws = wb.active
        thin_border = Border(left=Side(style='thin'),
                             right=Side(style='thin'),
                             top=Side(style='thin'),
                             bottom=Side(style='thin'))
        ws.column_dimensions["C"].width = 15
        ws.column_dimensions["F"].width = 12
        ws.column_dimensions["G"].width = 15
        ws.column_dimensions["H"].width = 15
        ws.column_dimensions["I"].width = 15
        ws.column_dimensions["J"].width = 15
        ws.column_dimensions["K"].width = 15
        ws.column_dimensions["L"].width = 15
        ws.column_dimensions["M"].width = 15
        ws.column_dimensions["N"].width = 15
        ws.column_dimensions["O"].width = 15

        ws['D1'] = u'REGISTRO DEL INVENTARIO PERMANENTE EN UNIDADES FÍSICAS'
        ws.merge_cells('D1:G1')
        ws['B3'] = "PERIODO: " + start_date.strftime('%d/%m/%Y') + ' - ' + end_date.strftime('%d/%m/%Y')
        ws.merge_cells('B3:E3')
        ws['B4'] = u"RUC:" + company().tax_id
        ws.merge_cells('B4:E4')
        ws['B5'] = u"APELLIDOS Y NOMBRES, DENOMINACIÓN O RAZÓN SOCIAL: " + company().business_name
        ws.merge_cells('B5:K5')
        ws['B6'] = u"ESTABLECIMIENTO (1): " + company().address()
        ws.merge_cells('B6:E6')
        ws['B7'] = u"CÓDIGO DE LA EXISTENCIA: " + product.code
        ws.merge_cells('B7:E7')
        ws[
            'B8'] = u"TIPO (TABLA 5): " + product.stock_type.sunat_code + " - " + product.stock_type.description
        ws.merge_cells('B8:G8')
        ws['B9'] = u"DESCRIPCIÓN: " + product.description
        ws.merge_cells('B9:E9')
        ws[
            'B10'] = u"CÓDIGO DE LA UNIDAD DE MEDIDA (TABLA 6): " + product.unit_of_measure.code + " - " + product.unit_of_measure.description
        ws.merge_cells('B10:H10')
        ws['B11'] = u"MÉTODO DE VALUACIÓN: PEPS"
        ws.merge_cells('B11:E11')

        ws['B13'] = u"DOCUMENTO DE TRASLADO, COMPROBANTE DE PAGO,\n DOCUMENTO INTERNO O SIMILAR"
        ws['B13'].border = thin_border
        ws.merge_cells('B13:E14')
        ws['B15'] = u"FECHA"
        ws['B15'].border = thin_border
        ws['C15'] = u"TIPO (TABLA 10)"
        ws['C15'].border = thin_border
        ws['D15'] = u"SERIE"
        ws['D15'].border = thin_border
        ws['E15'] = u"NÚMERO"
        ws['E15'].border = thin_border
        ws['F13'] = u"TIPO DE \n OPERACIÓN \n (TABLA 12)"
        ws['F13'].border = thin_border
        ws.merge_cells('F13:F15')

        ws['G13'] = u"ENTRADAS"
        ws['G13'].border = thin_border
        ws.merge_cells('G13:G15')
        ws['H13'] = u"SALIDAS"
        ws['H13'].border = thin_border
        ws.merge_cells('H13:H15')
        ws['I13'] = u"SALDO FINAL"
        ws['I13'].border = thin_border
        ws.merge_cells('I13:I15')

        try:
            kardex_inicial = initial_kardex_of(self, product, warehouse, start_date)
            opening_quantity = kardex_inicial.total_quantity
        except AttributeError:
            opening_quantity = 0
        cont = 16
        ws.cell(row=cont, column=2).border = thin_border
        ws.cell(row=cont, column=3).value = '00'
        ws.cell(row=cont, column=3).border = thin_border
        ws.cell(row=cont, column=4).value = 'SALDO'
        ws.cell(row=cont, column=4).border = thin_border
        ws.cell(row=cont, column=5).value = 'INICIAL'
        ws.cell(row=cont, column=5).border = thin_border
        ws.cell(row=cont, column=6).value = '16'
        ws.cell(row=cont, column=6).border = thin_border
        ws.cell(row=cont, column=7).value = 0
        ws.cell(row=cont, column=7).number_format = '#.00000'
        ws.cell(row=cont, column=7).border = thin_border
        ws.cell(row=cont, column=8).value = 0
        ws.cell(row=cont, column=8).number_format = '#.00000'
        ws.cell(row=cont, column=8).border = thin_border
        ws.cell(row=cont, column=9).value = opening_quantity
        ws.cell(row=cont, column=9).number_format = '#.00000'
        ws.cell(row=cont, column=9).border = thin_border

        listado_kardex, in_quantity, in_amount, out_quantity, out_amount = kardex_for_period(
            self, product, warehouse, start_date, end_date)
        for kardex in listado_kardex:
            cont = cont + 1
            ws.cell(row=cont, column=2).value = kardex.operation_date.strftime('%d/%m/%Y')
            ws.cell(row=cont, column=2).border = thin_border
            try:
                ws.cell(row=cont, column=3).value = kardex.movement.document_type.sunat_code
            except ObjectDoesNotExist:
                ws.cell(row=cont, column=3).value = '-'
            ws.cell(row=cont, column=3).border = thin_border
            ws.cell(row=cont, column=4).value = kardex.movement.series
            ws.cell(row=cont, column=4).border = thin_border
            ws.cell(row=cont, column=5).value = kardex.movement.number
            ws.cell(row=cont, column=5).border = thin_border
            ws.cell(row=cont, column=6).value = kardex.movement.movement_type.sunat_code
            ws.cell(row=cont, column=6).border = thin_border
            ws.cell(row=cont, column=7).value = kardex.in_quantity
            ws.cell(row=cont, column=7).number_format = '#.00000'
            ws.cell(row=cont, column=7).border = thin_border
            ws.cell(row=cont, column=8).value = kardex.out_quantity
            ws.cell(row=cont, column=8).number_format = '#.00000'
            ws.cell(row=cont, column=8).border = thin_border
            ws.cell(row=cont, column=9).value = kardex.total_quantity
            ws.cell(row=cont, column=9).number_format = '#.00000'
            ws.cell(row=cont, column=9).border = thin_border
        cont = cont + 1
        ws.cell(row=cont, column=6).value = "TOTALES"
        ws.cell(row=cont, column=6).border = thin_border
        ws.cell(row=cont, column=7).value = in_quantity
        ws.cell(row=cont, column=7).number_format = '#.00000'
        ws.cell(row=cont, column=7).border = thin_border
        ws.cell(row=cont, column=8).value = out_quantity
        ws.cell(row=cont, column=8).number_format = '#.00000'
        ws.cell(row=cont, column=8).border = thin_border
        ws.cell(row=cont, column=9).value = ""
        ws.cell(row=cont, column=9).number_format = '#.00000'
        ws.cell(row=cont, column=9).border = thin_border
        return wb

    def get_normal_format_product(self, product, start_date, end_date, warehouse):
        wb = Workbook()
        ws = wb.active
        ws.column_dimensions["C"].width = 14
        ws.column_dimensions["E"].width = 12
        ws.column_dimensions["F"].width = 12
        ws.column_dimensions["G"].width = 12
        ws.column_dimensions["H"].width = 12
        ws.column_dimensions["I"].width = 12
        ws.column_dimensions["J"].width = 12
        ws.column_dimensions["K"].width = 12
        ws.column_dimensions["L"].width = 12
        ws.column_dimensions["M"].width = 15
        ws['E1'] = u'Almacén: ' + warehouse.description
        ws.merge_cells('E1:G1')
        ws['H1'] = 'Periodo: ' + start_date.strftime('%d/%m/%Y') + ' - ' + end_date.strftime('%d/%m/%Y')
        ws.merge_cells('H1:J1')
        cont = 3
        ws.cell(row=cont, column=2).value = 'Codigo: ' + product.code
        ws.merge_cells(start_row=cont, start_column=2, end_row=cont, end_column=3)
        ws.cell(row=cont, column=4).value = u" Denominación: " + product.description
        ws.merge_cells(start_row=cont, start_column=4, end_row=cont, end_column=10)
        ws.cell(row=cont, column=11).value = " Unidad: " + product.unit_of_measure.description
        ws.merge_cells(start_row=cont, start_column=11, end_row=cont, end_column=12)
        cont = cont + 1
        try:
            kardex_inicial = initial_kardex_of(self, product, warehouse, start_date)
            opening_quantity = kardex_inicial.total_quantity
            opening_amount = kardex_inicial.total_amount
        except AttributeError:
            opening_quantity = 0
            opening_amount = 0
        ws.cell(row=cont, column=8).value = "SALDO INICIAL:"
        ws.merge_cells(start_row=cont, start_column=8, end_row=cont, end_column=9)
        ws.cell(row=cont, column=10).value = "Cantidad: "
        ws.cell(row=cont, column=11).value = opening_quantity
        ws.cell(row=cont, column=11).number_format = '#.00000'
        ws.cell(row=cont, column=12).value = "Valor: "
        ws.cell(row=cont, column=13).value = opening_amount
        ws.cell(row=cont, column=13).number_format = '#.00000'
        ws['B5'] = 'FECHA'
        ws['C5'] = 'NRO_DOC'
        ws['D5'] = 'TIPO_MOV'
        ws['E5'] = 'CANT. ENT'
        ws['F5'] = 'PRE. ENT'
        ws['G5'] = 'VALOR. ENT'
        ws['H5'] = 'CANT. SAL'
        ws['I5'] = 'PRE. SAL'
        ws['J5'] = 'VALOR. SAL'
        ws['K5'] = 'CANT. TOT'
        ws['L5'] = 'PRE. TOT'
        ws['M5'] = 'VALOR. TOT'
        cont = cont + 2
        listado_kardex, in_quantity, in_amount, out_quantity, out_amount = kardex_for_period(
            self, product, warehouse, start_date, end_date)
        if len(listado_kardex) > 0:
            for kardex in listado_kardex:
                ws.cell(row=cont, column=2).value = kardex.operation_date
                ws.cell(row=cont, column=2).number_format = 'dd/mm/yyyy'
                ws.cell(row=cont, column=3).value = kardex.movement.movement_id
                ws.cell(row=cont, column=4).value = kardex.movement.movement_type.code
                ws.cell(row=cont, column=5).value = kardex.in_quantity
                ws.cell(row=cont, column=5).number_format = '#.00000'
                ws.cell(row=cont, column=6).value = kardex.in_price
                ws.cell(row=cont, column=6).number_format = '#.00000'
                ws.cell(row=cont, column=7).value = kardex.in_amount
                ws.cell(row=cont, column=7).number_format = '#.00000'
                ws.cell(row=cont, column=8).value = kardex.out_quantity
                ws.cell(row=cont, column=8).number_format = '#.00000'
                ws.cell(row=cont, column=9).value = kardex.out_price
                ws.cell(row=cont, column=9).number_format = '#.00000'
                ws.cell(row=cont, column=10).value = kardex.out_amount
                ws.cell(row=cont, column=10).number_format = '#.00000'
                ws.cell(row=cont, column=11).value = kardex.total_quantity
                ws.cell(row=cont, column=11).number_format = '#.00000'
                ws.cell(row=cont, column=12).value = kardex.total_price
                ws.cell(row=cont, column=12).number_format = '#.00000'
                ws.cell(row=cont, column=13).value = kardex.total_amount
                ws.cell(row=cont, column=13).number_format = '#.00000'
                cont = cont + 1
            ws.cell(row=cont, column=5).value = in_quantity
            ws.cell(row=cont, column=7).value = in_amount
            ws.cell(row=cont, column=7).number_format = '#.00000'
            ws.cell(row=cont, column=8).value = out_quantity
            ws.cell(row=cont, column=10).value = out_amount
            ws.cell(row=cont, column=10).number_format = '#.00000'
            ws.cell(row=cont, column=11).value = kardex.total_quantity
            ws.cell(row=cont, column=13).value = kardex.total_amount
            ws.cell(row=cont, column=13).number_format = '#.00000'
            cont = cont + 2
        else:
            ws.cell(row=cont, column=5).value = 0
            ws.cell(row=cont, column=6).value = 0
            ws.cell(row=cont, column=6).number_format = '#.00000'
            ws.cell(row=cont, column=7).value = 0
            ws.cell(row=cont, column=7).number_format = '#.00000'
            ws.cell(row=cont, column=8).value = 0
            ws.cell(row=cont, column=9).value = 0
            ws.cell(row=cont, column=9).number_format = '#.00000'
            ws.cell(row=cont, column=10).value = 0
            ws.cell(row=cont, column=10).number_format = '#.00000'
            ws.cell(row=cont, column=11).value = 0
            ws.cell(row=cont, column=12).value = 0
            ws.cell(row=cont, column=12).number_format = '#.00000'
            ws.cell(row=cont, column=13).value = 0
            ws.cell(row=cont, column=13).number_format = '#.00000'
            cont = cont + 1
            ws.cell(row=cont, column=5).value = 0
            ws.cell(row=cont, column=7).value = 0
            ws.cell(row=cont, column=7).number_format = '#.00000'
            ws.cell(row=cont, column=8).value = 0
            ws.cell(row=cont, column=10).value = 0
            ws.cell(row=cont, column=10).number_format = '#.00000'
            ws.cell(row=cont, column=11).value = opening_quantity
            ws.cell(row=cont, column=13).value = opening_amount
            ws.cell(row=cont, column=13).number_format = '#.00000'
            cont = cont + 2
        return wb

    def get_sunat_valued_product(self, product, start_date, end_date, warehouse):
        wb = Workbook()
        ws = wb.active
        thin_border = Border(left=Side(style='thin'),
                             right=Side(style='thin'),
                             top=Side(style='thin'),
                             bottom=Side(style='thin'))
        ws.column_dimensions["C"].width = 15
        ws.column_dimensions["F"].width = 12
        ws.column_dimensions["G"].width = 15
        ws.column_dimensions["H"].width = 15
        ws.column_dimensions["I"].width = 15
        ws.column_dimensions["J"].width = 15
        ws.column_dimensions["K"].width = 15
        ws.column_dimensions["L"].width = 15
        ws.column_dimensions["M"].width = 15
        ws.column_dimensions["N"].width = 15
        ws.column_dimensions["O"].width = 15

        ws['H1'] = u'REGISTRO DE INVENTARIO PERMANENTE VALORIZADO'
        ws.merge_cells('H1:K1')
        ws['B3'] = "PERIODO: " + start_date.strftime('%d/%m/%Y') + ' - ' + end_date.strftime('%d/%m/%Y')
        ws.merge_cells('B3:E3')
        ws['B4'] = u"RUC:" + company().tax_id
        ws.merge_cells('B4:E4')
        ws['B5'] = u"APELLIDOS Y NOMBRES, DENOMINACIÓN O RAZÓN SOCIAL: " + company().business_name
        ws.merge_cells('B5:K5')
        ws['B6'] = u"ESTABLECIMIENTO (1): " + company().address()
        ws.merge_cells('B6:E6')
        ws['B7'] = u"CÓDIGO DE LA EXISTENCIA: " + product.code
        ws.merge_cells('B7:E7')
        ws[
            'B8'] = u"TIPO (TABLA 5): " + product.stock_type.sunat_code + " - " + product.stock_type.description
        ws.merge_cells('B8:G8')
        ws['B9'] = u"DESCRIPCIÓN: " + product.description
        ws.merge_cells('B9:E9')
        ws[
            'B10'] = u"CÓDIGO DE LA UNIDAD DE MEDIDA (TABLA 6): " + product.unit_of_measure.code + " - " + product.unit_of_measure.description
        ws.merge_cells('B10:H10')
        ws['B11'] = u"MÉTODO DE VALUACIÓN: PEPS"
        ws.merge_cells('B11:E11')

        ws['B13'] = u"DOCUMENTO DE TRASLADO, COMPROBANTE DE PAGO,\n DOCUMENTO INTERNO O SIMILAR"
        ws['B13'].border = thin_border
        ws.merge_cells('B13:E14')
        ws['B15'] = u"FECHA"
        ws['B15'].border = thin_border
        ws['C15'] = u"TIPO (TABLA 10)"
        ws['C15'].border = thin_border
        ws['D15'] = u"SERIE"
        ws['D15'].border = thin_border
        ws['E15'] = u"NÚMERO"
        ws['E15'].border = thin_border
        ws['F13'] = u"TIPO DE \n OPERACIÓN \n (TABLA 12)"
        ws['F13'].border = thin_border
        ws.merge_cells('F13:F15')

        ws['G13'] = u"ENTRADAS"
        ws['G13'].border = thin_border
        ws['I13'].border = thin_border
        ws.merge_cells('G13:I13')
        ws['G14'] = u"CANTIDAD"
        ws['G14'].border = thin_border
        ws.merge_cells('G14:G15')
        ws['H14'] = u"COSTO UNITARIO"
        ws['H14'].border = thin_border
        ws.merge_cells('H14:H15')
        ws['I14'] = u"COSTO TOTAL"
        ws['I14'].border = thin_border
        ws.merge_cells('I14:I15')

        ws['J13'] = u"SALIDAS"
        ws['J13'].border = thin_border
        ws['L13'].border = thin_border
        ws.merge_cells('J13:L13')
        ws['J14'] = u"CANTIDAD"
        ws['J14'].border = thin_border
        ws.merge_cells('J14:J15')
        ws['K14'] = u"COSTO UNITARIO"
        ws['K14'].border = thin_border
        ws.merge_cells('K14:K15')
        ws['L14'] = u"COSTO TOTAL"
        ws['L14'].border = thin_border
        ws.merge_cells('L14:L15')

        ws['M13'] = u"SALDO FINAL"
        ws['M13'].border = thin_border
        ws['O13'].border = thin_border
        ws.merge_cells('M13:O13')
        ws['M14'] = u"CANTIDAD"
        ws['M14'].border = thin_border
        ws.merge_cells('M14:M15')
        ws['N14'] = u"COSTO UNITARIO"
        ws['N14'].border = thin_border
        ws.merge_cells('N14:N15')
        ws['O14'] = u"COSTO TOTAL"
        ws['O14'].border = thin_border
        ws.merge_cells('O14:O15')

        try:
            kardex_inicial = initial_kardex_of(self, product, warehouse, start_date)
            opening_quantity = kardex_inicial.total_quantity
            opening_amount = kardex_inicial.total_amount
        except AttributeError:
            opening_quantity = 0
            opening_amount = 0
        cont = 16
        ws.cell(row=cont, column=2).border = thin_border
        ws.cell(row=cont, column=3).value = '00'
        ws.cell(row=cont, column=3).border = thin_border
        ws.cell(row=cont, column=4).value = 'SALDO'
        ws.cell(row=cont, column=4).border = thin_border
        ws.cell(row=cont, column=5).value = 'INICIAL'
        ws.cell(row=cont, column=5).border = thin_border
        ws.cell(row=cont, column=6).value = '16'
        ws.cell(row=cont, column=6).border = thin_border
        ws.cell(row=cont, column=7).value = 0
        ws.cell(row=cont, column=7).number_format = '#.00000'
        ws.cell(row=cont, column=7).border = thin_border
        ws.cell(row=cont, column=8).value = 0
        ws.cell(row=cont, column=8).number_format = '#.00000'
        ws.cell(row=cont, column=9).border = thin_border
        ws.cell(row=cont, column=9).value = 0
        ws.cell(row=cont, column=9).number_format = '#.00000'
        ws.cell(row=cont, column=10).value = 0
        ws.cell(row=cont, column=10).number_format = '#.00000'
        ws.cell(row=cont, column=10).border = thin_border
        ws.cell(row=cont, column=11).value = 0
        ws.cell(row=cont, column=11).number_format = '#.00000'
        ws.cell(row=cont, column=11).border = thin_border
        ws.cell(row=cont, column=12).value = 0
        ws.cell(row=cont, column=12).number_format = '#.00000'
        ws.cell(row=cont, column=12).border = thin_border
        ws.cell(row=cont, column=13).value = opening_quantity
        ws.cell(row=cont, column=13).number_format = '#.00000'
        ws.cell(row=cont, column=13).border = thin_border
        try:
            ws.cell(row=cont, column=14).value = opening_amount / opening_quantity
        except ZeroDivisionError:
            ws.cell(row=cont, column=14).value = 0
        ws.cell(row=cont, column=14).number_format = '#.00000'
        ws.cell(row=cont, column=14).border = thin_border
        ws.cell(row=cont, column=15).value = opening_amount
        ws.cell(row=cont, column=15).number_format = '#.00000'
        ws.cell(row=cont, column=15).border = thin_border

        listado_kardex, in_quantity, in_amount, out_quantity, out_amount = kardex_for_period(
            self, product, warehouse, start_date, end_date)
        for kardex in listado_kardex:
            cont = cont + 1
            ws.cell(row=cont, column=2).value = kardex.operation_date.strftime('%d/%m/%Y')
            ws.cell(row=cont, column=2).border = thin_border
            try:
                ws.cell(row=cont, column=3).value = kardex.movement.document_type.sunat_code
            except ObjectDoesNotExist:
                ws.cell(row=cont, column=3).value = '-'
            ws.cell(row=cont, column=3).border = thin_border
            ws.cell(row=cont, column=4).value = kardex.movement.series
            ws.cell(row=cont, column=4).border = thin_border
            ws.cell(row=cont, column=5).value = kardex.movement.number
            ws.cell(row=cont, column=5).border = thin_border
            ws.cell(row=cont, column=6).value = kardex.movement.movement_type.sunat_code
            ws.cell(row=cont, column=6).border = thin_border
            ws.cell(row=cont, column=7).value = kardex.in_quantity
            ws.cell(row=cont, column=7).number_format = '#.00000'
            ws.cell(row=cont, column=7).border = thin_border
            ws.cell(row=cont, column=8).value = kardex.in_price
            ws.cell(row=cont, column=8).number_format = '#.00000'
            ws.cell(row=cont, column=8).border = thin_border
            ws.cell(row=cont, column=9).value = kardex.in_amount
            ws.cell(row=cont, column=9).number_format = '#.00000'
            ws.cell(row=cont, column=9).border = thin_border
            ws.cell(row=cont, column=10).value = kardex.out_quantity
            ws.cell(row=cont, column=10).number_format = '#.00000'
            ws.cell(row=cont, column=10).border = thin_border
            ws.cell(row=cont, column=11).value = kardex.out_price
            ws.cell(row=cont, column=11).number_format = '#.00000'
            ws.cell(row=cont, column=11).border = thin_border
            ws.cell(row=cont, column=12).value = kardex.out_amount
            ws.cell(row=cont, column=12).number_format = '#.00000'
            ws.cell(row=cont, column=12).border = thin_border
            ws.cell(row=cont, column=13).value = kardex.total_quantity
            ws.cell(row=cont, column=13).number_format = '#.00000'
            ws.cell(row=cont, column=13).border = thin_border
            ws.cell(row=cont, column=14).value = kardex.total_price
            ws.cell(row=cont, column=14).number_format = '#.00000'
            ws.cell(row=cont, column=14).border = thin_border
            ws.cell(row=cont, column=15).value = kardex.total_amount
            ws.cell(row=cont, column=15).number_format = '#.00000'
            ws.cell(row=cont, column=15).border = thin_border
        cont = cont + 1

        ws.cell(row=cont, column=6).value = "TOTALES"
        ws.cell(row=cont, column=6).border = thin_border
        ws.cell(row=cont, column=7).value = in_quantity
        ws.cell(row=cont, column=7).number_format = '#.00000'
        ws.cell(row=cont, column=7).border = thin_border
        ws.cell(row=cont, column=8).value = ""
        ws.cell(row=cont, column=8).number_format = '#.00000'
        ws.cell(row=cont, column=8).border = thin_border
        ws.cell(row=cont, column=9).value = in_amount
        ws.cell(row=cont, column=9).number_format = '#.00000'
        ws.cell(row=cont, column=9).border = thin_border
        ws.cell(row=cont, column=10).value = out_quantity
        ws.cell(row=cont, column=10).number_format = '#.00000'
        ws.cell(row=cont, column=10).border = thin_border
        ws.cell(row=cont, column=11).value = ""
        ws.cell(row=cont, column=11).number_format = '#.00000'
        ws.cell(row=cont, column=11).border = thin_border
        ws.cell(row=cont, column=12).value = out_amount
        ws.cell(row=cont, column=12).number_format = '#.00000'
        ws.cell(row=cont, column=12).border = thin_border
        ws.cell(row=cont, column=13).value = ""
        ws.cell(row=cont, column=13).number_format = '#.00000'
        ws.cell(row=cont, column=13).border = thin_border
        ws.cell(row=cont, column=14).value = ""
        ws.cell(row=cont, column=14).number_format = '#.00000'
        ws.cell(row=cont, column=14).border = thin_border
        ws.cell(row=cont, column=15).value = ""
        ws.cell(row=cont, column=15).number_format = '#.00000'
        ws.cell(row=cont, column=15).border = thin_border
        return wb

    def get_sunat_physical_units_excel_by_product(self, ws, thin_border, cont, product, start_date, end_date,
                                                                  warehouse):
        ws.column_dimensions["C"].width = 15
        ws.column_dimensions["F"].width = 12
        ws.column_dimensions["G"].width = 15
        ws.column_dimensions["H"].width = 15
        ws.column_dimensions["I"].width = 15
        ws.column_dimensions["J"].width = 15
        ws.column_dimensions["K"].width = 15
        ws.column_dimensions["L"].width = 15
        ws.column_dimensions["M"].width = 15
        ws.column_dimensions["N"].width = 15
        ws.column_dimensions["O"].width = 15
        ws.cell(row=cont, column=4).value = u'REGISTRO DEL INVENTARIO PERMANENTE EN UNIDADES FÍSICAS'
        ws.merge_cells(start_row=cont, start_column=4, end_row=cont, end_column=8)
        cont = cont + 1
        ws.cell(row=cont, column=2).value = "PERIODO: " + start_date.strftime('%d/%m/%Y') + ' - ' + end_date.strftime(
            '%d/%m/%Y')
        ws.merge_cells(start_row=cont, start_column=2, end_row=cont, end_column=5)
        cont = cont + 1
        ws.cell(row=cont, column=2).value = u"RUC:" + company().tax_id
        ws.merge_cells(start_row=cont, start_column=2, end_row=cont, end_column=5)
        cont = cont + 1
        ws.cell(row=cont, column=2).value = u"APELLIDOS Y NOMBRES, DENOMINACIÓN O RAZÓN SOCIAL: " + company().business_name
        ws.merge_cells(start_row=cont, start_column=2, end_row=cont, end_column=11)
        cont = cont + 1
        ws.cell(row=cont, column=2).value = u"ESTABLECIMIENTO (1): " + company().address()
        ws.merge_cells(start_row=cont, start_column=2, end_row=cont, end_column=5)
        cont = cont + 1
        ws.cell(row=cont, column=2).value = u"CÓDIGO DE LA EXISTENCIA: " + product.code
        ws.merge_cells(start_row=cont, start_column=2, end_row=cont, end_column=5)
        cont = cont + 1
        ws.cell(row=cont,
                column=2).value = u"TIPO (TABLA 5): " + product.stock_type.sunat_code + " - " + product.stock_type.description
        ws.merge_cells(start_row=cont, start_column=2, end_row=cont, end_column=7)
        cont = cont + 1
        ws.cell(row=cont, column=2).value = u"DESCRIPCIÓN: " + product.description
        ws.merge_cells(start_row=cont, start_column=2, end_row=cont, end_column=5)
        cont = cont + 1
        ws.cell(row=cont,
                column=2).value = u"CÓDIGO DE LA UNIDAD DE MEDIDA (TABLA 6): " + product.unit_of_measure.code + " - " + product.unit_of_measure.description
        ws.merge_cells(start_row=cont, start_column=2, end_row=cont, end_column=8)
        cont = cont + 1
        ws.cell(row=cont, column=2).value = u"MÉTODO DE VALUACIÓN: PEPS"
        ws.merge_cells(start_row=cont, start_column=2, end_row=cont, end_column=5)
        cont = cont + 2
        ws.cell(row=cont, column=2).value = u"DOCUMENTO DE TRASLADO, COMPROBANTE DE PAGO,\n DOCUMENTO INTERNO O SIMILAR"
        ws.cell(row=cont, column=2).border = thin_border
        ws.merge_cells(start_row=cont, start_column=2, end_row=cont + 1, end_column=5)
        ws.cell(row=cont, column=6).value = u"TIPO DE \n OPERACIÓN \n (TABLA 12)"
        ws.cell(row=cont, column=6).border = thin_border
        ws.merge_cells(start_row=cont, start_column=6, end_row=cont + 2, end_column=6)
        ws.cell(row=cont, column=7).value = u"ENTRADAS"
        ws.cell(row=cont, column=7).border = thin_border
        ws.merge_cells(start_row=cont, start_column=7, end_row=cont + 2, end_column=7)
        ws.cell(row=cont, column=8).value = u"SALIDAS"
        ws.cell(row=cont, column=8).border = thin_border
        ws.merge_cells(start_row=cont, start_column=8, end_row=cont + 2, end_column=8)
        ws.cell(row=cont, column=9).value = u"SALDO FINAL"
        ws.cell(row=cont, column=9).border = thin_border
        ws.merge_cells(start_row=cont, start_column=9, end_row=cont + 2, end_column=9)
        cont = cont + 2
        ws.cell(row=cont, column=2).value = u"FECHA"
        ws.cell(row=cont, column=2).border = thin_border
        ws.cell(row=cont, column=3).value = u"TIPO (TABLA 10)"
        ws.cell(row=cont, column=3).border = thin_border
        ws.cell(row=cont, column=4).value = u"SERIE"
        ws.cell(row=cont, column=4).border = thin_border
        ws.cell(row=cont, column=5).value = u"NÚMERO"
        ws.cell(row=cont, column=5).border = thin_border

        try:
            kardex_inicial = initial_kardex_of(self, product, warehouse, start_date)
            opening_quantity = kardex_inicial.total_quantity
        except AttributeError:
            opening_quantity = 0
        cont = cont + 1
        ws.cell(row=cont, column=2).border = thin_border
        ws.cell(row=cont, column=3).value = '00'
        ws.cell(row=cont, column=3).border = thin_border
        ws.cell(row=cont, column=4).value = 'SALDO'
        ws.cell(row=cont, column=4).border = thin_border
        ws.cell(row=cont, column=5).value = 'INICIAL'
        ws.cell(row=cont, column=5).border = thin_border
        ws.cell(row=cont, column=6).value = '16'
        ws.cell(row=cont, column=6).border = thin_border
        ws.cell(row=cont, column=7).value = 0
        ws.cell(row=cont, column=7).number_format = '#.00000'
        ws.cell(row=cont, column=7).border = thin_border
        ws.cell(row=cont, column=8).value = 0
        ws.cell(row=cont, column=8).number_format = '#.00000'
        ws.cell(row=cont, column=8).border = thin_border
        ws.cell(row=cont, column=9).value = opening_quantity
        ws.cell(row=cont, column=9).number_format = '#.00000'
        ws.cell(row=cont, column=9).border = thin_border

        listado_kardex, in_quantity, in_amount, out_quantity, out_amount = kardex_for_period(
            self, product, warehouse, start_date, end_date)
        for kardex in listado_kardex:
            cont = cont + 1
            ws.cell(row=cont, column=2).value = kardex.operation_date.strftime('%d/%m/%Y')
            ws.cell(row=cont, column=2).border = thin_border
            try:
                ws.cell(row=cont, column=3).value = kardex.movement.document_type.sunat_code
            except ObjectDoesNotExist:
                ws.cell(row=cont, column=3).value = '-'
            ws.cell(row=cont, column=3).border = thin_border
            ws.cell(row=cont, column=4).value = kardex.movement.series
            ws.cell(row=cont, column=4).border = thin_border
            ws.cell(row=cont, column=5).value = kardex.movement.number
            ws.cell(row=cont, column=5).border = thin_border
            ws.cell(row=cont, column=6).value = kardex.movement.movement_type.sunat_code
            ws.cell(row=cont, column=6).border = thin_border
            ws.cell(row=cont, column=7).value = kardex.in_quantity
            ws.cell(row=cont, column=7).number_format = '#.00000'
            ws.cell(row=cont, column=7).border = thin_border
            ws.cell(row=cont, column=8).value = kardex.out_quantity
            ws.cell(row=cont, column=8).number_format = '#.00000'
            ws.cell(row=cont, column=8).border = thin_border
            ws.cell(row=cont, column=9).value = kardex.total_quantity
            ws.cell(row=cont, column=9).number_format = '#.00000'
            ws.cell(row=cont, column=9).border = thin_border
        cont = cont + 1
        ws.cell(row=cont, column=6).value = "TOTALES"
        ws.cell(row=cont, column=6).border = thin_border
        ws.cell(row=cont, column=7).value = in_quantity
        ws.cell(row=cont, column=7).number_format = '#.00000'
        ws.cell(row=cont, column=7).border = thin_border
        ws.cell(row=cont, column=8).value = out_quantity
        ws.cell(row=cont, column=8).number_format = '#.00000'
        ws.cell(row=cont, column=8).border = thin_border
        ws.cell(row=cont, column=9).value = ""
        ws.cell(row=cont, column=9).number_format = '#.00000'
        ws.cell(row=cont, column=9).border = thin_border
        return ws

    def get_sunat_physical_units_all(self, start_date, end_date, warehouse):
        productos = Product.objects.all().order_by('description').select_related(
            'unit_of_measure', 'stock_type')
        self.kardex_iniciales = Kardex.last_by_product(productos, before=start_date, warehouse=warehouse)
        self.kardex_batch = Product.kardex_by_batch(productos, warehouse, start_date, end_date)
        wb = Workbook()
        ws = wb.active
        thin_border = Border(left=Side(style='thin'),
                             right=Side(style='thin'),
                             top=Side(style='thin'),
                             bottom=Side(style='thin'))
        cont = 1
        for product in productos:
            ws.title = product.code
            self.get_sunat_physical_units_excel_by_product(ws, thin_border, cont, product, start_date,
                                                                           end_date, warehouse)
            ws = wb.create_sheet("Hoja")
        return wb

    def get_sunat_valued_excel_by_product(self, ws, thin_border, cont, product, start_date, end_date,
                                                            warehouse):
        ws.column_dimensions["C"].width = 15
        ws.column_dimensions["F"].width = 12
        ws.column_dimensions["G"].width = 15
        ws.column_dimensions["H"].width = 15
        ws.column_dimensions["I"].width = 15
        ws.column_dimensions["J"].width = 15
        ws.column_dimensions["K"].width = 15
        ws.column_dimensions["L"].width = 15
        ws.column_dimensions["M"].width = 15
        ws.column_dimensions["N"].width = 15
        ws.column_dimensions["O"].width = 15
        ws.cell(row=cont, column=4).value = u'REGISTRO DE INVENTARIO PERMANENTE VALORIZADO'
        ws.merge_cells(start_row=cont, start_column=4, end_row=cont, end_column=8)
        cont = cont + 1
        ws.cell(row=cont, column=2).value = "PERIODO: " + start_date.strftime('%d/%m/%Y') + ' - ' + end_date.strftime(
            '%d/%m/%Y')
        ws.merge_cells(start_row=cont, start_column=2, end_row=cont, end_column=5)
        cont = cont + 1
        ws.cell(row=cont, column=2).value = u"RUC:" + company().tax_id
        ws.merge_cells(start_row=cont, start_column=2, end_row=cont, end_column=5)
        cont = cont + 1
        ws.cell(row=cont, column=2).value = u"APELLIDOS Y NOMBRES, DENOMINACIÓN O RAZÓN SOCIAL: " + company().business_name
        ws.merge_cells(start_row=cont, start_column=2, end_row=cont, end_column=11)
        cont = cont + 1
        ws.cell(row=cont, column=2).value = u"ESTABLECIMIENTO (1): " + company().address()
        ws.merge_cells(start_row=cont, start_column=2, end_row=cont, end_column=5)
        cont = cont + 1
        ws.cell(row=cont, column=2).value = u"CÓDIGO DE LA EXISTENCIA: " + product.code
        ws.merge_cells(start_row=cont, start_column=2, end_row=cont, end_column=5)
        cont = cont + 1
        ws.cell(row=cont,
                column=2).value = u"TIPO (TABLA 5): " + product.stock_type.sunat_code + " - " + product.stock_type.description
        ws.merge_cells(start_row=cont, start_column=2, end_row=cont, end_column=7)
        cont = cont + 1
        ws.cell(row=cont, column=2).value = u"DESCRIPCIÓN: " + product.description
        ws.merge_cells(start_row=cont, start_column=2, end_row=cont, end_column=5)
        cont = cont + 1
        ws.cell(row=cont,
                column=2).value = u"CÓDIGO DE LA UNIDAD DE MEDIDA (TABLA 6): " + product.unit_of_measure.code + " - " + product.unit_of_measure.description
        ws.merge_cells(start_row=cont, start_column=2, end_row=cont, end_column=8)
        cont = cont + 1
        ws.cell(row=cont, column=2).value = u"MÉTODO DE VALUACIÓN: PEPS"
        ws.merge_cells(start_row=cont, start_column=2, end_row=cont, end_column=5)
        cont = cont + 2

        ws.cell(row=cont, column=2).value = u"DOCUMENTO DE TRASLADO, COMPROBANTE DE PAGO,\n DOCUMENTO INTERNO O SIMILAR"
        ws.cell(row=cont, column=2).border = thin_border
        ws.merge_cells(start_row=cont, start_column=2, end_row=cont + 1, end_column=5)
        ws.cell(row=cont, column=6).value = u"TIPO DE \n OPERACIÓN \n (TABLA 12)"
        ws.cell(row=cont, column=6).border = thin_border
        ws.merge_cells(start_row=cont, start_column=6, end_row=cont + 2, end_column=6)
        ws.cell(row=cont, column=7).value = u"ENTRADAS"
        ws.cell(row=cont, column=7).border = thin_border
        ws.merge_cells(start_row=cont, start_column=7, end_row=cont, end_column=9)
        ws.cell(row=cont, column=10).value = u"SALIDAS"
        ws.cell(row=cont, column=10).border = thin_border
        ws.merge_cells(start_row=cont, start_column=10, end_row=cont, end_column=12)
        ws.cell(row=cont, column=13).value = u"SALDO FINAL"
        ws.merge_cells(start_row=cont, start_column=13, end_row=cont, end_column=15)
        ws.cell(row=cont, column=13).border = thin_border
        cont = cont + 2
        ws.cell(row=cont, column=2).value = u"FECHA"
        ws.cell(row=cont, column=2).border = thin_border
        ws.cell(row=cont, column=3).value = u"TIPO (TABLA 10)"
        ws.cell(row=cont, column=3).border = thin_border
        ws.cell(row=cont, column=4).value = u"SERIE"
        ws.cell(row=cont, column=4).border = thin_border
        ws.cell(row=cont, column=5).value = u"NÚMERO"
        ws.cell(row=cont, column=5).border = thin_border

        ws.cell(row=cont - 1, column=7).value = u"CANTIDAD"
        ws.merge_cells(start_row=cont - 1, start_column=7, end_row=cont, end_column=7)
        ws.cell(row=cont - 1, column=7).border = thin_border
        ws.cell(row=cont - 1, column=8).value = u"COSTO UNITARIO"
        ws.merge_cells(start_row=cont - 1, start_column=8, end_row=cont, end_column=8)
        ws.cell(row=cont - 1, column=8).border = thin_border
        ws.cell(row=cont - 1, column=9).value = u"COSTO TOTAL"
        ws.merge_cells(start_row=cont - 1, start_column=9, end_row=cont, end_column=9)
        ws.cell(row=cont - 1, column=9).border = thin_border
        ws.cell(row=cont - 1, column=10).value = u"CANTIDAD"
        ws.merge_cells(start_row=cont - 1, start_column=10, end_row=cont, end_column=10)
        ws.cell(row=cont - 1, column=10).border = thin_border
        ws.cell(row=cont - 1, column=11).value = u"COSTO UNITARIO"
        ws.merge_cells(start_row=cont - 1, start_column=11, end_row=cont, end_column=11)
        ws.cell(row=cont - 1, column=11).border = thin_border
        ws.cell(row=cont - 1, column=12).value = u"COSTO TOTAL"
        ws.merge_cells(start_row=cont - 1, start_column=12, end_row=cont, end_column=12)
        ws.cell(row=cont - 1, column=12).border = thin_border
        ws.cell(row=cont - 1, column=13).value = u"CANTIDAD"
        ws.merge_cells(start_row=cont - 1, start_column=13, end_row=cont, end_column=13)
        ws.cell(row=cont - 1, column=13).border = thin_border
        ws.cell(row=cont - 1, column=14).value = u"COSTO UNITARIO"
        ws.merge_cells(start_row=cont - 1, start_column=14, end_row=cont, end_column=14)
        ws.cell(row=cont - 1, column=14).border = thin_border
        ws.cell(row=cont - 1, column=15).value = u"COSTO TOTAL"
        ws.merge_cells(start_row=cont - 1, start_column=15, end_row=cont, end_column=15)
        ws.cell(row=cont - 1, column=15).border = thin_border
        try:
            kardex_inicial = initial_kardex_of(self, product, warehouse, start_date)
            opening_quantity = kardex_inicial.total_quantity
            opening_amount = kardex_inicial.total_amount
        except AttributeError:
            opening_quantity = 0
            opening_amount = 0
        cont = cont + 1
        ws.cell(row=cont, column=2).border = thin_border
        ws.cell(row=cont, column=3).value = '00'
        ws.cell(row=cont, column=3).border = thin_border
        ws.cell(row=cont, column=4).value = 'SALDO'
        ws.cell(row=cont, column=4).border = thin_border
        ws.cell(row=cont, column=5).value = 'INICIAL'
        ws.cell(row=cont, column=5).border = thin_border
        ws.cell(row=cont, column=6).value = '16'
        ws.cell(row=cont, column=6).border = thin_border
        ws.cell(row=cont, column=7).value = 0
        ws.cell(row=cont, column=7).number_format = '#.00000'
        ws.cell(row=cont, column=7).border = thin_border
        ws.cell(row=cont, column=8).value = 0
        ws.cell(row=cont, column=8).number_format = '#.00000'
        ws.cell(row=cont, column=8).border = thin_border
        ws.cell(row=cont, column=9).value = 0
        ws.cell(row=cont, column=9).number_format = '#.00000'
        ws.cell(row=cont, column=9).border = thin_border
        ws.cell(row=cont, column=10).value = 0
        ws.cell(row=cont, column=10).number_format = '#.00000'
        ws.cell(row=cont, column=10).border = thin_border
        ws.cell(row=cont, column=11).value = 0
        ws.cell(row=cont, column=11).number_format = '#.00000'
        ws.cell(row=cont, column=11).border = thin_border
        ws.cell(row=cont, column=12).value = 0
        ws.cell(row=cont, column=12).number_format = '#.00000'
        ws.cell(row=cont, column=12).border = thin_border
        ws.cell(row=cont, column=13).value = opening_quantity
        ws.cell(row=cont, column=13).number_format = '#.00000'
        ws.cell(row=cont, column=13).border = thin_border
        try:
            ws.cell(row=cont, column=14).value = opening_amount / opening_quantity
        except ZeroDivisionError:
            ws.cell(row=cont, column=14).value = 0
        ws.cell(row=cont, column=14).number_format = '#.00000'
        ws.cell(row=cont, column=14).border = thin_border
        ws.cell(row=cont, column=15).value = opening_amount
        ws.cell(row=cont, column=15).number_format = '#.00000'
        ws.cell(row=cont, column=15).border = thin_border

        listado_kardex, in_quantity, in_amount, out_quantity, out_amount = kardex_for_period(
            self, product, warehouse, start_date, end_date)
        for kardex in listado_kardex:
            cont = cont + 1
            ws.cell(row=cont, column=2).value = kardex.operation_date.strftime('%d/%m/%Y')
            ws.cell(row=cont, column=2).border = thin_border
            try:
                ws.cell(row=cont, column=3).value = kardex.movement.document_type.sunat_code
            except ObjectDoesNotExist:
                ws.cell(row=cont, column=3).value = '-'
            ws.cell(row=cont, column=3).border = thin_border
            ws.cell(row=cont, column=4).value = kardex.movement.series
            ws.cell(row=cont, column=4).border = thin_border
            ws.cell(row=cont, column=5).value = kardex.movement.number
            ws.cell(row=cont, column=5).border = thin_border
            ws.cell(row=cont, column=6).value = kardex.movement.movement_type.sunat_code
            ws.cell(row=cont, column=6).border = thin_border
            ws.cell(row=cont, column=7).value = kardex.in_quantity
            ws.cell(row=cont, column=7).number_format = '#.00000'
            ws.cell(row=cont, column=7).border = thin_border
            ws.cell(row=cont, column=8).value = kardex.in_price
            ws.cell(row=cont, column=8).number_format = '#.00000'
            ws.cell(row=cont, column=8).border = thin_border
            ws.cell(row=cont, column=9).value = kardex.in_amount
            ws.cell(row=cont, column=9).number_format = '#.00000'
            ws.cell(row=cont, column=9).border = thin_border
            ws.cell(row=cont, column=10).value = kardex.out_quantity
            ws.cell(row=cont, column=10).number_format = '#.00000'
            ws.cell(row=cont, column=10).border = thin_border
            ws.cell(row=cont, column=11).value = kardex.out_price
            ws.cell(row=cont, column=11).number_format = '#.00000'
            ws.cell(row=cont, column=11).border = thin_border
            ws.cell(row=cont, column=12).value = kardex.out_amount
            ws.cell(row=cont, column=12).number_format = '#.00000'
            ws.cell(row=cont, column=12).border = thin_border
            ws.cell(row=cont, column=13).value = kardex.total_quantity
            ws.cell(row=cont, column=13).number_format = '#.00000'
            ws.cell(row=cont, column=13).border = thin_border
            ws.cell(row=cont, column=14).value = kardex.total_price
            ws.cell(row=cont, column=14).number_format = '#.00000'
            ws.cell(row=cont, column=14).border = thin_border
            ws.cell(row=cont, column=15).value = kardex.total_amount
            ws.cell(row=cont, column=15).number_format = '#.00000'
            ws.cell(row=cont, column=15).border = thin_border
        cont = cont + 1

        ws.cell(row=cont, column=6).value = "TOTALES"
        ws.cell(row=cont, column=6).border = thin_border
        ws.cell(row=cont, column=7).value = in_quantity
        ws.cell(row=cont, column=7).number_format = '#.00000'
        ws.cell(row=cont, column=7).border = thin_border
        ws.cell(row=cont, column=8).value = ""
        ws.cell(row=cont, column=8).number_format = '#.00000'
        ws.cell(row=cont, column=8).border = thin_border
        ws.cell(row=cont, column=9).value = in_amount
        ws.cell(row=cont, column=9).number_format = '#.00000'
        ws.cell(row=cont, column=9).border = thin_border
        ws.cell(row=cont, column=10).value = out_quantity
        ws.cell(row=cont, column=10).number_format = '#.00000'
        ws.cell(row=cont, column=10).border = thin_border
        ws.cell(row=cont, column=11).value = ""
        ws.cell(row=cont, column=11).number_format = '#.00000'
        ws.cell(row=cont, column=11).border = thin_border
        ws.cell(row=cont, column=12).value = out_amount
        ws.cell(row=cont, column=12).number_format = '#.00000'
        ws.cell(row=cont, column=12).border = thin_border
        ws.cell(row=cont, column=13).value = ""
        ws.cell(row=cont, column=13).number_format = '#.00000'
        ws.cell(row=cont, column=13).border = thin_border
        ws.cell(row=cont, column=14).value = ""
        ws.cell(row=cont, column=14).number_format = '#.00000'
        ws.cell(row=cont, column=14).border = thin_border
        ws.cell(row=cont, column=15).value = ""
        ws.cell(row=cont, column=15).number_format = '#.00000'
        ws.cell(row=cont, column=15).border = thin_border
        return ws

    def get_sunat_valued_all(self, start_date, end_date, warehouse):
        productos = Product.objects.all().order_by('description').select_related(
            'unit_of_measure', 'stock_type')
        self.kardex_iniciales = Kardex.last_by_product(productos, before=start_date, warehouse=warehouse)
        self.kardex_batch = Product.kardex_by_batch(productos, warehouse, start_date, end_date)
        wb = Workbook()
        ws = wb.active
        thin_border = Border(left=Side(style='thin'),
                             right=Side(style='thin'),
                             top=Side(style='thin'),
                             bottom=Side(style='thin'))
        cont = 1
        for product in productos:
            ws.title = product.code
            self.get_sunat_valued_excel_by_product(ws, thin_border, cont, product, start_date, end_date,
                                                                     warehouse)
            ws = wb.create_sheet("Hoja")
        return wb

    def get_consolidated_groups(self, start_date, end_date, warehouse):
        groups = ProductGroup.objects.filter(is_active=True,
                                               contains_products=True)
        self.kardex_batch_groups = ProductGroup.kardex_by_batch(groups, warehouse, start_date, end_date)
        wb = Workbook()
        ws = wb.active
        thin_border = Border(left=Side(style='thin'),
                             right=Side(style='thin'),
                             top=Side(style='thin'),
                             bottom=Side(style='thin'))
        ws.column_dimensions["B"].width = 8
        ws.column_dimensions["C"].width = 40
        ws.column_dimensions["D"].width = 10
        ws.column_dimensions["E"].width = 14
        ws.column_dimensions["F"].width = 14
        ws.column_dimensions["G"].width = 14
        ws.column_dimensions["H"].width = 14
        ws.column_dimensions["I"].width = 14
        ws.column_dimensions["J"].width = 14
        ws.column_dimensions["K"].width = 14
        ws.column_dimensions["L"].width = 14
        ws['D1'] = u'Almacén: ' + warehouse.description
        ws.merge_cells('D1:F1')
        ws['H1'] = 'Periodo: ' + start_date.strftime('%d/%m/%Y') + '-' + end_date.strftime('%d/%m/%Y')
        ws.merge_cells('H1:J1')
        ws['B3'] = 'CODIGO'
        ws['C3'] = 'NOMBRE'
        ws['D3'] = 'CTA_CONT.'
        ws['E3'] = 'CANT INICIAL'
        ws['F3'] = 'VALOR INICIAL'
        ws['G3'] = 'CANT. ENT'
        ws['H3'] = 'VALOR. ENT'
        ws['I3'] = 'CANT. SAL'
        ws['J3'] = 'VALOR. SAL'
        ws['K3'] = 'CANT. TOT'
        ws['L3'] = 'VALOR. TOT'
        ws['B3'].border = thin_border
        ws['C3'].border = thin_border
        ws['D3'].border = thin_border
        ws['E3'].border = thin_border
        ws['F3'].border = thin_border
        ws['G3'].border = thin_border
        ws['H3'].border = thin_border
        ws['I3'].border = thin_border
        ws['J3'].border = thin_border
        ws['K3'].border = thin_border
        ws['L3'].border = thin_border
        cont = 4
        for group in groups:
            ws.cell(row=cont, column=2).value = group.code
            ws.cell(row=cont, column=2).border = thin_border
            ws.cell(row=cont, column=3).value = group.description
            ws.cell(row=cont, column=3).border = thin_border
            ws.cell(row=cont, column=4).value = group.account.account_number
            ws.cell(row=cont, column=4).border = thin_border
            try:
                kardex_inicial = Kardex.objects.filter(product__product_group=group,
                                                       warehouse=warehouse,
                                                       operation_date__lt=start_date).latest('operation_date')
                opening_quantity = kardex_inicial.total_quantity
                opening_amount = kardex_inicial.total_amount
            except Kardex.DoesNotExist:
                opening_quantity = 0
                opening_amount = 0
            ws.cell(row=cont, column=5).value = opening_quantity
            ws.cell(row=cont, column=5).number_format = '#.00000'
            ws.cell(row=cont, column=5).border = thin_border
            ws.cell(row=cont, column=6).value = opening_amount
            ws.cell(row=cont, column=6).number_format = '#.00000'
            ws.cell(row=cont, column=6).border = thin_border
            listado_kardex, in_quantity, in_amount, out_quantity, out_amount = kardex_for_period(
                self, group, warehouse, start_date, end_date, by_group=True)
            total_quantity = opening_quantity + in_quantity - out_quantity
            total_amount = opening_amount + in_amount - out_amount
            ws.cell(row=cont, column=7).value = in_quantity
            ws.cell(row=cont, column=7).number_format = '#.00000'
            ws.cell(row=cont, column=7).border = thin_border
            ws.cell(row=cont, column=8).value = in_amount
            ws.cell(row=cont, column=8).number_format = '#.00000'
            ws.cell(row=cont, column=8).border = thin_border
            ws.cell(row=cont, column=9).value = out_quantity
            ws.cell(row=cont, column=9).number_format = '#.00000'
            ws.cell(row=cont, column=9).border = thin_border
            ws.cell(row=cont, column=10).value = out_amount
            ws.cell(row=cont, column=10).number_format = '#.00000'
            ws.cell(row=cont, column=10).border = thin_border
            ws.cell(row=cont, column=11).value = total_quantity
            ws.cell(row=cont, column=11).number_format = '#.00000'
            ws.cell(row=cont, column=11).border = thin_border
            ws.cell(row=cont, column=12).value = total_amount
            ws.cell(row=cont, column=12).number_format = '#.00000'
            ws.cell(row=cont, column=12).border = thin_border
            cont += 1
        return wb

    def get_consolidated_products(self, start_date, end_date, warehouse):
        productos = Product.objects.all().order_by('description')
        wb = Workbook()
        thin_border = Border(left=Side(style='thin'),
                             right=Side(style='thin'),
                             top=Side(style='thin'),
                             bottom=Side(style='thin'))
        ws = wb.active
        ws.column_dimensions["B"].width = 12
        ws.column_dimensions["C"].width = 50
        ws.column_dimensions["D"].width = 12
        ws.column_dimensions["E"].width = 12
        ws.column_dimensions["F"].width = 12
        ws.column_dimensions["G"].width = 12
        ws.column_dimensions["H"].width = 12
        ws.column_dimensions["I"].width = 12
        ws.column_dimensions["J"].width = 12
        ws.column_dimensions["K"].width = 12
        ws['D1'] = u'Almacén: ' + warehouse.description
        ws.merge_cells('D1:F1')
        ws['G1'] = 'Periodo: ' + start_date.strftime('%d/%m/%Y') + ' - ' + end_date.strftime('%d/%m/%Y')
        ws.merge_cells('G1:I1')
        ws['B3'] = 'CODIGO'
        ws['C3'] = 'NOMBRE'
        ws['D3'] = 'CANT INICIAL'
        ws['E3'] = 'VALOR INICIAL'
        ws['F3'] = 'CANT. ENT'
        ws['G3'] = 'VALOR. ENT'
        ws['H3'] = 'CANT. SAL'
        ws['I3'] = 'VALOR. SAL'
        ws['J3'] = 'CANT. TOT'
        ws['K3'] = 'VALOR. TOT'
        ws['B3'].border = thin_border
        ws['C3'].border = thin_border
        ws['D3'].border = thin_border
        ws['E3'].border = thin_border
        ws['F3'].border = thin_border
        ws['G3'].border = thin_border
        ws['H3'].border = thin_border
        ws['I3'].border = thin_border
        ws['J3'].border = thin_border
        ws['K3'].border = thin_border
        cont = 4
        iniciales = Kardex.last_by_product(productos, before=start_date, warehouse=warehouse)
        self.kardex_batch = Product.kardex_by_batch(productos, warehouse, start_date, end_date)
        for product in productos:
            ws.cell(row=cont, column=2).value = product.code
            ws.cell(row=cont, column=2).border = thin_border
            ws.cell(row=cont, column=3).value = product.description
            ws.cell(row=cont, column=3).border = thin_border
            try:
                kardex_inicial = iniciales.get(product.pk)
                opening_quantity = kardex_inicial.total_quantity
                opening_amount = kardex_inicial.total_amount
            except AttributeError:
                opening_quantity = 0
                opening_amount = 0
            ws.cell(row=cont, column=4).value = opening_quantity
            ws.cell(row=cont, column=4).number_format = '#.00000'
            ws.cell(row=cont, column=4).border = thin_border
            ws.cell(row=cont, column=5).value = opening_amount
            ws.cell(row=cont, column=5).number_format = '#.00000'
            ws.cell(row=cont, column=5).border = thin_border
            listado_kardex, in_quantity, in_amount, out_quantity, out_amount = kardex_for_period(
                self, product, warehouse, start_date, end_date)
            total_quantity = opening_quantity + in_quantity - out_quantity
            total_amount = opening_amount + in_amount - out_amount
            ws.cell(row=cont, column=6).value = in_quantity
            ws.cell(row=cont, column=6).number_format = '#.00000'
            ws.cell(row=cont, column=6).border = thin_border
            ws.cell(row=cont, column=7).value = in_amount
            ws.cell(row=cont, column=7).number_format = '#.00000'
            ws.cell(row=cont, column=7).border = thin_border
            ws.cell(row=cont, column=8).value = out_quantity
            ws.cell(row=cont, column=8).number_format = '#.00000'
            ws.cell(row=cont, column=8).border = thin_border
            ws.cell(row=cont, column=9).value = out_amount
            ws.cell(row=cont, column=9).number_format = '#.00000'
            ws.cell(row=cont, column=9).border = thin_border
            ws.cell(row=cont, column=10).value = total_quantity
            ws.cell(row=cont, column=10).number_format = '#.00000'
            ws.cell(row=cont, column=10).border = thin_border
            ws.cell(row=cont, column=11).value = total_amount
            ws.cell(row=cont, column=11).number_format = '#.00000'
            ws.cell(row=cont, column=11).border = thin_border
            cont += 1
        return wb

    def get_normal_format_all(self, start_date, end_date, warehouse):
        productos = (Kardex.objects.filter(warehouse=warehouse).order_by('product')
                     .distinct('product__code')
                     .select_related('product__unit_of_measure'))
        wb = Workbook()
        ws = wb.active
        ws['E1'] = u'Almacén: ' + warehouse.description
        ws.merge_cells('E1:G1')
        ws['H1'] = 'Periodo: ' + start_date.strftime('%d/%m/%Y') + ' - ' + end_date.strftime('%d/%m/%Y')
        ws.merge_cells('H1:J1')
        ws['B3'] = 'FECHA'
        ws['C3'] = 'NRO_DOC'
        ws['D3'] = 'TIPO_MOV'
        ws['E3'] = 'CANT. ENT'
        ws['F3'] = 'PRE. ENT'
        ws['G3'] = 'VALOR. ENT'
        ws['H3'] = 'CANT. SAL'
        ws['I3'] = 'PRE. SAL'
        ws['J3'] = 'VALOR. SAL'
        ws['K3'] = 'CANT. TOT'
        ws['L3'] = 'PRE. TOT'
        ws['M3'] = 'VALOR. TOT'
        cont = 4
        last_records = Kardex.last_by_product([prod.product_id for prod in productos],
                                              before=start_date, warehouse=warehouse)
        self.kardex_batch = Product.kardex_by_batch([prod.product_id for prod in productos],
                                                    warehouse, start_date, end_date)
        for prod in productos:
            product = prod.product
            ws.cell(row=cont, column=2).value = 'Codigo: ' + product.code
            ws.merge_cells(start_row=cont, start_column=2, end_row=cont, end_column=3)
            ws.cell(row=cont, column=4).value = u" Denominación: " + product.description
            ws.merge_cells(start_row=cont, start_column=4, end_row=cont, end_column=10)
            ws.cell(row=cont, column=11).value = " Unidad: " + product.unit_of_measure.description
            ws.merge_cells(start_row=cont, start_column=11, end_row=cont, end_column=12)
            cont += 1
            try:
                kardex_inicial = last_records.get(product.pk)
                opening_quantity = kardex_inicial.total_quantity
                opening_amount = kardex_inicial.total_amount
            except AttributeError:
                opening_quantity = 0
                opening_amount = 0
            ws.cell(row=cont, column=8).value = "SALDO INICIAL:"
            ws.merge_cells(start_row=cont, start_column=8, end_row=cont, end_column=9)
            ws.cell(row=cont, column=10).value = "Cantidad: "
            ws.cell(row=cont, column=11).value = opening_quantity
            ws.cell(row=cont, column=11).number_format = '#.00000'
            ws.cell(row=cont, column=12).value = "Valor: "
            ws.cell(row=cont, column=13).value = opening_amount
            ws.cell(row=cont, column=13).number_format = '#.00000'
            cont += 1
            listado_kardex, in_quantity, in_amount, out_quantity, out_amount = kardex_for_period(
                self, product, warehouse, start_date, end_date)
            if len(listado_kardex) > 0:
                for kardex in listado_kardex:
                    ws.cell(row=cont, column=2).value = kardex.operation_date
                    ws.cell(row=cont, column=2).number_format = 'dd/mm/yyyy'
                    ws.cell(row=cont, column=3).value = kardex.movement.movement_id
                    ws.cell(row=cont, column=4).value = kardex.movement.movement_type.code
                    ws.cell(row=cont, column=5).value = kardex.in_quantity
                    ws.cell(row=cont, column=6).value = kardex.in_price
                    ws.cell(row=cont, column=6).number_format = '#.00000'
                    ws.cell(row=cont, column=7).value = kardex.in_amount
                    ws.cell(row=cont, column=7).number_format = '#.00000'
                    ws.cell(row=cont, column=8).value = kardex.out_quantity
                    ws.cell(row=cont, column=9).value = kardex.out_price
                    ws.cell(row=cont, column=9).number_format = '#.00000'
                    ws.cell(row=cont, column=10).value = kardex.out_amount
                    ws.cell(row=cont, column=10).number_format = '#.00000'
                    ws.cell(row=cont, column=11).value = kardex.total_quantity
                    ws.cell(row=cont, column=12).value = kardex.total_price
                    ws.cell(row=cont, column=12).number_format = '#.00000'
                    ws.cell(row=cont, column=13).value = kardex.total_amount
                    ws.cell(row=cont, column=13).number_format = '#.00000'
                    cont += 1
                ws.cell(row=cont, column=5).value = in_quantity
                ws.cell(row=cont, column=7).value = in_amount
                ws.cell(row=cont, column=7).number_format = '#.00000'
                ws.cell(row=cont, column=8).value = out_quantity
                ws.cell(row=cont, column=10).value = out_amount
                ws.cell(row=cont, column=10).number_format = '#.00000'
                ws.cell(row=cont, column=11).value = kardex.total_quantity
                ws.cell(row=cont, column=13).value = kardex.total_amount
                ws.cell(row=cont, column=13).number_format = '#.00000'
                cont += 2
            else:
                ws.cell(row=cont, column=5).value = 0
                ws.cell(row=cont, column=6).value = 0
                ws.cell(row=cont, column=6).number_format = '#.00000'
                ws.cell(row=cont, column=7).value = 0
                ws.cell(row=cont, column=7).number_format = '#.00000'
                ws.cell(row=cont, column=8).value = 0
                ws.cell(row=cont, column=9).value = 0
                ws.cell(row=cont, column=9).number_format = '#.00000'
                ws.cell(row=cont, column=10).value = 0
                ws.cell(row=cont, column=10).number_format = '#.00000'
                ws.cell(row=cont, column=11).value = 0
                ws.cell(row=cont, column=12).value = 0
                ws.cell(row=cont, column=12).number_format = '#.00000'
                ws.cell(row=cont, column=13).value = 0
                ws.cell(row=cont, column=13).number_format = '#.00000'
                cont += 1
                ws.cell(row=cont, column=5).value = 0
                ws.cell(row=cont, column=7).value = 0
                ws.cell(row=cont, column=7).number_format = '#.00000'
                ws.cell(row=cont, column=8).value = 0
                ws.cell(row=cont, column=10).value = 0
                ws.cell(row=cont, column=10).number_format = '#.00000'
                ws.cell(row=cont, column=11).value = opening_quantity
                ws.cell(row=cont, column=13).value = opening_amount
                ws.cell(row=cont, column=13).number_format = '#.00000'
                cont += 2
        return wb


def inventory_report(start_date):
    """Construye el libro de Excel del reporte de inventario."""
    product_group = ProductGroup.objects.filter(is_active=True).select_related('account')

    wb = Workbook()
    ws = wb.active

    ws.merge_cells('A2:H2')
    ws['A2'].alignment = Alignment(horizontal="center", vertical="center")
    ws['A2'].border = Border(left=Side(border_style="thin"), right=Side(border_style="thin"),
                             top=Side(border_style="thin"), bottom=Side(border_style="thin"))
    ws['A2'].fill = PatternFill(start_color='66FFCC', end_color='66FFCC', fill_type='solid')
    ws['A2'].font = Font(name='Calibri', size=11, bold=True)
    ws['A2'] = 'INVENTARIO AL ' + start_date.strftime('%d.%m.%y')

    ws.row_dimensions[3].height = 25

    ws['A3'].alignment = Alignment(horizontal="center", vertical="center")
    ws['A3'].border = Border(left=Side(border_style="thin"), right=Side(border_style="thin"),
                             top=Side(border_style="thin"), bottom=Side(border_style="thin"))
    ws['A3'].font = Font(name='Calibri', size=8, bold=True)
    ws['A3'] = 'CTA CONTABLE'

    ws['B3'].alignment = Alignment(horizontal="center", vertical="center")
    ws['B3'].border = Border(left=Side(border_style="thin"), right=Side(border_style="thin"),
                             top=Side(border_style="thin"), bottom=Side(border_style="thin"))
    ws['B3'].font = Font(name='Calibri', size=8, bold=True)
    ws['B3'] = 'CODIGO'

    ws['C3'].alignment = Alignment(horizontal="center", vertical="center")
    ws['C3'].border = Border(left=Side(border_style="thin"), right=Side(border_style="thin"),
                             top=Side(border_style="thin"), bottom=Side(border_style="thin"))
    ws['C3'].font = Font(name='Calibri', size=8, bold=True)
    ws['C3'] = 'PRODUCTO'

    ws['D3'].alignment = Alignment(horizontal="center", vertical="center")
    ws['D3'].border = Border(left=Side(border_style="thin"), right=Side(border_style="thin"),
                             top=Side(border_style="thin"), bottom=Side(border_style="thin"))
    ws['D3'].font = Font(name='Calibri', size=8, bold=True)
    ws['D3'] = 'DETALLE 1'

    ws['E3'].alignment = Alignment(horizontal="center", vertical="center")
    ws['E3'].border = Border(left=Side(border_style="thin"), right=Side(border_style="thin"),
                             top=Side(border_style="thin"), bottom=Side(border_style="thin"))
    ws['E3'].font = Font(name='Calibri', size=8, bold=True)
    ws['E3'] = 'CANTIDAD'

    ws['F3'].alignment = Alignment(horizontal="center", vertical="center")
    ws['F3'].border = Border(left=Side(border_style="thin"), right=Side(border_style="thin"),
                             top=Side(border_style="thin"), bottom=Side(border_style="thin"))
    ws['F3'].font = Font(name='Calibri', size=8, bold=True)
    ws['F3'] = 'MEDIDA'

    ws['G3'].alignment = Alignment(horizontal="center", vertical="center")
    ws['G3'].border = Border(left=Side(border_style="thin"), right=Side(border_style="thin"),
                             top=Side(border_style="thin"), bottom=Side(border_style="thin"))
    ws['G3'].font = Font(name='Calibri', size=8, bold=True)
    ws['G3'] = 'VALOR UNIT'

    ws['H3'].alignment = Alignment(horizontal="center", vertical="center")
    ws['H3'].border = Border(left=Side(border_style="thin"), right=Side(border_style="thin"),
                             top=Side(border_style="thin"), bottom=Side(border_style="thin"))
    ws['H3'].font = Font(name='Calibri', size=8, bold=True)
    ws['H3'] = 'VALOR TOTAL'
    ws.column_dimensions["A"].width = 15
    ws.column_dimensions["B"].width = 15
    ws.column_dimensions["C"].width = 40
    ws.column_dimensions["G"].width = 12
    ws.column_dimensions["H"].width = 12
    cont = 5
    total_final = 0
    inventory_summary = []
    for product_group in product_group:

        productos = list(Product.objects.filter(product_group=product_group)
                         .select_related('unit_of_measure'))
        bandera = " "
        temp_account = ""

        if productos:
            amount_sum = 0
            ws['A' + str(cont)].alignment = Alignment(horizontal="center")
            ws.merge_cells('A' + str(cont) + ':H' + str(cont))
            ws['A' + str(cont)].fill = PatternFill(start_color='F2DCDB', end_color='F2DCDB', fill_type='solid')
            ws.cell(row=cont, column=1).value = product_group.description
            bandera = product_group.description
            cont += 2
            last_records = Kardex.last_by_product(productos)
            for product in productos:
                try:
                    kardex = last_records.get(product.pk)
                    code = kardex.product.code
                    description = kardex.product.description
                    unit_of_measure = kardex.product.unit_of_measure.description
                    stock = kardex.total_quantity
                    price = kardex.total_price
                    amount = kardex.total_amount
                    detail = kardex.movement_line_number
                    amount_sum += amount

                except (Kardex.DoesNotExist, AttributeError):
                    code = product.code
                    description = product.description
                    unit_of_measure = product.unit_of_measure.code
                    stock = 0
                    price = 0
                    amount = 0
                    detail = ""
                ws.cell(row=cont, column=1).alignment = Alignment(horizontal="center")
                ws.cell(row=cont, column=1).border = Border(left=Side(border_style="thin"),
                                                            right=Side(border_style="thin"),
                                                            top=Side(border_style="thin"),
                                                            bottom=Side(border_style="thin"))
                ws.cell(row=cont, column=1).font = Font(name='Calibri', size=8)
                ws.cell(row=cont, column=1).value = product_group.account.account_number
                temp_account = product_group.account.account_number
                ws.cell(row=cont, column=2).alignment = Alignment(horizontal="center")
                ws.cell(row=cont, column=2).border = Border(left=Side(border_style="thin"),
                                                            right=Side(border_style="thin"),
                                                            top=Side(border_style="thin"),
                                                            bottom=Side(border_style="thin"))
                ws.cell(row=cont, column=2).font = Font(name='Calibri', size=8)
                ws.cell(row=cont, column=2).value = code

                ws.cell(row=cont, column=3).alignment = Alignment(horizontal="left")
                ws.cell(row=cont, column=3).border = Border(left=Side(border_style="thin"),
                                                            right=Side(border_style="thin"),
                                                            top=Side(border_style="thin"),
                                                            bottom=Side(border_style="thin"))
                ws.cell(row=cont, column=3).font = Font(name='Calibri', size=8)
                ws.cell(row=cont, column=3).value = description

                ws.cell(row=cont, column=4).alignment = Alignment(horizontal="center")
                ws.cell(row=cont, column=4).border = Border(left=Side(border_style="thin"),
                                                            right=Side(border_style="thin"),
                                                            top=Side(border_style="thin"),
                                                            bottom=Side(border_style="thin"))
                ws.cell(row=cont, column=4).font = Font(name='Calibri', size=8)
                ws.cell(row=cont, column=4).value = detail

                ws.cell(row=cont, column=5).alignment = Alignment(horizontal="right")
                ws.cell(row=cont, column=5).border = Border(left=Side(border_style="thin"),
                                                            right=Side(border_style="thin"),
                                                            top=Side(border_style="thin"),
                                                            bottom=Side(border_style="thin"))
                ws.cell(row=cont, column=5).font = Font(name='Calibri', size=8)
                ws.cell(row=cont, column=5).value = stock

                ws.cell(row=cont, column=6).alignment = Alignment(horizontal="center")
                ws.cell(row=cont, column=6).border = Border(left=Side(border_style="thin"),
                                                            right=Side(border_style="thin"),
                                                            top=Side(border_style="thin"),
                                                            bottom=Side(border_style="thin"))
                ws.cell(row=cont, column=6).font = Font(name='Calibri', size=8)
                ws.cell(row=cont, column=6).value = unit_of_measure

                temp_price = format(price, '.3f')
                if temp_price == '-0.000':
                    price = format(abs(price), '.3f')
                else:
                    price = format(price, '.3f')
                ws.cell(row=cont, column=7).alignment = Alignment(horizontal="right")
                ws.cell(row=cont, column=7).border = Border(left=Side(border_style="thin"),
                                                            right=Side(border_style="thin"),
                                                            top=Side(border_style="thin"),
                                                            bottom=Side(border_style="thin"))
                ws.cell(row=cont, column=7).font = Font(name='Calibri', size=8)
                ws.cell(row=cont, column=7).value = price
                ws.cell(row=cont, column=7).number_format = '#.000'
                temp_amount = format(amount, '.3f')
                if temp_amount == '-0.000':
                    amount = format(abs(amount), '.3f')
                else:
                    amount = format(amount, '.3f')
                ws.cell(row=cont, column=8).alignment = Alignment(horizontal="right")
                ws.cell(row=cont, column=8).border = Border(left=Side(border_style="thin"),
                                                            right=Side(border_style="thin"),
                                                            top=Side(border_style="thin"),
                                                            bottom=Side(border_style="thin"))
                ws.cell(row=cont, column=8).font = Font(name='Calibri', size=8)
                ws.cell(row=cont, column=8).value = amount
                ws.cell(row=cont, column=8).number_format = '#.000'

                cont = cont + 1
            temp_summary = [bandera, temp_account, amount_sum]
            inventory_summary.append(temp_summary)
            temp_amount_sum = format(amount_sum, '.3f')
            if temp_amount_sum == '-0.000':
                amount = format(abs(amount_sum), '.3f')
            else:
                amount = format(amount_sum, '.3f')
            ws.cell(row=cont, column=8).alignment = Alignment(horizontal="right")
            ws.cell(row=cont, column=8).border = Border(left=Side(border_style="thin"),
                                                        right=Side(border_style="thin"),
                                                        top=Side(border_style="thin"),
                                                        bottom=Side(border_style="thin"))
            ws.cell(row=cont, column=8).fill = PatternFill(start_color='DCE6F2', end_color='DCE6F2',
                                                           fill_type='solid')
            ws.cell(row=cont, column=8).font = Font(name='Calibri', size=8)
            ws.cell(row=cont, column=8).value = amount_sum
            ws.cell(row=cont, column=8).number_format = '#.000'
            total_final += amount_sum
            cont = cont + 2

    ws.cell(row=cont, column=6).fill = PatternFill(start_color='DCE6F2', end_color='DCE6F2', fill_type='solid')
    ws.cell(row=cont, column=6).border = Border(left=Side(border_style="thin"), right=Side(border_style="thin"),
                                                top=Side(border_style="thin"), bottom=Side(border_style="thin"))
    ws.cell(row=cont, column=7).alignment = Alignment(horizontal="right")
    ws.cell(row=cont, column=7).border = Border(left=Side(border_style="thin"), right=Side(border_style="thin"),
                                                top=Side(border_style="thin"), bottom=Side(border_style="thin"))
    ws.cell(row=cont, column=7).fill = PatternFill(start_color='DCE6F2', end_color='DCE6F2', fill_type='solid')
    ws.cell(row=cont, column=7).font = Font(name='Calibri', size=12)
    ws.cell(row=cont, column=7).value = "Monto Total  S/."

    temp_amount_sum = format(total_final, '.3f')
    if temp_amount_sum == '-0.000':
        amount = format(abs(total_final), '.3f')
    else:
        amount = format(total_final, '.3f')
    ws.cell(row=cont, column=8).alignment = Alignment(horizontal="right")
    ws.cell(row=cont, column=8).border = Border(left=Side(border_style="thin"), right=Side(border_style="thin"),
                                                top=Side(border_style="thin"), bottom=Side(border_style="thin"))
    ws.cell(row=cont, column=8).fill = PatternFill(start_color='DCE6F2', end_color='DCE6F2', fill_type='solid')
    ws.cell(row=cont, column=8).font = Font(name='Calibri', size=8)
    ws.cell(row=cont, column=8).value = total_final
    ws.cell(row=cont, column=8).number_format = '#.000'

    cont = cont + 4
    ws.merge_cells('A1262:H1262')
    ws.cell(row=cont - 1, column=1).alignment = Alignment(horizontal="center", vertical="center")
    ws.cell(row=cont - 1, column=1).border = Border(left=Side(border_style="thin"), right=Side(border_style="thin"),
                                                    top=Side(border_style="thin"), bottom=Side(border_style="thin"))
    ws.cell(row=cont - 1, column=1).fill = PatternFill(start_color='66FFCC', end_color='66FFCC', fill_type='solid')
    ws.cell(row=cont - 1, column=1).font = Font(name='Calibri', size=11, bold=True)
    ws.cell(row=cont - 1, column=1).value = 'INVENTARIO AL ' + start_date.strftime('%d.%m.%y')

    ws.row_dimensions[3].height = 25

    ws.cell(row=cont, column=1).alignment = Alignment(horizontal="center", vertical="center")
    ws.cell(row=cont, column=1).border = Border(left=Side(border_style="thin"), right=Side(border_style="thin"),
                                                top=Side(border_style="thin"), bottom=Side(border_style="thin"))
    ws.cell(row=cont, column=1).font = Font(name='Calibri', size=8, bold=True)
    ws.cell(row=cont, column=1).value = 'CTA CONTABLE'

    ws.cell(row=cont, column=2).alignment = Alignment(horizontal="center", vertical="center")
    ws.cell(row=cont, column=2).border = Border(left=Side(border_style="thin"), right=Side(border_style="thin"),
                                                top=Side(border_style="thin"), bottom=Side(border_style="thin"))
    ws.cell(row=cont, column=2).font = Font(name='Calibri', size=8, bold=True)
    ws.cell(row=cont, column=2).value = 'CODIGO'

    ws.cell(row=cont, column=3).alignment = Alignment(horizontal="center", vertical="center")
    ws.cell(row=cont, column=3).border = Border(left=Side(border_style="thin"), right=Side(border_style="thin"),
                                                top=Side(border_style="thin"), bottom=Side(border_style="thin"))
    ws.cell(row=cont, column=3).font = Font(name='Calibri', size=8, bold=True)
    ws.cell(row=cont, column=3).value = 'PRODUCTO'

    ws.cell(row=cont, column=4).alignment = Alignment(horizontal="center", vertical="center")
    ws.cell(row=cont, column=4).border = Border(left=Side(border_style="thin"), right=Side(border_style="thin"),
                                                top=Side(border_style="thin"), bottom=Side(border_style="thin"))
    ws.cell(row=cont, column=4).font = Font(name='Calibri', size=8, bold=True)
    ws.cell(row=cont, column=4).value = 'DETALLE 1'

    ws.cell(row=cont, column=5).alignment = Alignment(horizontal="center", vertical="center")
    ws.cell(row=cont, column=5).border = Border(left=Side(border_style="thin"), right=Side(border_style="thin"),
                                                top=Side(border_style="thin"), bottom=Side(border_style="thin"))
    ws.cell(row=cont, column=5).font = Font(name='Calibri', size=8, bold=True)
    ws.cell(row=cont, column=5).value = 'CANTIDAD'

    ws.cell(row=cont, column=6).alignment = Alignment(horizontal="center", vertical="center")
    ws.cell(row=cont, column=6).border = Border(left=Side(border_style="thin"), right=Side(border_style="thin"),
                                                top=Side(border_style="thin"), bottom=Side(border_style="thin"))
    ws.cell(row=cont, column=6).font = Font(name='Calibri', size=8, bold=True)
    ws.cell(row=cont, column=6).value = 'MEDIDA'

    ws.cell(row=cont, column=7).alignment = Alignment(horizontal="center", vertical="center")
    ws.cell(row=cont, column=7).border = Border(left=Side(border_style="thin"), right=Side(border_style="thin"),
                                                top=Side(border_style="thin"), bottom=Side(border_style="thin"))
    ws.cell(row=cont, column=7).font = Font(name='Calibri', size=8, bold=True)
    ws.cell(row=cont, column=7).value = 'VALOR UNIT'

    ws.cell(row=cont, column=8).alignment = Alignment(horizontal="center", vertical="center")
    ws.cell(row=cont, column=8).border = Border(left=Side(border_style="thin"), right=Side(border_style="thin"),
                                                top=Side(border_style="thin"), bottom=Side(border_style="thin"))
    ws.cell(row=cont, column=8).font = Font(name='Calibri', size=8, bold=True)
    ws.cell(row=cont, column=8).value = 'VALOR TOTAL'

    cont = cont + 1

    for summary in inventory_summary:
        ws.cell(row=cont, column=1).alignment = Alignment(horizontal="center")
        ws.cell(row=cont, column=1).border = Border(left=Side(border_style="thin"), right=Side(border_style="thin"),
                                                    top=Side(border_style="thin"), bottom=Side(border_style="thin"))
        ws.cell(row=cont, column=1).font = Font(name='Calibri', size=8)
        ws.cell(row=cont, column=1).value = ""

        ws.cell(row=cont, column=2).alignment = Alignment(horizontal="center")
        ws.cell(row=cont, column=2).border = Border(left=Side(border_style="thin"), right=Side(border_style="thin"),
                                                    top=Side(border_style="thin"), bottom=Side(border_style="thin"))
        ws.cell(row=cont, column=2).font = Font(name='Calibri', size=8)
        ws.cell(row=cont, column=2).value = summary[1]

        ws.cell(row=cont, column=3).alignment = Alignment(horizontal="left")
        ws.cell(row=cont, column=3).border = Border(left=Side(border_style="thin"), right=Side(border_style="thin"),
                                                    top=Side(border_style="thin"), bottom=Side(border_style="thin"))
        ws.cell(row=cont, column=3).font = Font(name='Calibri', size=8)
        ws.cell(row=cont, column=3).value = summary[0]

        ws.cell(row=cont, column=4).alignment = Alignment(horizontal="center")
        ws.cell(row=cont, column=4).border = Border(left=Side(border_style="thin"), right=Side(border_style="thin"),
                                                    top=Side(border_style="thin"), bottom=Side(border_style="thin"))
        ws.cell(row=cont, column=4).font = Font(name='Calibri', size=8)
        ws.cell(row=cont, column=4).value = ""

        ws.cell(row=cont, column=5).alignment = Alignment(horizontal="right")
        ws.cell(row=cont, column=5).border = Border(left=Side(border_style="thin"), right=Side(border_style="thin"),
                                                    top=Side(border_style="thin"), bottom=Side(border_style="thin"))
        ws.cell(row=cont, column=5).font = Font(name='Calibri', size=8)
        ws.cell(row=cont, column=5).value = summary[2]
        ws.cell(row=cont, column=5).number_format = '#.000'

        ws.cell(row=cont, column=6).alignment = Alignment(horizontal="center")
        ws.cell(row=cont, column=6).border = Border(left=Side(border_style="thin"), right=Side(border_style="thin"),
                                                    top=Side(border_style="thin"), bottom=Side(border_style="thin"))
        ws.cell(row=cont, column=6).font = Font(name='Calibri', size=8)
        ws.cell(row=cont, column=6).value = ""

        ws.cell(row=cont, column=7).border = Border(left=Side(border_style="thin"), right=Side(border_style="thin"),
                                                    top=Side(border_style="thin"), bottom=Side(border_style="thin"))
        ws.cell(row=cont, column=8).border = Border(left=Side(border_style="thin"), right=Side(border_style="thin"),
                                                    top=Side(border_style="thin"), bottom=Side(border_style="thin"))
        cont = cont + 1

    ws.cell(row=cont, column=4).fill = PatternFill(start_color='DCE6F2', end_color='DCE6F2', fill_type='solid')
    ws.cell(row=cont, column=4).border = Border(left=Side(border_style="thin"), right=Side(border_style="thin"),
                                                top=Side(border_style="thin"), bottom=Side(border_style="thin"))
    ws.cell(row=cont, column=4).alignment = Alignment(horizontal="right")
    ws.cell(row=cont, column=4).border = Border(left=Side(border_style="thin"), right=Side(border_style="thin"),
                                                top=Side(border_style="thin"), bottom=Side(border_style="thin"))
    ws.cell(row=cont, column=3).fill = PatternFill(start_color='DCE6F2', end_color='DCE6F2', fill_type='solid')
    ws.cell(row=cont, column=3).font = Font(name='Calibri', size=12)
    ws.cell(row=cont, column=3).value = "   TOTAL  S/."
    ws.cell(row=cont, column=3).alignment = Alignment(horizontal="right")
    ws.cell(row=cont, column=3).border = Border(left=Side(border_style="thin"), right=Side(border_style="thin"),
                                                top=Side(border_style="thin"), bottom=Side(border_style="thin"))
    ws.cell(row=cont, column=5).border = Border(left=Side(border_style="thin"), right=Side(border_style="thin"),
                                                top=Side(border_style="thin"), bottom=Side(border_style="thin"))
    ws.cell(row=cont, column=5).fill = PatternFill(start_color='DCE6F2', end_color='DCE6F2', fill_type='solid')
    ws.cell(row=cont, column=5).fill = PatternFill(start_color='DCE6F2', end_color='DCE6F2', fill_type='solid')
    ws.cell(row=cont, column=5).font = Font(name='Calibri', size=8)
    ws.cell(row=cont, column=5).value = total_final
    ws.cell(row=cont, column=5).number_format = '#.000'
    return wb
