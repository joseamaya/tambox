# -*- coding: utf-8 -*- 
from django.shortcuts import render, get_object_or_404
from django.views.generic.base import View, TemplateView
from django.views.generic.list import ListView
from django.views.generic.edit import FormView, UpdateView, CreateView
from django.core.urlresolvers import reverse_lazy, reverse
from django.http.response import HttpResponseRedirect
import json
from django.http import HttpResponse
import simplejson
from django.views.generic.detail import DetailView
from reportlab.pdfgen import canvas
from io import BytesIO
from reportlab.platypus import Paragraph, TableStyle
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib import colors
from reportlab.platypus import Table
from django.conf import settings
from reportlab.lib.pagesizes import cm
from reportlab.lib.enums import TA_JUSTIFY
from administracion.models import Oficina, Puesto
import locale
from django.contrib.auth.decorators import permission_required
from django.utils.decorators import method_decorator
import os
from django.db import transaction, IntegrityError
from django.db.models import Q
from django.contrib import messages
from contabilidad.models import Configuracion, Empresa
from requerimientos.models import AprobacionRequerimiento, Requerimiento,\
    DetalleRequerimiento
from requerimientos.forms import AprobacionRequerimientoForm,\
    FormularioDetalleRequerimiento, RequerimientoForm,\
    DetalleRequerimientoFormSet
from compras.forms import DetalleCotizacionFormSet
from compras.models import Cotizacion
from productos.models import Producto
from requerimientos.mail import correo_creacion_requerimiento

locale.setlocale(locale.LC_ALL,"")
empresa = Empresa.load()
# Create your views here.
class Tablero(View):
    
    def get(self, request, *args, **kwargs):
        lista_notificaciones = []
        context = {'notificaciones':lista_notificaciones}
        return render(request, 'requerimientos/tablero_requerimientos.html', context)

class AprobarRequerimiento(UpdateView):
    model = AprobacionRequerimiento
    template_name = 'requerimientos/aprobar_requerimiento.html'
    form_class = AprobacionRequerimientoForm
    success_url = reverse_lazy('requerimientos:listado_aprobacion_requerimientos')
    
    @method_decorator(permission_required('requerimientos.change_aprobacionrequerimiento',reverse_lazy('seguridad:permiso_denegado')))
    def dispatch(self, *args, **kwargs):
        aprobacion_requerimiento = get_object_or_404(self.model, pk=kwargs['pk'])
        configuracion = Configuracion.objects.first()
        oficina_administracion = configuracion.administracion
        presupuesto = configuracion.presupuesto
        logistica = configuracion.logistica
        puesto_usuario = self.request.user.trabajador.puesto_set.all().filter(estado=True)[0]
        oficina_usuario = puesto_usuario.oficina
        requerimiento_oficina = aprobacion_requerimiento.requerimiento.oficina        
        if puesto_usuario.es_jefatura and oficina_usuario==requerimiento_oficina and aprobacion_requerimiento.estado==AprobacionRequerimiento.STATUS.PEND:
            if aprobacion_requerimiento.estado==AprobacionRequerimiento.STATUS.PEND or aprobacion_requerimiento.estado==AprobacionRequerimiento.STATUS.APROB_JEF or aprobacion_requerimiento.estado==AprobacionRequerimiento.STATUS.DESAP_JEF:
                return super(AprobarRequerimiento, self).dispatch(*args, **kwargs)
        elif oficina_usuario==requerimiento_oficina.gerencia:
            if aprobacion_requerimiento.estado==AprobacionRequerimiento.STATUS.APROB_JEF or aprobacion_requerimiento.estado==AprobacionRequerimiento.STATUS.APROB_GER_INM or aprobacion_requerimiento.estado==AprobacionRequerimiento.STATUS.DESAP_GER_INM:
                return super(AprobarRequerimiento, self).dispatch(*args, **kwargs)
        elif oficina_usuario == oficina_administracion:
            if aprobacion_requerimiento.estado==AprobacionRequerimiento.STATUS.APROB_GER_INM or aprobacion_requerimiento.estado==AprobacionRequerimiento.STATUS.APROB_GER_ADM or aprobacion_requerimiento.estado==AprobacionRequerimiento.STATUS.DESAP_GER_ADM:
                return super(AprobarRequerimiento, self).dispatch(*args, **kwargs)
        elif oficina_usuario == logistica:
            if aprobacion_requerimiento.estado==AprobacionRequerimiento.STATUS.APROB_GER_ADM or aprobacion_requerimiento.estado==AprobacionRequerimiento.STATUS.APROB_LOG or aprobacion_requerimiento.estado==AprobacionRequerimiento.STATUS.DESAP_LOG:
                return super(AprobarRequerimiento, self).dispatch(*args, **kwargs)
        elif oficina_usuario == presupuesto:
            if aprobacion_requerimiento.estado==AprobacionRequerimiento.STATUS.APROB_LOG or aprobacion_requerimiento.estado==AprobacionRequerimiento.STATUS.APROB_PRES or aprobacion_requerimiento.estado==AprobacionRequerimiento.STATUS.DESAP_PRES:
                return super(AprobarRequerimiento, self).dispatch(*args, **kwargs)
        return HttpResponseRedirect(reverse('seguridad:permiso_denegado'))
    
    def get_form_kwargs(self):
        kwargs = super(AprobarRequerimiento, self).get_form_kwargs()
        kwargs['request'] = self.request
        return kwargs
    
