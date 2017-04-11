# -*- coding: utf-8 -*- 
from reportlab.lib.pagesizes import letter, A4, landscape
from reportlab.platypus import SimpleDocTemplate, Paragraph, Image, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER,TA_LEFT, TA_JUSTIFY
from reportlab.platypus import Table
from reportlab.lib import colors
from reportlab.lib.pagesizes import cm
from reportlab.platypus.flowables import Spacer
from django.conf import settings
import os
from io import BytesIO
from almacen.models import DetalleMovimiento
from almacen.settings import EMPRESA, OFICINA_ADMINISTRACION, LOGISTICA

class ReporteMovimiento():
    
    def __init__(self, pagesize, movimiento):
        self.movimiento = movimiento
        self.buffer = BytesIO()
        if pagesize == 'A4':
            self.pagesize = A4
        elif pagesize == 'Letter':
            self.pagesize = letter
        self.width, self.height = self.pagesize
        
    def tabla_encabezado(self, styles):
        movimiento = self.movimiento        
        sp = ParagraphStyle('parrafos',
                            alignment = TA_CENTER,
                            fontSize = 14,
                            fontName="Times-Roman")
        try:
            archivo_imagen = os.path.join(settings.MEDIA_ROOT,str(EMPRESA.logo))
            imagen = Image(archivo_imagen, width=90, height=50,hAlign='LEFT')
        except:
            imagen = Paragraph(u"LOGO", sp)
        
        if movimiento.tipo_movimiento.incrementa:
            nota = Paragraph(u"NOTA DE INGRESO N°", sp)
        else:
            nota = Paragraph(u"NOTA DE SALIDA N°", sp)
        id_movimiento = Paragraph(movimiento.id_movimiento, sp)
        fecha = Paragraph("FECHA: "+movimiento.fecha_operacion.strftime('%d/%m/%y'), sp)        
        encabezado = [[imagen,nota,fecha],
                      ['',id_movimiento,'']
                      ]
        tabla_encabezado = Table(encabezado,colWidths=[4 * cm, 9 * cm, 6 * cm])
        tabla_encabezado.setStyle(TableStyle(
            [
                ('VALIGN',(0,0),(2,0),'CENTER'),
                ('VALIGN',(1,1),(2,1),'TOP'),                
                ('SPAN',(0,0),(0,1)),                        
            ]
        ))
        return tabla_encabezado
    
    def tabla_datos(self, styles):
        movimiento = self.movimiento
        izquierda = ParagraphStyle('parrafos',
                            alignment = TA_LEFT,
                            fontSize = 10,
                            fontName="Times-Roman")
        try:
            if movimiento.referencia.cotizacion is not None:
                proveedor = Paragraph(u"PROVEEDOR: "+movimiento.referencia.cotizacion.proveedor.razon_social,izquierda)
            else:
                proveedor = Paragraph(u"PROVEEDOR: "+movimiento.referencia.proveedor.razon_social,izquierda)
        except:
            proveedor = Paragraph(u"PROVEEDOR: SATP",izquierda)
        operacion = Paragraph(u"OPERACIÓN: "+movimiento.tipo_movimiento.descripcion,izquierda)
        almacen = Paragraph(u"ALMACÉN: "+movimiento.almacen.codigo+"-"+movimiento.almacen.descripcion,izquierda)
        try:
            orden_compra = Paragraph(u"ORDEN DE COMPRA: "+movimiento.referencia.codigo,izquierda)            
        except:
            orden_compra = Paragraph(u"REFERENCIA: -",izquierda)
        try:
            documento = Paragraph(u"DOCUMENTO: "+movimiento.tipo_documento.descripcion + " SERIE:" + movimiento.serie + u" NÚMERO:" + movimiento.numero,
                                  izquierda)
        except:
            documento = ""
        try:
            pedido = Paragraph(u"PEDIDO: "+movimiento.pedido.codigo, izquierda)
        except:
            pedido = ""        
        encabezado = [[operacion,''],
                      [almacen,''],
                      [proveedor,''],
                      [orden_compra,''],
                      [documento,''],
                      [pedido,'']]
        tabla_datos = Table(encabezado,colWidths=[11 * cm, 9 * cm])
        tabla_datos.setStyle(TableStyle(
            [                
                                                             
            ]
        ))
        return tabla_datos        
    
    def tabla_detalle(self):
        movimiento = self.movimiento
        encabezados = ['Item', 'Cantidad', 'Unidad', u'Descripción','Precio','Total']
        detalles = DetalleMovimiento.objects.filter(movimiento=movimiento).order_by('pk')
        sp = ParagraphStyle('parrafos')
        sp.alignment = TA_JUSTIFY 
        sp.fontSize = 8
        sp.fontName="Times-Roman"        
        lista_detalles = []
        for detalle in detalles:
            tupla_producto = [Paragraph(str(detalle.nro_detalle),sp), 
                              Paragraph(str(detalle.cantidad), sp),
                              Paragraph(detalle.producto.unidad_medida.codigo,sp),
                              Paragraph(detalle.producto.descripcion, sp),
                              Paragraph(str(detalle.precio),sp),
                              Paragraph(str(round(detalle.valor,5)),sp)]
            lista_detalles.append(tupla_producto)
        adicionales = [('','','','','')] * (15-len(lista_detalles))
        tabla_detalle = Table([encabezados] + lista_detalles,colWidths=[1.5 * cm, 2.5 * cm, 1.5 * cm,10* cm, 2 * cm, 2.5 * cm])
        style = TableStyle(
            [
                ('GRID', (0, 0), (-1, -1), 1, colors.black), 
                ('FONTSIZE', (0, 0), (-1, -1), 8),  
                ('ALIGN',(4,0),(-1,-1),'RIGHT'),            
            ]
        )
        tabla_detalle.setStyle(style)
        return tabla_detalle
    
    def tabla_total(self):
        movimiento = self.movimiento
        izquierda = ParagraphStyle('parrafos',
                            alignment = TA_LEFT,
                            fontSize = 10,
                            fontName="Times-Roman")

        texto_total = Paragraph("Total: ",izquierda)
        total = Paragraph(str(round(movimiento.total,2)),izquierda)
        total = [['',texto_total, total]]
        tabla_total = Table(total,colWidths=[15.5 * cm,2 * cm,2.5 * cm])
        tabla_total.setStyle(TableStyle(
            [
                ('GRID', (2, 0), (2, 0), 1, colors.black),
                ('FONTSIZE', (0, 0), (-1, -1), 8),
                ('ALIGN',(0,0),(-1,-1),'RIGHT'),
            ]
        ))
        return tabla_total
    
    def tabla_observaciones(self):
        movimiento = self.movimiento
        p = ParagraphStyle('parrafos',
                           alignment = TA_JUSTIFY,
                           fontSize = 8,
                           fontName="Times-Roman")
        obs=Paragraph("OBSERVACIONES: "+movimiento.observaciones,p)
        observaciones = [[obs]]
        tabla_observaciones = Table(observaciones,colWidths=[20 * cm], rowHeights=1.8 * cm)
        tabla_observaciones.setStyle(TableStyle(
            [
                ('GRID', (0, 0), (0, 2), 1, colors.black),
                ('FONTSIZE', (0, 0), (-1, -1), 8),
                ('ALIGN',(0,0),(-1,-1),'LEFT'),
                ('VALIGN',(0,0),(-1,-1),'TOP'),
            ]
        ))
        return tabla_observaciones  
    
    def tabla_firmas(self):
        movimiento = self.movimiento
        izquierda = ParagraphStyle('parrafos',
                            alignment = TA_CENTER,
                            fontSize = 8,
                            fontName="Times-Roman")
        nombre_oficina_administracion = Paragraph(OFICINA_ADMINISTRACION.nombre,izquierda)
        nombre_oficina_logistica = Paragraph(LOGISTICA.nombre,izquierda)
        if movimiento.tipo_movimiento.incrementa:            
            total = [[nombre_oficina_administracion,'', nombre_oficina_logistica]]
            tabla_firmas = Table(total,colWidths=[7 * cm,4 * cm,7 * cm])
            tabla_firmas.setStyle(TableStyle(
                [
                    ("LINEABOVE", (0,0), (0,0), 1, colors.black),
                    ("LINEABOVE", (2,0), (2,0), 1, colors.black),
                    ('VALIGN',(0,0),(-1,-1),'TOP'),
                ]
            ))
        else:
            solicitante = Paragraph('SOLICITANTE',izquierda)
            total = [[nombre_oficina_administracion,'',nombre_oficina_logistica,'',solicitante]]
            tabla_firmas = Table(total,colWidths=[5 * cm, 1 * cm, 5 * cm, 1 * cm, 5 * cm])
            tabla_firmas.setStyle(TableStyle(
                [
                    ("LINEABOVE", (0,0), (0,0), 1, colors.black),
                    ("LINEABOVE", (2,0), (2,0), 1, colors.black),
                    ("LINEABOVE", (4,0), (4,0), 1, colors.black),
                    #("LINEABOVE", (2,0), (2,0), 1, colors.black),
                    ('VALIGN',(0,0),(-1,-1),'TOP'),
                ]
            ))
        
        return tabla_firmas
    
    def pie_pagina(self, canvas, doc):
        canvas.saveState()
        canvas.setFont('Times-Roman',10)
        canvas.drawCentredString(300, 20, EMPRESA.direccion())
        canvas.restoreState()
    
    def imprimir(self):
        y=300
        buffer = self.buffer
        izquierda = ParagraphStyle('parrafos',
                                   alignment = TA_LEFT,
                                   fontSize = 10,
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
        elements.append(Spacer(1,0.25 * cm))
        elements.append(self.tabla_total())   
        elements.append(Spacer(1, 0.25 * cm))     
        elements.append(self.tabla_observaciones())
        elements.append(Spacer(1, 4 * cm))
        elements.append(self.tabla_firmas())        
        doc.build(elements, onFirstPage=self.pie_pagina, onLaterPages=self.pie_pagina)
        pdf = buffer.getvalue()
        buffer.close()
        return pdf


class ReporteKardexPDF():

    def __init__(self, pagesize):
        self.buffer = BytesIO()
        if pagesize == 'A4':
            self.pagesize = landscape(A4)
        elif pagesize == 'Letter':
            self.pagesize = letter
        self.width, self.height = self.pagesize

    def tabla_encabezado(self, styles, desde, hasta, producto):
        sp = ParagraphStyle('parrafos',
                            alignment=TA_CENTER,
                            fontSize=14,
                            fontName="Times-Roman")
        try:
            archivo_imagen = os.path.join(settings.MEDIA_ROOT, str(EMPRESA.logo))
            imagen = Image(archivo_imagen, width=90, height=50, hAlign='LEFT')
        except:
            imagen = Paragraph(u"LOGO", sp)

        titulo = Paragraph(u"REGISTRO DEL INVENTARIO PERMANENTE EN UNIDADES FÍSICAS", sp)

        encabezado = [[imagen, titulo]]
        tabla_encabezado = Table(encabezado, colWidths=[4 * cm, 19 * cm])
        """tabla_encabezado.setStyle(TableStyle(
            [
                ('ALIGN', (0, 0), (2, 1), 'CENTER'),
                ('VALIGN', (0, 0), (2, 0), 'CENTER'),
                ('VALIGN', (1, 1), (2, 1), 'TOP'),
                ('SPAN', (0, 0), (0, 1)),

            ]
        ))"""
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
        except:
            telefono = Paragraph(u"TELÉFONO: -", izquierda)
        try:
            referencia = Paragraph(
                u"REFERENCIA: " + orden.cotizacion.requerimiento.codigo + " - " + orden.cotizacion.requerimiento.oficina.nombre,
                izquierda)
        except:
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
            except:
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
            [Paragraph(EMPRESA.direccion(), p), Paragraph(u"INMEDIATA", p), Paragraph(orden.forma_pago.descripcion, p),
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
                          Facturar a nombre de """ + smart_str(EMPRESA.razon_social), p),
            Paragraph("El " + smart_str(EMPRESA.razon_social) + """, se reserva el derecho de devolver
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

    def imprimir_formato_sunat_unidades_fisicas(self,desde,hasta,producto):
        y = 300
        buffer = self.buffer
        izquierda = ParagraphStyle('parrafos',
                                   alignment=TA_LEFT,
                                   fontSize=12,
                                   fontName="Times-Roman")
        doc = SimpleDocTemplate(buffer,
                                rightMargin=50,
                                leftMargin=50,
                                topMargin=20,
                                bottomMargin=50,
                                pagesize=self.pagesize)

        elements = []
        styles = getSampleStyleSheet()
        elements.append(self.tabla_encabezado(styles,desde,hasta,producto))
        elements.append(Spacer(1, 0.5 * cm))
        periodo = Paragraph("PERIODO: " + desde.strftime('%d/%m/%Y') + ' - ' + hasta.strftime('%d/%m/%Y'), izquierda)
        elements.append(periodo)
        elements.append(Spacer(1, 0.25 * cm))
        ruc = Paragraph(u"RUC:" + EMPRESA.ruc, izquierda)
        elements.append(ruc)
        elements.append(Spacer(1, 0.25 * cm))
        razon_social = Paragraph(u"APELLIDOS Y NOMBRES, DENOMINACIÓN O RAZÓN SOCIAL: " + EMPRESA.razon_social, izquierda)
        elements.append(razon_social)
        elements.append(Spacer(1, 0.25 * cm))
        direccion = Paragraph(u"ESTABLECIMIENTO (1): " + EMPRESA.direccion(), izquierda)
        elements.append(direccion)
        elements.append(Spacer(1, 0.25 * cm))
        codigo = Paragraph(u"CÓDIGO DE LA EXISTENCIA: " + producto.codigo, izquierda)
        elements.append(codigo)
        elements.append(Spacer(1, 0.25 * cm))
        tipo = Paragraph(u"TIPO (TABLA 5): " + producto.tipo_existencia.codigo_sunat + " - " + producto.tipo_existencia.descripcion,
                         izquierda)
        elements.append(tipo)
        elements.append(Spacer(1, 0.25 * cm))
        descripcion = Paragraph(u"DESCRIPCIÓN: " + producto.descripcion, izquierda)
        elements.append(descripcion)
        elements.append(Spacer(1, 0.25 * cm))
        unidad = Paragraph(u"CÓDIGO DE LA UNIDAD DE MEDIDA (TABLA 6): " + producto.unidad_medida.codigo + " - " + producto.unidad_medida.descripcion,
                           izquierda)
        elements.append(unidad)
        elements.append(Spacer(1, 0.25 * cm))
        doc.build(elements)
        pdf = buffer.getvalue()
        buffer.close()
        return pdf