# -*- coding: utf-8 -*- 
from reportlab.lib.pagesizes import letter, A4, landscape
from reportlab.platypus import SimpleDocTemplate, Paragraph, Image, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER,TA_LEFT, TA_JUSTIFY, TA_RIGHT
from reportlab.platypus import Table
from reportlab.lib import colors
from reportlab.lib.pagesizes import cm
from reportlab.platypus.flowables import Spacer, PageBreak
from django.conf import settings
import os
from io import BytesIO
from almacen.models import DetalleMovimiento, Kardex, Movimiento
from almacen.settings import EMPRESA, OFICINA_ADMINISTRACION, LOGISTICA
from django.db.models import Sum
import datetime
from productos.models import Producto, GrupoProductos

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
            proveedor = Paragraph(u"PROVEEDOR:",izquierda)
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



    def tabla_encabezado(self,valorizado):
        sp = ParagraphStyle('parrafos',
                            alignment=TA_CENTER,
                            fontSize=14,
                            fontName="Times-Roman")
        try:
            archivo_imagen = os.path.join(settings.MEDIA_ROOT, str(EMPRESA.logo))
            imagen = Image(archivo_imagen, width=90, height=50, hAlign='LEFT')
        except:
            imagen = Paragraph(u"LOGO", sp)
        if valorizado:
            titulo = Paragraph(u"REGISTRO DEL INVENTARIO PERMANENTE VALORIZADO", sp)
        else:
            titulo = Paragraph(u"REGISTRO DEL INVENTARIO PERMANENTE EN UNIDADES FÍSICAS", sp)

        encabezado = [[imagen,titulo]]
        tabla_encabezado = Table(encabezado, colWidths=[2 * cm, 23 * cm])
        return tabla_encabezado

    def tabla_detalle_unidades_fisicas(self, producto, desde, hasta, almacen):
        tabla = []
        encab_prim = [u"DOCUMENTO DE TRASLADO, COMPROBANTE DE PAGO,\n DOCUMENTO INTERNO O SIMILAR",
                        "",
                        "",
                        "",
                       u"TIPO DE \n OPERACIÓN \n (TABLA 12)",
                       u"ENTRADAS",
                       u"SALIDAS",
                       u"SALDO FINAL"]
        tabla.append(encab_prim)
        encab_seg = ["FECHA", "TIPO (TABLA 10)","SERIE","NÚMERO","","","",""]
        tabla.append(encab_seg)
        try:
            kardex_inicial = Kardex.objects.filter(producto=producto,
                                                   almacen=almacen,
                                                   fecha_operacion__lt=desde).latest('fecha_operacion')
            cant_saldo_inicial = kardex_inicial.cantidad_total
        except:
            cant_saldo_inicial = 0
        saldo_inicial = ['','00','SALDO','INICIAL','16',format(0,'.5f'),format(0,'.5f'),format(cant_saldo_inicial,'.5f')]
        tabla.append(saldo_inicial)
        listado_kardex, cantidad_ingreso, valor_ingreso, cantidad_salida, valor_salida, cantidad_total, valor_total = producto.obtener_kardex(
            almacen,
            desde,
            hasta)

        for kardex in listado_kardex:
            try:
                tipo_documento = kardex.movimiento.tipo_documento.codigo_sunat
            except:
                tipo_documento = '-'
            try:
                tipo_movimiento = kardex.movimiento.tipo_movimiento.codigo_sunat
            except:
                tipo_movimiento = "-"

            tabla.append([kardex.fecha_operacion.strftime('%d/%m/%Y'),
                          tipo_documento,
                          kardex.movimiento.serie,
                          kardex.movimiento.numero,
                          tipo_movimiento,
                          format(kardex.cantidad_ingreso,'.5f'),
                          format(kardex.cantidad_salida,'.5f'),
                          format(kardex.cantidad_total,'.5f')])
        totales = ['','','','',"TOTALES",format(cantidad_ingreso,'.5f'),format(cantidad_salida,'.5f'),format(cantidad_total,'.5f')]
        tabla.append(totales)
        tabla_detalle = Table(tabla, colWidths=[3 * cm, 4 * cm,3 * cm, 3 * cm,3 * cm, 3.5 * cm,3.5 * cm, 3.5 * cm])
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
        tabla_detalle.setStyle(style)
        return tabla_detalle

    def tabla_detalle_consolidado_productos(self, producto, desde, hasta, almacen, print_cabecera):

        tabla = []
        if print_cabecera:
            encabezado = [u"CODIGO", u"NOMBRE", u"CANT. INICIAL", u"VALOR INICIAL", u"CANT. ENT", u"VALOR. ENT",
                          u"CANT. SAL", u"VALOR. SAL.", u"CANT. TOT", u"VALOR. TOT"]
            tabla.append(encabezado)
        try:
            kardex_inicial = Kardex.objects.filter(producto=producto,
                                                   almacen=almacen,
                                                   fecha_operacion__lt=desde).latest('fecha_operacion')
            cant_saldo_inicial = kardex_inicial.cantidad_total
            valor_saldo_inicial = kardex_inicial.valor_total
        except:
            cant_saldo_inicial = 0
            valor_saldo_inicial = 0

        from almacen.views import ReporteKardex
        listado_kardex, cantidad_ingreso, valor_ingreso, cantidad_salida, valor_salida, cantidad_total, valor_total = ReporteKardex.obtener_kardex_producto(
            producto,
            almacen,
            desde,
            hasta)
        cantidad_total = cant_saldo_inicial + cantidad_ingreso - cantidad_salida
        valor_total = valor_saldo_inicial + valor_ingreso - valor_salida

        registro=[producto.codigo,
                  producto.descripcion,
                  format(cant_saldo_inicial,'.5f'),
                  format(valor_saldo_inicial,'.5f'),
                  format(cantidad_ingreso,'.5f'),
                  format(valor_ingreso,'.5f'),
                  format(cantidad_salida,'.5f'),
                  format(valor_salida,'.5f'),
                  format(cantidad_total,'.5f'),
                  format(valor_total,'.5f')]
        tabla.append(registro)
        tabla_detalle = Table(tabla, colWidths=[2.2 * cm, 8 * cm,2.3 * cm, 2.3 * cm,2 * cm, 2 * cm,2 * cm, 2 * cm,2 * cm, 2 * cm])
        style = TableStyle(
            [
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('ALIGN', (2, 0), (-1, -1), 'RIGHT'),
                ('TEXTFONT', (0, 0), (-1, -1), 'Times-Roman'),
                ('FONTSIZE', (0, 0), (-1, -1), 8),
            ]
        )
        tabla_detalle.setStyle(style)
        return tabla_detalle

    def tabla_detalle_consolidado_grupo(self, grupo, desde, hasta, almacen, print_cabecera):

        tabla = []
        if print_cabecera:
            encabezado = [u"CODIGO", u"NOMBRE", u"CTA_CONT", u"CANT. INICIAL", u"VALOR INICIAL", u"CANT. ENT", u"VALOR. ENT",
                          u"CANT. SAL", u"VALOR. SAL.", u"CANT. TOT", u"VALOR. TOT"]
            tabla.append(encabezado)
        try:
            kardex_inicial = Kardex.objects.filter(producto__grupo_productos=grupo,
                                                   almacen=almacen,
                                                   fecha_operacion__lt=desde).latest('fecha_operacion')
            cant_saldo_inicial = kardex_inicial.cantidad_total
            valor_saldo_inicial = kardex_inicial.valor_total
        except:
            cant_saldo_inicial = 0
            valor_saldo_inicial = 0

        from almacen.views import ReporteKardex
        listado_kardex, cantidad_ingreso, valor_ingreso, cantidad_salida, valor_salida = ReporteKardex.obtener_kardex_grupo(
            grupo,
            almacen,
            desde,
            hasta)
        cantidad_total = cant_saldo_inicial + cantidad_ingreso - cantidad_salida
        valor_total = valor_saldo_inicial + valor_ingreso - valor_salida

        registro=[grupo.codigo,
                  grupo.descripcion,
                  grupo.ctacontable.cuenta,
                  format(cant_saldo_inicial,'.5f'),
                  format(valor_saldo_inicial,'.5f'),
                  format(cantidad_ingreso,'.5f'),
                  format(valor_ingreso,'.5f'),
                  format(cantidad_salida,'.5f'),
                  format(valor_salida,'.5f'),
                  format(cantidad_total,'.5f'),
                  format(valor_total,'.5f')]
        tabla.append(registro)
        tabla_detalle = Table(tabla, colWidths=[1.4 * cm, 7 * cm, 1.8 * cm, 2.2 * cm, 2.3 * cm,2.3 * cm, 2.3 * cm,2.3 * cm, 2.4 * cm,2.3 * cm, 2.5 * cm])
        style = TableStyle(
            [
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('ALIGN', (2, 0), (-1, -1), 'RIGHT'),
                ('TEXTFONT', (0, 0), (-1, -1), 'Times-Roman'),
                ('FONTSIZE', (0, 0), (-1, -1), 8),
            ]
        )
        tabla_detalle.setStyle(style)
        return tabla_detalle

    def tabla_detalle_valorizado(self, producto, desde, hasta, almacen):
        tabla = []
        encab_prim = [u"DOCUMENTO DE TRASLADO, COMPROBANTE DE PAGO,\n DOCUMENTO INTERNO O SIMILAR",
                        "","","",
                       u"TIPO DE \n OPERACIÓN \n (TABLA 12)",
                       u"ENTRADAS","","",
                       u"SALIDAS","","",
                       u"SALDO FINAL","",""]
        tabla.append(encab_prim)
        encab_seg = ["", "", "", "","",
                      "CANTIDAD", "COSTO\nUNITARIO", "TOTAL",
                      "CANTIDAD", "COSTO\nUNITARIO", "TOTAL",
                      "CANTIDAD", "COSTO\nUNITARIO", "TOTAL"]
        tabla.append(encab_seg)
        encab_terc = ["FECHA", "TIPO\n(TABLA 10)","SERIE","NÚMERO",
                     "","","",
                     "","","",
                     "","",""]
        tabla.append(encab_terc)
        try:
            kardex_inicial = Kardex.objects.filter(producto=producto,
                                                   almacen=almacen,
                                                   fecha_operacion__lt=desde).latest('fecha_operacion')
            cant_saldo_inicial = kardex_inicial.cantidad_total
            valor_saldo_inicial = kardex_inicial.valor_total
        except:
            cant_saldo_inicial = 0
            valor_saldo_inicial = 0
        try:
            precio_saldo_inicial = valor_saldo_inicial / cant_saldo_inicial
        except:
            precio_saldo_inicial = 0
        saldo_inicial = ['','00','SALDO','INICIAL','16',
                         format(0,'.5f'),format(0,'.5f'),format(0,'.5f'),
                         format(0,'.5f'),format(0,'.5f'),format(0,'.5f'),
                         format(cant_saldo_inicial,'.5f'),format(precio_saldo_inicial,'.5f'),format(valor_saldo_inicial,'.5f')]
        tabla.append(saldo_inicial)
        listado_kardex, cantidad_ingreso, valor_ingreso, cantidad_salida, valor_salida, cantidad_total, valor_total = producto.obtener_kardex(
            almacen,
            desde,
            hasta)

        for kardex in listado_kardex:
            try:
                tipo_documento = kardex.movimiento.tipo_documento.codigo_sunat
            except:
                tipo_documento = '-'
            try:
                tipo_movimiento = kardex.movimiento.tipo_movimiento.codigo_sunat
            except:
                tipo_movimiento = "-"

            tabla.append([kardex.fecha_operacion.strftime('%d/%m/%Y'),
                          tipo_documento,
                          kardex.movimiento.serie,
                          kardex.movimiento.numero,
                          tipo_movimiento,
                          format(kardex.cantidad_ingreso,'.5f'),
                          format(kardex.precio_ingreso, '.5f'),
                          format(kardex.valor_ingreso, '.5f'),
                          format(kardex.cantidad_salida,'.5f'),
                          format(kardex.precio_salida, '.5f'),
                          format(kardex.valor_salida, '.5f'),
                          format(kardex.cantidad_total,'.5f'),
                          format(kardex.precio_total, '.5f'),
                          format(kardex.valor_total, '.5f')])
        try:
            t_precio_i = valor_ingreso / cantidad_ingreso
        except:
            t_precio_i = 0
        try:
            t_precio_s = valor_salida / cantidad_salida
        except:
            t_precio_s = 0
        try:
            t_precio_t = valor_total / cantidad_total
        except:
            t_precio_t = 0
        totales = ['','','','',"TOTALES",
                   format(cantidad_ingreso,'.5f'),format(t_precio_i,'.5f'),format(valor_ingreso,'.5f'),
                   format(cantidad_salida,'.5f'),format(t_precio_s,'.5f'),format(valor_salida,'.5f'),
                   format(cantidad_total,'.5f'),format(t_precio_t,'.5f'),format(valor_total,'.5f')]
        tabla.append(totales)
        tabla_detalle = Table(tabla)
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
        tabla_detalle.setStyle(style)
        return tabla_detalle

    def imprimir_formato_sunat_unidades_fisicas_producto(self, producto, desde, hasta, almacen):
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
        elements.append(self.tabla_encabezado(False))
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
        unidad = Paragraph(u"MÉTODO DE VALUACIÓN: PEPS",
                           izquierda)
        elements.append(unidad)
        elements.append(Spacer(1, 0.5 * cm))
        elements.append(self.tabla_detalle_unidades_fisicas(producto, desde, hasta, almacen))
        doc.build(elements)
        pdf = buffer.getvalue()
        buffer.close()
        return pdf

    def imprimir_formato_sunat_valorizado_producto(self, producto, desde, hasta, almacen):
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
        elements.append(self.tabla_encabezado(True))
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
        unidad = Paragraph(u"MÉTODO DE VALUACIÓN: PEPS",
                           izquierda)
        elements.append(unidad)
        elements.append(Spacer(1, 0.5 * cm))
        elements.append(self.tabla_detalle_valorizado(producto, desde, hasta, almacen))
        doc.build(elements)
        pdf = buffer.getvalue()
        buffer.close()
        return pdf

    def imprimir_formato_sunat_unidades_fisicas_todos(self, desde, hasta, almacen):
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
        productos = Producto.objects.all().order_by('descripcion')
        for producto in productos:
            elements.append(self.tabla_encabezado(False))
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
            unidad = Paragraph(u"MÉTODO DE VALUACIÓN: PEPS",
                               izquierda)
            elements.append(unidad)
            elements.append(Spacer(1, 0.5 * cm))
            elements.append(self.tabla_detalle_unidades_fisicas(producto, desde, hasta, almacen))
            elements.append(PageBreak())
        doc.build(elements)
        pdf = buffer.getvalue()
        buffer.close()
        return pdf

    def imprimir_formato_consolidado_productos(self, desde, hasta, almacen):
        y = 300
        buffer = self.buffer
        derecha = ParagraphStyle('parrafos',
                                   alignment=TA_RIGHT,
                                   fontSize=12,
                                   fontName="Times-Roman")
        centro = ParagraphStyle('parrafos',
                                   alignment=TA_CENTER,
                                   fontSize=12,
                                   fontName="Times-Roman")
        doc = SimpleDocTemplate(buffer,
                                rightMargin=50,
                                leftMargin=50,
                                topMargin=20,
                                bottomMargin=50,
                                pagesize=self.pagesize)

        elements = []
        productos = Producto.objects.all().order_by('descripcion')
        posicion=1
        print_cabecera=False
        for producto in productos:
            if posicion==1 or posicion % 25 == 0:
                if posicion != 1:elements.append(PageBreak())
                titulo_almacen = Paragraph(u"ALMACÉN: " + almacen.descripcion, centro)
                elements.append(titulo_almacen)
                periodo = Paragraph("PERIODO: " + desde.strftime('%d/%m/%Y') + ' - ' + hasta.strftime('%d/%m/%Y'),derecha)
                elements.append(periodo)
                elements.append(Spacer(1, 0.5 * cm))
                print_cabecera=True
            elements.append(self.tabla_detalle_consolidado_productos(producto, desde, hasta, almacen, print_cabecera))
            posicion += 1
            print_cabecera = False

        doc.build(elements)
        pdf = buffer.getvalue()
        buffer.close()
        return pdf

    def imprimir_formato_consolidado_grupos(self, desde, hasta, almacen):
        y = 300
        buffer = self.buffer
        derecha = ParagraphStyle('parrafos',
                                   alignment=TA_RIGHT,
                                   fontSize=12,
                                   fontName="Times-Roman")
        centro = ParagraphStyle('parrafos',
                                   alignment=TA_CENTER,
                                   fontSize=12,
                                   fontName="Times-Roman")
        doc = SimpleDocTemplate(buffer,
                                rightMargin=50,
                                leftMargin=50,
                                topMargin=20,
                                bottomMargin=50,
                                pagesize=self.pagesize)

        elements = []
        grupos = GrupoProductos.objects.filter(estado=True, son_productos=True)
        posicion=1
        print_cabecera=False
        for grupo in grupos:
            if posicion==1 or posicion % 25 == 0:
                if posicion != 1:elements.append(PageBreak())
                titulo_almacen = Paragraph(u"ALMACÉN: " + almacen.descripcion, centro)
                elements.append(titulo_almacen)
                periodo = Paragraph("PERIODO: " + desde.strftime('%d/%m/%Y') + ' - ' + hasta.strftime('%d/%m/%Y'),derecha)
                elements.append(periodo)
                elements.append(Spacer(1, 0.5 * cm))
                print_cabecera=True
            elements.append(self.tabla_detalle_consolidado_grupo(grupo, desde, hasta, almacen, print_cabecera))
            posicion += 1
            print_cabecera = False

        doc.build(elements)
        pdf = buffer.getvalue()
        buffer.close()
        return pdf

    def imprimir_formato_sunat_valorizado_todos(self, desde, hasta, almacen):
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
        productos = Producto.objects.all().order_by('descripcion')
        for producto in productos:
            elements.append(self.tabla_encabezado(True))
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
            unidad = Paragraph(u"MÉTODO DE VALUACIÓN: PEPS",
                               izquierda)
            elements.append(unidad)
            elements.append(Spacer(1, 0.5 * cm))
            elements.append(self.tabla_detalle_valorizado(producto, desde, hasta, almacen))
            elements.append(PageBreak())
        doc.build(elements)
        pdf = buffer.getvalue()
        buffer.close()
        return pdf