class CrearDetalleRequerimiento(FormView):    
        
    def get(self, request, *args, **kwargs):
        if request.is_ajax():
            lista_detalles = []            
            det = {}
            det['codigo'] = ''               
            det['producto'] = ''                    
            det['unidad'] = ''
            det['cantidad'] = '0'
            det['uso'] = ''
            lista_detalles.append(det)
            formset = DetalleRequerimientoFormSet(initial=lista_detalles)
            lista_json = []
            for form in formset:
                detalle_json = {}    
                detalle_json['codigo'] = str(form['codigo'])
                detalle_json['producto'] = str(form['producto'])
                detalle_json['unidad'] = str(form['unidad'])
                detalle_json['cantidad'] = str(form['cantidad'])
                detalle_json['uso'] = str(form['uso'])
                lista_json.append(detalle_json)                                
            data = json.dumps(lista_json)
            return HttpResponse(data, 'application/json')

class CrearRequerimiento(CreateView):
    template_name = 'requerimientos/requerimiento.html'
    form_class = RequerimientoForm
    model = Requerimiento
        
    def get_form_kwargs(self):
        kwargs = super(CrearRequerimiento, self).get_form_kwargs()
        kwargs['request'] = self.request
        return kwargs
    
    def get(self, request, *args, **kwargs):
        self.object = None
        oficinas = Oficina.objects.all()        
        if not oficinas:
            return HttpResponseRedirect(reverse('administracion:crear_oficina'))
        try:
            trabajador = request.user.trabajador
            try:
                puesto = Puesto.objects.get(trabajador=trabajador)
                if trabajador.firma:
                    puesto_jefe = Puesto.objects.get(oficina=puesto.oficina,es_jefatura=True,estado=True)
                    configuracion = Configuracion.objects.first()
                    if configuracion is not None:
                        form_class = self.get_form_class()
                        form = self.get_form(form_class)
                        detalle_requerimiento_formset=DetalleRequerimientoFormSet()
                        return self.render_to_response(self.get_context_data(form=form,
                                                                             detalle_requerimiento_formset=detalle_requerimiento_formset))
                    else:
                        return HttpResponseRedirect(reverse('contabilidad:configuracion'))
                else:
                    return HttpResponseRedirect(reverse('administracion:modificar_trabajador',args=[trabajador.pk]))
            except Puesto.DoesNotExist:
                return HttpResponseRedirect(reverse('administracion:crear_puesto'))
        except:
            return HttpResponseRedirect(reverse('administracion:crear_trabajador'))
    
    def post(self, request, *args, **kwargs):
        self.object = None
        form_class = self.get_form_class()
        form = self.get_form(form_class)
        detalle_requerimiento_formset = DetalleRequerimientoFormSet(request.POST)
        if form.is_valid() and detalle_requerimiento_formset.is_valid():
            return self.form_valid(form, detalle_requerimiento_formset)
        else:
            return self.form_invalid(form, detalle_requerimiento_formset)
    
    def form_valid(self, form, detalle_requerimiento_formset):
        try:
            with transaction.atomic():
                self.object = form.save()
                detalles = []
                cont = 1
                for detalle_requerimiento_form in detalle_requerimiento_formset:                
                    codigo = detalle_requerimiento_form.cleaned_data.get('codigo')
                    cantidad = detalle_requerimiento_form.cleaned_data.get('cantidad')
                    uso = detalle_requerimiento_form.cleaned_data.get('uso')
                    if codigo and cantidad:                                
                        producto = Producto.objects.get(codigo=codigo)                
                        detalles.append(DetalleRequerimiento(requerimiento=self.object, nro_detalle = cont, producto=producto, cantidad=cantidad, uso=uso))
                        cont = cont + 1
                    elif cantidad:
                        producto = detalle_requerimiento_form.cleaned_data.get('producto')
                        detalles.append(DetalleRequerimiento(requerimiento=self.object, nro_detalle = cont, otro=producto, cantidad=cantidad, uso=uso))
                        cont = cont + 1
                DetalleRequerimiento.objects.bulk_create(detalles)
                puesto_jefe = Puesto.objects.get(oficina=self.object.oficina, es_jefatura=True, estado=True)
                jefe = puesto_jefe.trabajador
                destinatario = [jefe.usuario.email]
                correo_creacion_requerimiento(destinatario, self.object)
                return HttpResponseRedirect(reverse('requerimientos:detalle_requerimiento', args=[self.object.codigo]))
        except IntegrityError:
                messages.error(self.request, 'Error guardando el requerimiento.')
        
    def form_invalid(self, form, detalle_requerimiento_formset):
        return self.render_to_response(self.get_context_data(form=form,
                                                             detalle_requerimiento_formset=detalle_requerimiento_formset))

