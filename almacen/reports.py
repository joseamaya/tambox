# -*- coding: utf-8 -*- 
from reportlab.lib.pagesizes import letter, A4, landscape
from reportlab.platypus import SimpleDocTemplate, Paragraph, Image, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER,TA_LEFT, TA_JUSTIFY
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

from productos.models import Producto


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

    def obtener_kardex(self, producto, almacen, desde, hasta):
        listado_kardex = Kardex.objects.filter(almacen = almacen,
                                               movimiento__estado = Movimiento.STATUS.ACT,
                                               fecha_operacion__gte=desde,
                                               fecha_operacion__lte=hasta,
                                               producto = producto).order_by('producto__descripcion',
                                                                           'fecha_operacion',
                                                                           'cantidad_salida',
                                                                           'created')
        if len(listado_kardex)>0:
            cantidad_ingreso = listado_kardex.aggregate(Sum('cantidad_ingreso'))
            cantidad_salida = listado_kardex.aggregate(Sum('cantidad_salida'))
            cantidad_total = listado_kardex.aggregate(Sum('cantidad_total'))
            t_cantidad_i = cantidad_ingreso['cantidad_ingreso__sum']
            t_cantidad_s = cantidad_salida['cantidad_salida__sum']
            t_cantidad_t= cantidad_total['cantidad_total__sum']
            valor_ingreso = listado_kardex.aggregate(Sum('valor_ingreso'))
            valor_salida = listado_kardex.aggregate(Sum('valor_salida'))
            valor_total = listado_kardex.aggregate(Sum('valor_total'))
            t_valor_i = valor_ingreso['valor_ingreso__sum']
            t_valor_s = valor_salida['valor_salida__sum']
            t_valor_t= valor_total['valor_total__sum']
        else:
            t_cantidad_i = 0
            t_cantidad_s = 0
            t_cantidad_t = 0
            t_valor_i = 0
            t_valor_s = 0
            t_valor_t = 0
        return (listado_kardex, t_cantidad_i, t_valor_i, t_cantidad_s, t_valor_s, t_cantidad_t, t_valor_t)

    def tabla_encabezado(self):
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
        listado_kardex, cantidad_ingreso, valor_ingreso, cantidad_salida, valor_salida, cantidad_total, valor_total = self.obtener_kardex(
            producto,
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
                #('ALIGN', (0, 0), (4, 0), 'CENTER'),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('TEXTFONT', (0, 1), (-1, 1), 'Times-Roman'),
                ('ALIGN', (5, 1), (7, -1), 'RIGHT'),
                #('VALIGN', (0, 0), (-1, -1), 'TOP'),
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

    def imprimir_formato_sunat_unidades_fisicas(self, producto, desde, hasta, almacen):
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
        elements.append(self.tabla_encabezado())
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

class ReporteKardexTodosPDF():

    def __init__(self, pagesize):
        self.buffer = BytesIO()
        if pagesize == 'A4':
            self.pagesize = landscape(A4)
        elif pagesize == 'Letter':
            self.pagesize = letter
        self.width, self.height = self.pagesize

    def obtener_kardex(self, producto, almacen, desde, hasta):
        listado_kardex = Kardex.objects.filter(almacen = almacen,
                                               movimiento__estado = Movimiento.STATUS.ACT,
                                               fecha_operacion__gte=desde,
                                               fecha_operacion__lte=hasta,
                                               producto = producto).order_by('producto__descripcion',
                                                                           'fecha_operacion',
                                                                           'cantidad_salida',
                                                                           'created')
        if len(listado_kardex)>0:
            cantidad_ingreso = listado_kardex.aggregate(Sum('cantidad_ingreso'))
            cantidad_salida = listado_kardex.aggregate(Sum('cantidad_salida'))
            cantidad_total = listado_kardex.aggregate(Sum('cantidad_total'))
            t_cantidad_i = cantidad_ingreso['cantidad_ingreso__sum']
            t_cantidad_s = cantidad_salida['cantidad_salida__sum']
            t_cantidad_t= cantidad_total['cantidad_total__sum']
            valor_ingreso = listado_kardex.aggregate(Sum('valor_ingreso'))
            valor_salida = listado_kardex.aggregate(Sum('valor_salida'))
            valor_total = listado_kardex.aggregate(Sum('valor_total'))
            t_valor_i = valor_ingreso['valor_ingreso__sum']
            t_valor_s = valor_salida['valor_salida__sum']
            t_valor_t= valor_total['valor_total__sum']
        else:
            t_cantidad_i = 0
            t_cantidad_s = 0
            t_cantidad_t = 0
            t_valor_i = 0
            t_valor_s = 0
            t_valor_t = 0
        return (listado_kardex, t_cantidad_i, t_valor_i, t_cantidad_s, t_valor_s, t_cantidad_t, t_valor_t)

    def tabla_encabezado(self):
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
        listado_kardex, cantidad_ingreso, valor_ingreso, cantidad_salida, valor_salida, cantidad_total, valor_total = self.obtener_kardex(
            producto,
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
                #('ALIGN', (0, 0), (4, 0), 'CENTER'),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('TEXTFONT', (0, 1), (-1, 1), 'Times-Roman'),
                ('ALIGN', (5, 1), (7, -1), 'RIGHT'),
                #('VALIGN', (0, 0), (-1, -1), 'TOP'),
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

    def imprimir_formato_sunat_unidades_fisicas(self, desde, hasta, almacen):
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
            elements.append(self.tabla_encabezado())
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