# -*- coding: utf-8 -*- 
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Image, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER,TA_LEFT, TA_JUSTIFY
from contabilidad.models import Empresa
from django.conf import settings
import os
from reportlab.platypus import Table
from reportlab.lib import colors
from reportlab.lib.pagesizes import cm
from reportlab.platypus.flowables import Spacer, ListFlowable
from io import BytesIO
from compras.models import DetalleOrdenCompra
from django.utils.encoding import smart_str
from reportlab.graphics.shapes import Line, Drawing

empresa = Empresa.load()
 
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
                            alignment = TA_CENTER,
                            fontSize = 14,
                            fontName="Times-Roman")
        try:
            archivo_imagen = os.path.join(settings.MEDIA_ROOT,str(empresa.logo))
            imagen = Image(archivo_imagen, width=90, height=50,hAlign='LEFT')
        except:
            imagen = Paragraph(u"LOGO", sp)
        
        nro = Paragraph(u"ORDEN DE COMPRA", sp)
        ruc = Paragraph("R.U.C."+empresa.ruc, sp)
        encabezado = [[imagen,nro,ruc],['',u"N°"+orden_compra.codigo,empresa.distrito + " " + orden_compra.fecha.strftime('%d de %b de %Y')]]
        tabla_encabezado = Table(encabezado,colWidths=[4 * cm, 9 * cm, 6 * cm])
        tabla_encabezado.setStyle(TableStyle(
            [
                ('ALIGN',(0,0),(2,1),'CENTER'),
                ('VALIGN',(0,0),(2,0),'CENTER'),
                ('VALIGN',(1,1),(2,1),'TOP'),
                ('SPAN',(0,0),(0,1)),  
                                             
            ]
        ))
        return tabla_encabezado
    
    def tabla_datos(self, styles):
        orden = self.orden_compra
        izquierda = ParagraphStyle('parrafos',
                            alignment = TA_LEFT,
                            fontSize = 10,
                            fontName="Times-Roman")
        cotizacion = orden.cotizacion
        if cotizacion is None:
            proveedor = orden.proveedor
        else:
            proveedor = orden.cotizacion.proveedor
        razon_social_proveedor = Paragraph(u"SEÑOR(ES): "+proveedor.razon_social, izquierda)
        ruc_proveedor = Paragraph(u"R.U.C.: "+proveedor.ruc, izquierda)
        direccion = Paragraph(u"DIRECCIÓN: "+proveedor.direccion, izquierda)
        try:
            telefono = Paragraph(u"TELÉFONO: "+proveedor.telefono, izquierda)
        except:
            telefono = Paragraph(u"TELÉFONO: -", izquierda)
        try:
            referencia = Paragraph(u"REFERENCIA: "+orden.cotizacion.requerimiento.codigo+" - "+orden.cotizacion.requerimiento.oficina.nombre, izquierda)
        except:
            referencia = Paragraph(u"REFERENCIA: ",izquierda)
        proceso = Paragraph(u"PROCESO: "+orden.proceso, izquierda)
        nota = Paragraph(u"Sírvase remitirnos según especificaciones que detallamos lo siguiente: ", izquierda)
        datos = [[razon_social_proveedor,ruc_proveedor],[direccion,telefono],[referencia,''],[proceso,''],[nota,'']]
        tabla_detalle = Table(datos,colWidths=[11* cm, 9 * cm])        
        tabla_detalle.setStyle(TableStyle(
            [
                ('SPAN',(0,2),(1,2)),                        
            ]
        ))
        return tabla_detalle
    
    def tabla_detalle(self):
        orden = self.orden_compra
        encabezados = ['Item', 'Cantidad', 'Unidad', u'Descripción','Precio','Total']
        detalles = DetalleOrdenCompra.objects.filter(orden=orden).order_by('pk')
        sp = ParagraphStyle('parrafos')
        sp.alignment = TA_JUSTIFY 
        sp.fontSize = 8
        sp.fontName="Times-Roman"        
        lista_detalles = []
        for detalle in detalles:
            try:
                tupla_producto = [Paragraph(str(detalle.nro_detalle),sp), 
                                  Paragraph(str(detalle.cantidad), sp),
                                  Paragraph(detalle.detalle_cotizacion.detalle_requerimiento.producto.unidad_medida.descripcion,sp),
                                  Paragraph(detalle.detalle_cotizacion.detalle_requerimiento.producto.descripcion, sp),
                                  Paragraph(str(detalle.precio),sp),
                                  Paragraph(str(detalle.valor),sp)]
            except:
                tupla_producto = [Paragraph(str(detalle.nro_detalle),sp), 
                                  Paragraph(str(detalle.cantidad), sp),
                                  Paragraph(detalle.producto.unidad_medida.descripcion,sp),
                                  Paragraph(detalle.producto.descripcion, sp),
                                  Paragraph(str(detalle.precio),sp),
                                  Paragraph(str(detalle.valor),sp)]
            lista_detalles.append(tupla_producto)
        adicionales = [('','','','','')] * (15-len(lista_detalles))
        tabla_detalle = Table([encabezados] + lista_detalles + adicionales,colWidths=[0.8 * cm, 2 * cm, 2.5 * cm,10.2* cm, 2 * cm, 2.5 * cm])
        style = TableStyle(
            [
                ('ALIGN',(0,0),(4,0),'CENTER'),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('FONTSIZE', (0, 0), (-1, -1), 7),  
                ('ALIGN',(4,1),(-1,-1),'LEFT'), 
                ('VALIGN',(0,0),(-1,-1),'TOP'),          
            ]
        )
        tabla_detalle.setStyle(style)
        return tabla_detalle
    
    def tabla_total_letras(self):
        orden = self.orden_compra
        total_letras = [("SON: "+orden.total_letras,'')]
        tabla_total_letras = Table(total_letras,colWidths=[17.5 * cm, 2.5 * cm])
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
                           alignment = TA_CENTER,
                           fontSize = 8,
                           fontName="Times-Roman")
        sub_total = Paragraph(u"SUBTOTAL: ",p)
        igv = Paragraph(u"IGV: ",p)
        total = Paragraph(u"TOTAL: ",p)
        datos_otros = [[ Paragraph(u"LUGAR DE ENTREGA",p),  Paragraph(u"PLAZO DE ENTREGA",p),  Paragraph(u"FORMA DE PAGO",p),sub_total,orden.subtotal],
                       [Paragraph(empresa.direccion(),p),Paragraph(u"INMEDIATA",p),Paragraph(orden.forma_pago.descripcion,p),igv,str(orden.igv)],
                       ['','','',total,str(orden.total)],
                       ]
        tabla_otros = Table(datos_otros,colWidths=[5.5 * cm, 5 * cm, 5 * cm, 2 * cm, 2.5 * cm])
        tabla_otros.setStyle(TableStyle(
            [
                ('GRID', (0, 0), (2, 2), 1, colors.black),
                ('SPAN',(0,1),(0,2)),
                ('SPAN',(1,1),(1,2)),
                ('SPAN',(2,1),(2,2)),
                ('GRID', (4, 0), (4, 2), 1, colors.black),
                ('VALIGN',(0,1),(2,1),'MIDDLE'),
            ]
        ))
        return tabla_otros
    
    def tabla_observaciones(self):
        orden = self.orden_compra
        p = ParagraphStyle('parrafos',
                           alignment = TA_JUSTIFY,
                           fontSize = 8,
                           fontName="Times-Roman")
        obs=Paragraph("OBSERVACIONES: "+orden.observaciones,p)
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
    
    def tabla_afectacion_presupuestal(self):
        orden = self.orden_compra
        p = ParagraphStyle('parrafos', 
                           alignment = TA_JUSTIFY,
                           fontSize = 8,
                           fontName="Times-Roman")
        hoja_afectacion = Paragraph(u"HOJA DE AFECTACIÓN PRESUPUESTAL: ",p)
        importante = Paragraph(u"IMPORTANTE: ", p)
        recibido = Paragraph(u"RECIBIDO POR: ", p)
        firma = Paragraph(u"FIRMA: ", p)
        nombre = Paragraph(u"NOMBRE: ", p)
        dni = Paragraph(u"DNI: ", p)
        lista = ListFlowable([
                          Paragraph("""Consignar el número de la presente Orden de Compra en su Guía de Remisión y Factura. 
                          Facturar a nombre de """ + smart_str(empresa.razon_social),p),
                          Paragraph("El " + smart_str(empresa.razon_social) + """, se reserva el derecho de devolver 
                          la mercaderia, sino se ajusta a las especificaciones requeridas, asimismo de anular la presente 
                          Orden de Compra.""",p),
                          Paragraph("""El pago de toda factura se hará de acuerdo a las condiciones establecidas.""",p)
                          ],bulletType='1'
                         )
        datos_otros = [[hoja_afectacion,''],
                       [importante,recibido],
                       [lista,''],
                       ['',firma],
                       ['',nombre],
                       ['',dni],
                       ]
        tabla_afectacion_presupuestal = Table(datos_otros,colWidths=[10 * cm, 10 * cm])
        tabla_afectacion_presupuestal.setStyle(TableStyle(
            [
                ('ALIGN',(0,1),(1,1),'CENTER'), 
                ('SPAN',(0,2),(0,5)),               
            ]
        ))
        return tabla_afectacion_presupuestal 
        
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
        elements.append(self.tabla_total_letras())        
        elements.append(Spacer(1, 0.25 * cm))
        elements.append(self.tabla_otros())
        elements.append(Spacer(1, 0.25 * cm))
        elements.append(self.tabla_observaciones())
        elements.append(Spacer(1, 0.25 * cm))
        elements.append(self.tabla_afectacion_presupuestal())
        linea_firma = Line(280, y-250, 470, y-250)
        d = Drawing(100, 1)
        d.add(linea_firma)
        elements.append(d)
        doc.build(elements)
        pdf = buffer.getvalue()
        buffer.close()
        return pdf