class DetalleOperacionRequerimiento(DetailView):
    model = Requerimiento
    template_name = 'requerimientos/detalle_requerimiento.html'
    
class EliminarRequerimiento(TemplateView):
    
    def get(self, request, *args, **kwargs):
        if request.is_ajax():
            codigo = request.GET['codigo']
            requerimiento = Requerimiento.objects.get(codigo=codigo)
            requerimiento_json = {}
            requerimiento_json['codigo'] = codigo
            if len(requerimiento.ordencompra_set.all())>0:
                requerimiento_json['ordenes'] = 'SI'
            else:
                requerimiento_json['ordenes'] = 'NO'
                with transaction.atomic():
                    Requerimiento.objects.filter(codigo=codigo).update(estado = False)
                    DetalleRequerimiento.objects.filter(requerimiento=requerimiento).delete()
            data = simplejson.dumps(requerimiento_json)
            return HttpResponse(data, 'application/json')
        
class ListadoAprobacionRequerimientos(ListView):
    model = AprobacionRequerimiento
    template_name = 'requerimientos/listado_aprobacion_requerimientos.html'
    context_object_name = 'aprobacion_requerimientos'    
    
    @method_decorator(permission_required('requerimientos.ver_tabla_requerimientos',reverse_lazy('seguridad:permiso_denegado')))
    def dispatch(self, *args, **kwargs):
        return super(ListadoAprobacionRequerimientos, self).dispatch(*args, **kwargs)
    
    def get(self, request, *args, **kwargs):
        try:
            trabajador = self.request.user.trabajador
            puestos = trabajador.puesto_set.all().filter(estado=True)
            if trabajador.firma == '':
                return HttpResponseRedirect(reverse('seguridad:permiso_denegado'))
            if puestos[0].es_jefatura:
                return super(ListadoAprobacionRequerimientos, self).get(request, *args, **kwargs)
            else:
                return HttpResponseRedirect(reverse('seguridad:permiso_denegado'))
        except:
            return HttpResponseRedirect(reverse('seguridad:permiso_denegado'))        
    
    def get_queryset(self):
        configuracion = Configuracion.objects.first()
        oficina_administracion = configuracion.administracion
        presupuesto = configuracion.presupuesto
        logistica = configuracion.logistica
        puestos = self.request.user.trabajador.puesto_set.all().filter(estado=True)
        puesto_usuario = puestos[0]
        oficina_usuario =  puesto_usuario.oficina
        queryset = AprobacionRequerimiento.objects.filter(requerimiento__in=Requerimiento.objects.filter(oficina = oficina_usuario),
                                                          estado=AprobacionRequerimiento.STATUS.PEND)
        if len(queryset)==0:
            queryset = AprobacionRequerimiento.objects.filter(requerimiento__in=Requerimiento.objects.filter(oficina__gerencia = oficina_usuario),
                                                              estado=AprobacionRequerimiento.STATUS.APROB_JEF)
        if len(queryset)==0:
            if oficina_usuario == oficina_administracion:
                queryset = AprobacionRequerimiento.objects.filter(estado=AprobacionRequerimiento.STATUS.APROB_GER_INM)                
            elif oficina_usuario == logistica:
                queryset = AprobacionRequerimiento.objects.filter(estado=AprobacionRequerimiento.STATUS.APROB_GER_ADM)
            elif oficina_usuario == presupuesto:
                queryset = AprobacionRequerimiento.objects.filter(estado=AprobacionRequerimiento.STATUS.APROB_LOG)                
        return queryset
    
class ListadoCotizacionesPorRequerimiento(ListView):
    model = Cotizacion
    template_name = 'compras/cotizaciones.html'
    context_object_name = 'cotizaciones'    
    
    @method_decorator(permission_required('compras.ver_tabla_cotizaciones',reverse_lazy('seguridad:permiso_denegado')))
    def dispatch(self, *args, **kwargs):
        return super(ListadoCotizacionesPorRequerimiento, self).dispatch(*args, **kwargs)
    
    def get_queryset(self):
        requerimiento = Requerimiento.objects.get(pk=self.kwargs['requerimiento'])
        queryset = requerimiento.cotizacion_set.all()
        return queryset
    
class ListadoRequerimientos(ListView):
    model = Requerimiento
    template_name = 'requerimientos/listado_requerimientos.html'
    context_object_name = 'requerimientos'
    queryset = Requerimiento.objects.exclude(estado=Requerimiento.STATUS.CANC).order_by('codigo')
    
    @method_decorator(permission_required('requerimientos.ver_tabla_requerimientos',reverse_lazy('seguridad:permiso_denegado')))
    def dispatch(self, *args, **kwargs):
        return super(ListadoRequerimientos, self).dispatch(*args, **kwargs)
    
class ModificarRequerimiento(UpdateView):    
    template_name = 'requerimientos/requerimiento.html'
    model = Requerimiento
    form_class = RequerimientoForm
    
    def get_form_kwargs(self):
        kwargs = super(ModificarRequerimiento, self).get_form_kwargs()
        kwargs['request'] = self.request
        return kwargs
    
    '''def get_initial(self):
        initial = super(ModificarRequerimiento, self).get_initial()
        initial['fecha'] = self.object.fecha.strftime('%d/%m/%Y')
        return initial'''
    
    def get_context_data(self, **kwargs):
        context = super(ModificarRequerimiento, self).get_context_data(**kwargs)
        try:
            context['archivo_informe'] = os.path.join('/tambox','media',self.object.informe.url)
        except:
            pass
        return context
    
    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        form_class = self.get_form_class()
        form = self.get_form(form_class)
        detalles = DetalleRequerimiento.objects.filter(requerimiento=self.object).order_by('nro_detalle')
        detalles_data = []
        for detalle in detalles:
            try:
                d = {'codigo': detalle.producto.codigo, 
                     'producto': detalle.producto.descripcion, 
                     'cantidad': detalle.cantidad, 
                     'unidad': detalle.producto.unidad_medida.codigo,
                     'uso': detalle.uso }
            except:
                d = {'codigo': '', 
                     'producto': detalle.otro, 
                     'cantidad': detalle.cantidad,
                     'unidad': '',
                     'uso': detalle.uso }
            detalles_data.append(d)
        detalle_requerimiento_formset=DetalleRequerimientoFormSet(initial=detalles_data)
        return self.render_to_response(self.get_context_data(form=form,
                                                             detalle_requerimiento_formset=detalle_requerimiento_formset))
    
    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        form_class = self.get_form_class()
        form = self.get_form(form_class)
        detalle_requerimiento_formset = DetalleRequerimientoFormSet(request.POST)
        if form.is_valid() and detalle_requerimiento_formset.is_valid():
            return self.form_valid(form, detalle_requerimiento_formset)
        else:
            return self.form_invalid(form, detalle_requerimiento_formset)
    
    def form_valid(self, form, detalle_requerimiento_formset):
        try:
            with transaction.atomic():
                DetalleRequerimiento.objects.filter(requerimiento=self.object).delete()
                form.save()        
                detalles = []
                cont = 1
                for detalle_requerimiento_form in detalle_requerimiento_formset:                
                    codigo = detalle_requerimiento_form.cleaned_data.get('codigo')
                    cantidad = detalle_requerimiento_form.cleaned_data.get('cantidad')
                    uso = detalle_requerimiento_form.cleaned_data.get('uso')
                    if codigo and cantidad:                                
                        producto = Producto.objects.get(codigo=codigo)                
                        detalles.append(DetalleRequerimiento(requerimiento=self.object, nro_detalle = cont, producto=producto, cantidad=cantidad, uso=uso))
                        cont = cont + 1
                    elif cantidad:
                        producto = detalle_requerimiento_form.cleaned_data.get('producto')
                        detalles.append(DetalleRequerimiento(requerimiento=self.object, nro_detalle = cont, otro=producto, cantidad=cantidad, uso=uso))
                        cont = cont + 1
                DetalleRequerimiento.objects.bulk_create(detalles)
                return HttpResponseRedirect(reverse('requerimientos:detalle_requerimiento', args=[self.object.codigo]))
        except IntegrityError:
                messages.error(self.request, 'Error guardando el requerimiento.')
        
    def form_invalid(self, form, detalle_requerimiento_formset):
        return self.render_to_response(self.get_context_data(form=form,
                                                             detalle_requerimiento_formset=detalle_requerimiento_formset))

class ObtenerDetalleRequerimiento(TemplateView):
    
    def get(self, request, *args, **kwargs):
        if request.is_ajax():
            requerimiento = request.GET['requerimiento']
            tipo_busqueda =  request.GET['tipo_busqueda']
            if tipo_busqueda == 'TODOS':
                detalles = DetalleRequerimiento.objects.filter(Q(estado=DetalleRequerimiento.STATUS.PEND) | Q(estado=DetalleRequerimiento.STATUS.COTIZ),requerimiento__codigo=requerimiento).order_by('nro_detalle')
            elif tipo_busqueda == 'PRODUCTOS':
                detalles = DetalleRequerimiento.objects.filter(Q(estado=DetalleRequerimiento.STATUS.PEND) | Q(estado=DetalleRequerimiento.STATUS.COTIZ),requerimiento__codigo=requerimiento,producto__isnull=False).order_by('nro_detalle')
            lista_detalles = []
            for detalle in detalles:
                det = {}       
                det['requerimiento'] = detalle.id
                try:
                    det['codigo'] = detalle.producto.codigo                
                    det['nombre'] = detalle.producto.descripcion                
                    det['unidad'] = detalle.producto.unidad_medida.codigo
                    #det['uso'] = detalle.uso
                    det['cantidad'] = str(detalle.cantidad-detalle.cantidad_atendida)
                    #det['precio'] = str(detalle.producto.precio)
                    #det['valor'] = str(detalle.producto.precio*(detalle.cantidad-detalle.cantidad_atendida))
                    lista_detalles.append(det)
                except:
                    pass                
            formset = DetalleCotizacionFormSet(initial=lista_detalles)
            lista_json = []
            for form in formset:
                detalle_json = {}    
                detalle_json['requerimiento'] = str(form['requerimiento'])
                detalle_json['codigo'] = str(form['codigo'])
                detalle_json['nombre'] = str(form['nombre'])
                detalle_json['unidad'] = str(form['unidad'])
                detalle_json['cantidad'] = str(form['cantidad'])
                lista_json.append(detalle_json)                
            data = json.dumps(lista_json)
            return HttpResponse(data, 'application/json')

class TransferenciaRequerimiento(TemplateView):
    template_name = 'requerimientos/transferencia_requerimiento.html'   
    
    def get_context_data(self, **kwargs):
        context = super(TransferenciaRequerimiento, self).get_context_data(**kwargs)
        requerimientos = Requerimiento.objects.filter(aprobacionrequerimiento__estado=AprobacionRequerimiento.STATUS.APROB_PRES).filter(Q(estado = Requerimiento.STATUS.PEND) | Q(estado = Requerimiento.STATUS.COTIZ_PARC) | Q(estado = Requerimiento.STATUS.COTIZ))
        context['requerimientos'] = requerimientos
        return context
    
class ReportePDFRequerimiento(View):
    
    def cabecera(self,pdf,requerimiento):
        try:
            archivo_imagen = os.path.join(settings.MEDIA_ROOT,str(empresa.logo))
            pdf.drawImage(archivo_imagen, 40, 750, 100, 90, mask='auto',preserveAspectRatio=True)
        except:
            pdf.drawString(40,800,str(archivo_imagen))        
        pdf.setFont("Times-Roman", 14)
        encabezado = [[u"REQUERIMIENTO DE BIENES Y SERVICIOS"]]
        tabla_encabezado = Table(encabezado,colWidths=[8 * cm])
        tabla_encabezado.setStyle(TableStyle(
            [
                ('ALIGN',(0,0),(0,0),'CENTER'),
                ('GRID', (0, 0), (1, 0), 1, colors.black),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
            ]
        ))
        tabla_encabezado.wrapOn(pdf, 800, 600)
        tabla_encabezado.drawOn(pdf, 200,800)
        pdf.drawString(270, 780, u"N°"+requerimiento.codigo)
        pdf.setFont("Times-Roman", 10)
        pdf.drawString(20, 750, u"SOLICITADO POR: "+requerimiento.solicitante.nombre_completo())
        pdf.drawString(20, 730, u"PEDIDO PARA: "+requerimiento.motivo)
        pdf.drawString(20, 710, u"FECHA DE REQUERIMIENTO: "+requerimiento.created.strftime('%d/%m/%Y'))
        pdf.drawString(320, 710, u"MES EN QUE SE NECESITA: "+requerimiento.get_mes_display())
        pdf.drawString(20, 690, u"REQUERIMIENTO PARA STOCK DE ALMACEN: ")
        if requerimiento.entrega_directa_solicitante:
            pdf.drawString(320, 690, u"ENTREGA DIRECTAMENTE AL SOLICITANTE: SI")
        else:
            pdf.drawString(320, 690, u"ENTREGA DIRECTAMENTE AL SOLICITANTE: NO")
        
    def detalle(self,pdf,y,requerimiento):
        encabezados = ('Nro', 'Cantidad', 'Unidad', u'Descripción','Uso')
        detalles = DetalleRequerimiento.objects.filter(requerimiento=requerimiento)
        lista_detalles = []
        for detalle in detalles:
            try:
                tupla_producto = (detalle.nro_detalle, detalle.cantidad, detalle.producto.unidad_medida.descripcion, detalle.producto.descripcion, detalle.uso)
                lista_detalles.append(tupla_producto)
            except:
                tupla_otro = (detalle.nro_detalle, detalle.cantidad, detalle.unidad, detalle.otro, detalle.uso)
                lista_detalles.append(tupla_otro)
        adicionales = [('','','','','')]*(15-len(detalles))
        tabla_detalle = Table([encabezados] + lista_detalles + adicionales,colWidths=[0.7 * cm, 1.8 * cm, 1.5 * cm,7.5* cm, 8 * cm])
        tabla_detalle.setStyle(TableStyle(
            [
                ('ALIGN',(0,0),(4,0),'CENTER'),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('FONTSIZE', (0, 0), (-1, -1), 7),  
                ('ALIGN',(4,1),(-1,-1),'LEFT'),           
            ]
        ))
        tabla_detalle.wrapOn(pdf, 800, 600)
        tabla_detalle.drawOn(pdf, 20,y+80)
        
    def cuadro_observaciones(self,pdf,y,requerimiento):
        p = ParagraphStyle('parrafos')
        p.alignment = TA_JUSTIFY 
        p.fontSize = 8
        p.fontName="Times-Roman"
        obs=Paragraph("OBSERVACIONES: "+requerimiento.observaciones,p)
        observaciones = [[obs]]
        tabla_observaciones = Table(observaciones,colWidths=[19.5 * cm], rowHeights=1.8 * cm)
        tabla_observaciones.setStyle(TableStyle(
            [
                ('GRID', (0, 0), (0, 2), 1, colors.black),
                ('FONTSIZE', (0, 0), (-1, -1), 8),
                ('ALIGN',(0,0),(-1,-1),'LEFT'),
                ('VALIGN',(0,0),(-1,-1),'TOP'),
            ]
        ))
        tabla_observaciones.wrapOn(pdf, 800, 600)
        tabla_observaciones.drawOn(pdf, 20,y+20)
        
    def firmas(self,pdf,y,requerimiento):
        p = ParagraphStyle('parrafos')
        p.alignment = TA_JUSTIFY 
        p.fontSize = 8
        p.fontName="Times-Roman"
        obs=Paragraph("RECEPCIÓN: ",p)
        encabezados = [(u'Recepción', '', '', u'','','')]
        cuerpo = [('','','','','','')]        
        oficina = requerimiento.oficina
        jefatura = Puesto.objects.get(oficina=oficina,es_jefatura=True,estado=True)
        gerencia = Puesto.objects.get(oficina=oficina.gerencia,estado=True)
        configuracion = Configuracion.objects.first()
        oficina_administracion = configuracion.administracion
        presupuesto = configuracion.presupuesto
        logistica = configuracion.logistica
        jefatura_administracion = Puesto.objects.get(oficina = oficina_administracion,es_jefatura=True,estado=True)
        jefatura_presupuesto = Puesto.objects.get(oficina=presupuesto,es_jefatura=True,estado=True)
        jefatura_logistica = Puesto.objects.get(oficina=logistica,es_jefatura=True,estado=True)
        jefe = jefatura.trabajador
        gerente = gerencia.trabajador
        gerente_administracion = jefatura_administracion.trabajador
        jefe_logistica = jefatura_logistica.trabajador
        jefe_presupuesto = jefatura_presupuesto.trabajador 
        firma_solicitante = os.path.join(settings.MEDIA_ROOT,str(requerimiento.solicitante.firma))
        firma_jefe_departamento = os.path.join(settings.MEDIA_ROOT,str(jefe.firma))
        firma_gerente = os.path.join(settings.MEDIA_ROOT,str(gerente.firma))
        firma_gerente_administracion = os.path.join(settings.MEDIA_ROOT,str(gerente_administracion.firma))
        firma_jefe_oficina_logistica = os.path.join(settings.MEDIA_ROOT,str(jefe_logistica.firma))
        firma_jefe_oficina_presupuesto = os.path.join(settings.MEDIA_ROOT,str(jefe_presupuesto.firma))
        if requerimiento.aprobacionrequerimiento.estado==AprobacionRequerimiento.STATUS.PEND:
            pdf.drawImage(firma_solicitante, 100, y-70, 90, 90,preserveAspectRatio=True)
        elif requerimiento.aprobacionrequerimiento.estado==AprobacionRequerimiento.STATUS.APROB_JEF:
            pdf.drawImage(firma_solicitante, 100, y-70, 90, 90,preserveAspectRatio=True)
            pdf.drawImage(firma_jefe_departamento, 190, y-70, 90, 90,preserveAspectRatio=True)
        elif requerimiento.aprobacionrequerimiento.estado==AprobacionRequerimiento.STATUS.APROB_GER_INM:
            pdf.drawImage(firma_solicitante, 100, y-70, 90, 90,preserveAspectRatio=True)
            pdf.drawImage(firma_jefe_departamento, 190, y-70, 90, 90,preserveAspectRatio=True)
            pdf.drawImage(firma_gerente, 290, y-70, 90, 90,preserveAspectRatio=True)
        elif requerimiento.aprobacionrequerimiento.estado==AprobacionRequerimiento.STATUS.APROB_GER_ADM:
            pdf.drawImage(firma_solicitante, 100, y-70, 90, 90,preserveAspectRatio=True)
            pdf.drawImage(firma_jefe_departamento, 190, y-70, 90, 90,preserveAspectRatio=True)
            pdf.drawImage(firma_gerente, 290, y-70, 90, 90,preserveAspectRatio=True)
            pdf.drawImage(firma_gerente_administracion, 380, y-70, 90, 90,preserveAspectRatio=True)
        elif requerimiento.aprobacionrequerimiento.estado==AprobacionRequerimiento.STATUS.APROB_LOG:
            pdf.drawImage(firma_solicitante, 100, y-70, 90, 90,preserveAspectRatio=True)
            pdf.drawImage(firma_jefe_departamento, 190, y-70, 90, 90,preserveAspectRatio=True)
            pdf.drawImage(firma_gerente, 290, y-70, 90, 90,preserveAspectRatio=True)
            pdf.drawImage(firma_gerente_administracion, 380, y-70, 90, 90,preserveAspectRatio=True)
            pdf.drawImage(firma_jefe_oficina_logistica, 15, y-70, 90, 90,preserveAspectRatio=True)
        elif requerimiento.aprobacionrequerimiento.estado==AprobacionRequerimiento.STATUS.APROB_PRES:
            pdf.drawImage(firma_solicitante, 100, y-70, 90, 90,preserveAspectRatio=True)
            pdf.drawImage(firma_jefe_departamento, 190, y-70, 90, 90,preserveAspectRatio=True)
            pdf.drawImage(firma_gerente, 290, y-70, 90, 90,preserveAspectRatio=True)
            pdf.drawImage(firma_gerente_administracion, 380, y-70, 90, 90,preserveAspectRatio=True)
            pdf.drawImage(firma_jefe_oficina_logistica, 15, y-70, 90, 90,preserveAspectRatio=True)
            pdf.drawImage(firma_jefe_oficina_presupuesto, 480, y-70, 90, 90,preserveAspectRatio=True)
        pie = [(u'Fecha :     /     /   ', 'Solicitado por:', 'Jefe de Departamento', u'V° B° Gerente Inmediato',u'Vº Bº Gerente Adm.',u'Vº Bº Presupuesto')]
        tabla_observaciones = Table(encabezados+cuerpo+pie,colWidths=[2.8 * cm, 3.1 * cm, 3.4 * cm,3.4* cm, 3.4 * cm, 3.4 * cm], rowHeights=[0.5 * cm,2 * cm,0.5 * cm])
        tabla_observaciones.setStyle(TableStyle(
            [
                ('GRID', (0, 0), (5, 2), 1, colors.black),
                ('FONTSIZE', (0, 0), (-1, -1), 8),
                ('ALIGN',(0,0),(-1,-1),'LEFT'),
                ('ALIGN',(0,2),(5,2),'CENTER'),
                ('VALIGN',(0,0),(-1,-1),'TOP'),
            ]
        ))
        tabla_observaciones.wrapOn(pdf, 800, 600)
        tabla_observaciones.drawOn(pdf, 20,y-70)
        
    def get(self, request, *args, **kwargs): 
        codigo = kwargs['codigo']
        requerimiento = Requerimiento.objects.get(codigo=codigo)        
        response = HttpResponse(content_type='application/pdf')
        #response['Content-Disposition'] = 'attachment; filename="resume.pdf"'
        buffer = BytesIO()
        pdf = canvas.Canvas(buffer)  
        self.cabecera(pdf, requerimiento)
        y=300
        self.detalle(pdf, y, requerimiento)
        self.cuadro_observaciones(pdf, y, requerimiento)
        self.firmas(pdf, y, requerimiento)
        pdf.showPage()    
        pdf.save()
        pdf = buffer.getvalue()
        buffer.close()
        response.write(pdf)
        return response
