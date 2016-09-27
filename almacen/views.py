# -*- coding: utf-8 -*- 
from django.shortcuts import render
from almacen.models import Almacen, Movimiento, Kardex,TipoMovimiento,  DetalleMovimiento, ControlProductoAlmacen,\
    Pedido, DetallePedido
from django.http import HttpResponse, HttpResponseRedirect
from django.core.urlresolvers import reverse, reverse_lazy
import datetime
from django.views.generic import TemplateView, FormView, View, ListView
from almacen.forms import AlmacenForm, TipoStockForm, TipoSalidaForm,FormularioDetalleMovimiento, TipoMovimientoForm, FormularioReporteMovimientos,\
    FormularioKardexProducto, CargarInventarioInicialForm, FormularioPedido, FormularioDetallePedido,\
    FormularioAprobacionPedido, FormularioReporteStock, MovimientoForm,\
    DetalleIngresoFormSet, DetalleSalidaFormSet, PedidoForm,\
    DetallePedidoFormSet
from django.db.models import Sum
from decimal import Decimal
from io import BytesIO
from reportlab.platypus import SimpleDocTemplate, Paragraph, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.platypus import Table
from django.http import JsonResponse
from compras.models import DetalleOrdenCompra,OrdenCompra
from openpyxl import Workbook
import simplejson
import json
from django.conf import settings
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import cm
from django.views.generic.detail import DetailView
from django.views.generic.edit import UpdateView, CreateView
from reportlab.lib.enums import TA_JUSTIFY
from administracion.models import Puesto
import locale
from contabilidad.models import Tipo, Configuracion, Empresa
import csv
from contabilidad.forms import UploadForm
import os
from django.contrib.auth.decorators import permission_required
from django.utils.decorators import method_decorator
from django.db.models import Q
from django.db import transaction, IntegrityError
from django.contrib import messages
from productos.models import Producto

locale.setlocale(locale.LC_ALL,"")
empresa = Empresa.load()

class Tablero(View):
    
    def get(self, request, *args, **kwargs):
        cod_mov_invent_ini = 'I00'
        cod_mov_ingreso_compra = 'I01'
        cod_mov_salida_pedido = 'S01'
        lista_notificaciones = []
        cant_almacenes = Almacen.objects.count()
        cant_tipos_documento = Tipo.objects.filter(tabla="tipo_documento",descripcion_campo="tipo_documento").count()
        cant_tipos_movimientos_ingreso = TipoMovimiento.objects.filter(incrementa=True).exclude(codigo=cod_mov_invent_ini).count()
        cant_tipos_movimientos_salida = TipoMovimiento.objects.filter(incrementa=False).count()
        inventario_inicial = Movimiento.objects.filter(tipo_movimiento=cod_mov_invent_ini).count()
        tipo_movimiento, creado = TipoMovimiento.objects.get_or_create(codigo = cod_mov_invent_ini,
                                                                       defaults = {'descripcion':'INVENTARIO INICIAL',
                                                                                   'incrementa':True,
                                                                                   'estado':True})
        if creado:
            lista_notificaciones.append("Se ha creado el tipo de movimiento inventario inicial")
        tipo_movimiento, creado = TipoMovimiento.objects.get_or_create(codigo = cod_mov_ingreso_compra,
                                                                       defaults = {'descripcion':'INGRESO POR COMPRA',
                                                                                   'incrementa':True,
                                                                                   'pide_referencia':True,
                                                                                   'estado':True})
        if creado:
            lista_notificaciones.append("Se ha creado el tipo de movimiento Ingreso por Compra")
        tipo_movimiento, creado = TipoMovimiento.objects.get_or_create(codigo = cod_mov_salida_pedido,
                                                                       defaults = {'descripcion':'SALIDA POR PEDIDO',
                                                                                   'incrementa':False,
                                                                                   'pide_referencia':True,
                                                                                   'estado':True})
        if creado:
            lista_notificaciones.append("Se ha creado el tipo de movimiento Salida por Pedido")                            
        if cant_almacenes==0:
            lista_notificaciones.append("No se ha creado ningún almacen")            
        if cant_tipos_documento == 0:
            lista_notificaciones.append("No se ha creado ningún tipo de documento")       
        if cant_tipos_movimientos_ingreso == 0:
            lista_notificaciones.append("No se ha creado ningún tipo de movimiento de ingreso")            
        if cant_tipos_movimientos_salida == 0:
            lista_notificaciones.append("No se ha creado ningún tipo de movimiento de salida")        
        if inventario_inicial == 0:
            lista_notificaciones.append("No se ha realizado el inventario inicial")            
        context = {'notificaciones':lista_notificaciones}
        return render(request, 'almacen/tablero_almacen.html', context)
    
class AprobarPedido(FormView):
    template_name = 'almacen/aprobar_pedido.html'
    form_class = FormularioAprobacionPedido
    
    @method_decorator(permission_required('almacen.aprobar_pedido',reverse_lazy('seguridad:permiso_denegado')))
    def dispatch(self, *args, **kwargs):
        try:
            trabajador = self.request.user.trabajador
        except:
            return HttpResponseRedirect(reverse('administracion:crear_trabajador'))        
        try:
            puestos = trabajador.puesto_set.all().filter(estado=True)
            configuracion = Configuracion.objects.first()
            logistica = configuracion.logistica
            if trabajador.firma == '':
                return HttpResponseRedirect(reverse('administracion:modificar_trabajador'))
            if puestos[0].es_jefatura and puestos[0].oficina == logistica:
                return super(AprobarPedido, self).dispatch(*args, **kwargs)
            else:
                return HttpResponseRedirect(reverse('seguridad:permiso_denegado'))
        except:
            return HttpResponseRedirect(reverse('seguridad:permiso_denegado'))
    
    def get_initial(self):
        initial = super(AprobarPedido, self).get_initial()
        initial['cod_pedido'] = self.codigo
        return initial
    
    def get(self, request, *args, **kwargs):
        self.codigo = kwargs['codigo']  
        return super(AprobarPedido, self).get(request, *args, **kwargs)
    
    def get_context_data(self, **kwargs):
        pedido = Pedido.objects.get(codigo = self.codigo)
        detalles = DetallePedido.objects.filter(pedido=pedido,estado=DetallePedido.STATUS.PEND)
        cant_detalles = detalles.count()
        context = super(AprobarPedido, self).get_context_data(**kwargs)
        context['pedido'] = pedido
        context['detalles'] = detalles
        context['cant_detalles'] = cant_detalles
        return context
    
    def obtener_fecha_hora(self,r_fecha,r_hora):
        anio = int(r_fecha[6:])
        mes = int(r_fecha[3:5])
        dia = int(r_fecha[0:2])
        horas = int(r_hora[0:2])
        minutos = int(r_hora[3:5])
        segundos = int(r_hora[6:8])
        fecha = datetime.datetime(anio,mes,dia,horas,minutos,segundos)
        return fecha
    
    def guardar_cabecera_movimiento(self,tipo_salida, fecha_operacion, almacen, usuario, total, referencia, oficina, observaciones):
        tipo_movimiento = TipoMovimiento.objects.get(codigo=tipo_salida)
        movimiento = Movimiento.objects.create(tipo_movimiento = tipo_movimiento,
                                               almacen = almacen,
                                               fecha_operacion = fecha_operacion,
                                               total = total,
                                               oficina = oficina,
                                               observacion = observaciones)
        return movimiento
        
    def guardar_detalle_con_referencia(self,cdetalles,referencia, movimiento):
        request=self.request
        pedido_abierto = False
        cont_detalles = 1;
        estado_pedido = Pedido.STATUS.PEND
        for i in range(cdetalles):
            try:
                r_cod_detalle="detalle_pedido"+str(i+1)
                r_cantidad="cantidad"+str(i+1)
                r_precio="precio"+str(i+1)
                r_valor="valor"+str(i+1)
                cantidad = Decimal(request.POST[r_cantidad])
                precio= Decimal(request.POST[r_precio])
                valor = Decimal(request.POST[r_valor])
                id_detalle_orden = request.POST[r_cod_detalle]                
                detalle_pedido = DetallePedido.objects.get(pk = id_detalle_orden)
                producto = detalle_pedido.producto 
                self.guardar_detalle_movimiento(cont_detalles, detalle_pedido, movimiento, producto, cantidad, precio, valor)
                detalle_pedido.cantidad_atendida = detalle_pedido.cantidad_atendida+cantidad            
                if detalle_pedido.cantidad_atendida<detalle_pedido.cantidad:
                    detalle_pedido.estado=DetallePedido.STATUS.ATEN_PARC
                    estado_pedido = Pedido.STATUS.ATEN_PARC
                elif detalle_pedido.cantidad_atendida==detalle_pedido.cantidad:
                    detalle_pedido.estado=DetallePedido.STATUS.ATEN
                detalle_pedido.save()
                cont_detalles = cont_detalles + 1
            except:
                estado_pedido = Pedido.STATUS.ATEN_PARC    
        if estado_pedido <> Pedido.STATUS.ATEN_PARC:
            estado_pedido = Pedido.STATUS.ATEN
        referencia.estado = estado_pedido                    
        referencia.save()

    def guardar_detalle_movimiento(self,cont_detalles,detalle_pedido,movimiento,producto,cantidad, precio,valor):
        DetalleMovimiento.objects.create(detalle_pedido=detalle_pedido,
                                         nro_detalle=cont_detalles,
                                         movimiento=movimiento,
                                         producto=producto,
                                         cantidad=cantidad,
                                         precio=precio,
                                         valor = valor)
        
    def guardar_aprobacion(self,codigo, r_almacen, cdetalles, r_fecha, r_hora, total, observaciones):
        pedido = Pedido.objects.get(codigo=codigo)
        tipo_salida = 'S01'
        oficina = pedido.oficina
        referencia = pedido
        request = self.request
        fecha_operacion = self.obtener_fecha_hora(r_fecha, r_hora)
        almacen = Almacen.objects.get(codigo=r_almacen)
        usuario = request.user
        with transaction.atomic():
            movimiento = self.guardar_cabecera_movimiento(tipo_salida, fecha_operacion, almacen, usuario, total, referencia, oficina, observaciones)
            self.guardar_detalle_con_referencia(cdetalles, referencia, movimiento)            
        return movimiento
        
    def post(self, request, *args, **kwargs):
        codigo = request.POST['cod_pedido']
        r_almacen = request.POST['almacenes']
        r_fecha = request.POST['fecha']
        r_hora = request.POST['hora'].replace(" ","")
        cdetalles = int(request.POST['cdetalles'])
        total = request.POST['total']
        observaciones = request.POST['observaciones']        
        movimiento = self.guardar_aprobacion(codigo, r_almacen, cdetalles, r_fecha, r_hora, total, observaciones)
        return HttpResponseRedirect(reverse('almacen:detalle_movimiento', args=[movimiento]))
    
class BusquedaProductosAlmacen(TemplateView):
    
    def get(self, request, *args, **kwargs):
        if request.is_ajax():
            descripcion = request.GET['descripcion']
            almacen = request.GET['almacen']
            print descripcion
            print almacen
            control_productos = ControlProductoAlmacen.objects.filter(almacen__codigo=almacen,producto__descripcion__icontains = descripcion)[:20]    
            lista_productos = []
            for control in control_productos:
                print control.producto.descripcion
                producto_json = {}                
                producto_json['label'] = control.producto.descripcion
                producto_json['codigo'] = control.producto.codigo
                producto_json['descripcion'] = control.producto.descripcion
                producto_json['unidad'] = control.producto.unidad_medida.descripcion
                producto_json['precio'] = str(control.precio)
                print producto_json
                lista_productos.append(producto_json)                            
            print lista_productos
            data = json.dumps(lista_productos)
            print data
            return HttpResponse(data, 'application/json')

class CargarAlmacenes(FormView):
    template_name = 'almacen/cargar_almacenes.html'
    form_class = UploadForm
    
    def form_valid(self, form):
        data = form.cleaned_data
        docfile = data['archivo']            
        form.save()
        csv_filepathname = os.path.join(settings.MEDIA_ROOT,'archivos',str(docfile))
        dataReader = csv.reader(open(csv_filepathname), delimiter=',', quotechar='"')
        for fila in dataReader:
            Almacen.objects.create(codigo=fila[0],
                                   descripcion=unicode(fila[1], errors='ignore'))                        
        return HttpResponseRedirect(reverse('almacen:almacenes'))
    
class CargarInventarioInicial(FormView):
    template_name = 'almacen/cargar_inventario_inicial.html'
    form_class = CargarInventarioInicialForm
    
    def obtener_fecha_hora(self,r_fecha,r_hora):
        r_hora = r_hora.replace(" ","")
        anio = int(r_fecha[6:])
        mes = int(r_fecha[3:5])
        dia = int(r_fecha[0:2])
        horas = int(r_hora[0:2])
        minutos = int(r_hora[3:5])
        segundos = int(r_hora[6:8])
        fecha = datetime.datetime(anio,mes,dia,horas,minutos,segundos)
        return fecha
    
    def form_valid(self, form):
        data = form.cleaned_data
        docfile = data['archivo']
        fecha = data['fecha']
        hora = data['hora']
        almacen = data['almacenes']
        form.save()
        fecha_operacion = self.obtener_fecha_hora(fecha, hora)
        usuario = self.request.user
        csv_filepathname = os.path.join(settings.MEDIA_ROOT,'archivos',str(docfile))
        dataReader = csv.reader(open(csv_filepathname), delimiter=',', quotechar='"')
        tipo_movimiento = TipoMovimiento.objects.get(codigo='I00')
        with transaction.atomic():            
            movimiento = Movimiento.objects.create(tipo_movimiento = tipo_movimiento,
                                                   almacen = almacen,
                                                   fecha_operacion=fecha_operacion,
                                                   total = 0,
                                                   observaciones = 'INVENTARIO INICIAL')
            
            cont_detalles = 1
            detalles = []
            total = 0
            for fila in dataReader:
                producto = Producto.objects.get(descripcion=unicode(fila[0], errors='ignore'))
                cantidad = Decimal(fila[1])
                precio = Decimal(fila[2])
                valor = cantidad * precio
                detalle_movimiento = DetalleMovimiento(nro_detalle=cont_detalles,
                                                       movimiento=movimiento,
                                                       producto=producto,
                                                       cantidad=cantidad,
                                                       precio=precio,
                                                       valor = valor)
                detalles.append(detalle_movimiento) 
                total = total + valor
                cont_detalles = cont_detalles + 1
                DetalleMovimiento.objects.bulk_create(detalles,None)
            movimiento.total = total
            movimiento.save()
        return HttpResponseRedirect(reverse('almacen:modificar_movimiento', args=[movimiento.id_movimiento]))
    
class CrearTipoMovimiento(CreateView):
    template_name = 'almacen/crear_tipo_movimiento.html'
    form_class = TipoMovimientoForm
    success_url = reverse_lazy('almacen:tipos_movimientos')

    @method_decorator(permission_required('almacen.add_tipomovimiento',reverse_lazy('seguridad:permiso_denegado')))
    def dispatch(self, *args, **kwargs):
        return super(CrearTipoMovimiento, self).dispatch(*args, **kwargs)
    
    def get_success_url(self):
        return reverse('almacen:detalle_tipo_movimiento', args=[self.object.pk])
    
class CrearTipoSalida(FormView):
    template_name = 'almacen/crear_tipo_salida.html'
    form_class = TipoSalidaForm
    success_url = reverse_lazy('almacen:crear_tipo_salida')

    def form_valid(self, form):
        form.save()
        return super(CrearTipoSalida, self).form_valid(form)  
    
class CrearTipoStock(View):
    
    def get(self, request, *args, **kwargs):
        form = TipoStockForm()        
        return render(request, 'crear_tipo_stock.html', {'form': form})
    
    '''template_name = 'almacen/crear_tipo_stock.html'
    form_class = TipoStockForm
    success_url = reverse_lazy('almacen:crear_tipo_stock')

    def form_valid(self, form):
        form.save()
        return super(CrearTipoStock, self).form_valid(form)'''

class CrearAlmacen(FormView):
    template_name = 'almacen/crear_almacen.html'
    form_class = AlmacenForm
    success_url = reverse_lazy('almacen:almacenes')

    def form_valid(self, form):
        form.save()
        return super(CrearAlmacen, self).form_valid(form)
    
'''class CrearDetalleSalida(FormView):
    template_name = 'almacen/crear_detalle_salida.html'
    form_class = FormularioDetalleMovimiento
    success_url = reverse_lazy('almacen:crear_detalle_salida')
    
    def get(self, request, *args, **kwargs):
        self.almacen = kwargs['almacen']
        return super(CrearDetalleSalida, self).get(request, *args, **kwargs)
    
    def get_initial(self):
        initial = super(CrearDetalleSalida, self).get_initial()        
        initial['almacen'] = self.almacen       
        return initial

    def form_valid(self, form):
        form.save()
        return super(CrearDetalleSalida, self).form_valid(form)'''
    
class CrearDetalleSalida(TemplateView):
        
    def get(self, request, *args, **kwargs):
        if request.is_ajax():
            lista_detalles = []            
            det = {}
            det['codigo'] = ''               
            det['nombre'] = ''                    
            det['cantidad'] = '0'
            det['precio'] = '0'
            det['unidad'] = ''
            det['valor'] = '0'
            lista_detalles.append(det)
            formset = DetalleSalidaFormSet(initial=lista_detalles)
            lista_json = []
            for form in formset:
                detalle_json = {}    
                detalle_json['codigo'] = str(form['codigo'])
                detalle_json['nombre'] = str(form['nombre'])
                detalle_json['cantidad'] = str(form['cantidad'])
                detalle_json['precio'] = str(form['precio'])
                detalle_json['unidad'] = str(form['unidad'])                
                detalle_json['valor'] = str(form['valor'])
                lista_json.append(detalle_json)                                
            data = json.dumps(lista_json)
            return HttpResponse(data, 'application/json')
        
class CrearDetallePedido(TemplateView):
        
    def get(self, request, *args, **kwargs):
        if request.is_ajax():
            lista_detalles = []            
            det = {}
            det['codigo'] = ''               
            det['nombre'] = ''                    
            det['cantidad'] = '0'
            det['unidad'] = ''            
            lista_detalles.append(det)
            formset = DetallePedidoFormSet(initial=lista_detalles)
            lista_json = []
            for form in formset:
                detalle_json = {}    
                detalle_json['codigo'] = str(form['codigo'])
                detalle_json['nombre'] = str(form['nombre'])
                detalle_json['cantidad'] = str(form['cantidad'])
                detalle_json['unidad'] = str(form['unidad'])
                lista_json.append(detalle_json)
            data = json.dumps(lista_json)
            return HttpResponse(data, 'application/json')

class CrearDetalleIngreso(TemplateView):
        
    def get(self, request, *args, **kwargs):
        if request.is_ajax():
            lista_detalles = []            
            det = {}
            det['orden_compra'] = '0'
            det['codigo'] = ''               
            det['nombre'] = ''                    
            det['cantidad'] = '0'
            det['precio'] = '0'
            det['unidad'] = ''
            det['valor'] = '0'
            lista_detalles.append(det)
            formset = DetalleIngresoFormSet(initial=lista_detalles)
            lista_json = []
            for form in formset:
                detalle_json = {}    
                detalle_json['orden_compra'] = str(form['orden_compra'])
                detalle_json['codigo'] = str(form['codigo'])
                detalle_json['nombre'] = str(form['nombre'])
                detalle_json['cantidad'] = str(form['cantidad'])
                detalle_json['precio'] = str(form['precio'])
                detalle_json['unidad'] = str(form['unidad'])                
                detalle_json['valor'] = str(form['valor'])
                lista_json.append(detalle_json)                                
            data = json.dumps(lista_json)
            return HttpResponse(data, 'application/json')
    
class CrearPedido(CreateView):
    template_name = 'almacen/crear_pedido.html'
    form_class = PedidoForm
    model = Pedido
    
    @method_decorator(permission_required('almacen.add_pedido',reverse_lazy('seguridad:permiso_denegado')))
    def dispatch(self, *args, **kwargs):
        try:
            trabajador = self.request.user.trabajador
        except:
            return HttpResponseRedirect(reverse('seguridad:permiso_denegado'))
        try:
            puesto_usuario = Puesto.objects.get(trabajador = trabajador)
            if puesto_usuario.es_jefatura:                
                if trabajador.firma:
                    return super(CrearPedido, self).dispatch(*args, **kwargs)
                else:
                    return HttpResponseRedirect(reverse('administracion:modificar_trabajador',args=[trabajador.pk]))
            else:
                return HttpResponseRedirect(reverse('seguridad:permiso_denegado'))
        except Puesto.DoesNotExist:
            return HttpResponseRedirect(reverse('administracion:crear_puesto'))
    
    def get(self, request, *args, **kwargs):
        self.object = None        
        form_class = self.get_form_class()
        form = self.get_form(form_class)
        detalle_pedido_formset=DetallePedidoFormSet()
        return self.render_to_response(self.get_context_data(form=form,
                                                             detalle_pedido_formset = detalle_pedido_formset))
        
    def get_form_kwargs(self):
        kwargs = super(CrearPedido, self).get_form_kwargs()
        kwargs['request'] = self.request
        return kwargs

    def post(self, request, *args, **kwargs):
        self.object = None
        form_class = self.get_form_class()
        form = self.get_form(form_class)
        detalle_pedido_formset = DetallePedidoFormSet(request.POST)
        if form.is_valid() and detalle_pedido_formset.is_valid():
            return self.form_valid(form, detalle_pedido_formset)
        else:
            return self.form_invalid(form, detalle_pedido_formset)
    
    def form_valid(self, form, detalle_pedido_formset):
        try:
            with transaction.atomic():
                self.object = form.save()        
                detalles = []
                cont = 1
                for detalle_pedido_form in detalle_pedido_formset:                
                    codigo = detalle_pedido_form.cleaned_data.get('codigo')
                    cantidad = detalle_pedido_form.cleaned_data.get('cantidad')
                    if codigo and cantidad:                                
                        producto = Producto.objects.get(codigo=codigo)                
                        detalles.append(DetallePedido(pedido=self.object, nro_detalle=cont, producto=producto, cantidad=cantidad))
                        cont = cont + 1                    
                DetallePedido.objects.bulk_create(detalles)
                return HttpResponseRedirect(reverse('almacen:detalle_pedido', args=[self.object.pk]))
        except IntegrityError:
                messages.error(self.request, 'Error guardando el pedido.')
        
    def form_invalid(self, form, detalle_pedido_formset):
        return self.render_to_response(self.get_context_data(form=form,
                                                             detalle_pedido_formset=detalle_pedido_formset))
    
class ConsultaStock(TemplateView):
    def get(self, request, *args, **kwargs):
        if request.is_ajax():
            almacen = request.GET['almacen']
            codigo = request.GET['codigo']
            control_producto = ControlProductoAlmacen.objects.get(almacen__codigo = almacen,producto__codigo = codigo)  
            producto_json = {}                
            producto_json['stock'] = control_producto.stock
            data = simplejson.dumps(producto_json)
            return HttpResponse(data, 'application/json')

class DetalleAlmacen(DetailView):
    model = Almacen
    template_name = 'almacen/detalle_almacen.html'
    
class DetalleTipoMovimiento(DetailView):
    model = TipoMovimiento
    template_name = 'almacen/detalle_tipo_movimiento.html'

class DetalleOperacionPedido(DetailView):
    model = Pedido
    template_name = 'almacen/detalle_pedido.html'    
    
class DetalleOperacionMovimiento(DetailView):
    model = Movimiento
    template_name = 'almacen/detalle_movimiento.html'

class EliminarAlmacen(TemplateView):
    
    def get(self, request, *args, **kwargs):
        if request.is_ajax():
            codigo = request.GET['codigo']
            almacen = Almacen.objects.get(pk=codigo)
            almacen_json = {}
            almacen_json['codigo'] = almacen.codigo
            almacen_json['descripcion'] = almacen.descripcion
            if len(almacen.movimiento_set.all())>0:
                almacen_json['relaciones'] = 'SI'
            else:
                almacen_json['relaciones'] = 'NO'
                Almacen.objects.filter(pk=codigo).update(estado = False)                
            data = simplejson.dumps(almacen_json)
            return HttpResponse(data, 'application/json')
    
class EliminarMovimiento(TemplateView):
    
    def get(self, request, *args, **kwargs):
        if request.is_ajax():
            id_movimiento = request.GET['id_movimiento']
            movimiento = Movimiento.objects.get(id_movimiento=id_movimiento)
            orden = movimiento.referencia
            if orden is not None:
                orden.abierta = True    
                orden.save()        
            detalle_kardex = Kardex.objects.filter(movimiento__id_movimiento = id_movimiento)
            for kardex in detalle_kardex:
                control = ControlProductoAlmacen.objects.get(producto=kardex.producto)
                if kardex.cantidad_ingreso>0:                    
                    control.stock = control.stock - kardex.cantidad_ingreso
                    try:
                        detalle_orden = DetalleOrdenCompra.objects.get(orden=orden,producto=kardex.producto)
                        detalle_orden.cantidad_atendida = detalle_orden.cantidad_atendida - kardex.cantidad_ingreso
                        detalle_orden.abierta = True 
                        detalle_orden.save()
                    except DetalleOrdenCompra.DoesNotExist:
                        pass                    
                elif kardex.cantidad_salida > 0:
                    control.stock = control.stock + kardex.cantidad_salida
                control.save()
                kardex.delete()             
            Movimiento.objects.filter(id_movimiento=id_movimiento).update(estado = Movimiento.STATUS.CANC, referencia=None)
            DetalleMovimiento.objects.filter(movimiento=movimiento).delete()
            movimiento_json = {}
            movimiento_json['id_movimiento'] = id_movimiento
            data = simplejson.dumps(movimiento_json)
            return HttpResponse(data, 'application/json')

class InicioOperaciones(TemplateView):
    template_name = "inicio_operaciones.html"    
    
class ListadoAprobacionPedidos(ListView):
    model = Pedido
    template_name = 'almacen/listado_pedidos.html'
    context_object_name = 'pedidos'    
    
    @method_decorator(permission_required('almacen.ver_tabla_aprobacion_pedidos',reverse_lazy('seguridad:permiso_denegado')))
    def dispatch(self, *args, **kwargs):
        try:
            trabajador = self.request.user.trabajador
        except:
            return HttpResponseRedirect(reverse('administracion:crear_trabajador'))        
        try:
            puestos = trabajador.puesto_set.all().filter(estado=True)
            configuracion = Configuracion.objects.first()
            logistica = configuracion.logistica            
            if trabajador.firma == '':
                return HttpResponseRedirect(reverse('administracion:modificar_trabajador'))
            if puestos[0].es_jefatura and puestos[0].oficina == logistica:
                return super(ListadoAprobacionPedidos, self).dispatch(*args, **kwargs)
            else:
                return HttpResponseRedirect(reverse('seguridad:permiso_denegado'))
        except:
            return HttpResponseRedirect(reverse('seguridad:permiso_denegado'))
    
    def get_queryset(self):
        queryset = Pedido.objects.filter(~Q(estado = Pedido.STATUS.APROB))
        return queryset
    
class ListadoAlmacenes(ListView):
    model = Almacen
    template_name = 'almacen/almacenes.html'
    context_object_name = 'almacenes'
    queryset = Almacen.objects.all().order_by('descripcion')

class ListadoPedidos(ListView):
    model = Pedido
    template_name = 'almacen/listado_pedidos.html'
    context_object_name = 'pedidos'
    queryset = Pedido.objects.all().order_by('codigo')
    
class ListadoTiposUnidadMedida(ListView):
    model = Tipo
    template_name = 'almacen/tipos.html'
    context_object_name = 'tipos'
    paginate_by = 10
    queryset = Tipo.objects.filter(tabla="tipo_unidad_medida",descripcion_campo="tipo_unidad_medida").order_by('descripcion_valor')

    def get_context_data(self, **kwargs):
        context = super(ListadoTiposUnidadMedida, self).get_context_data(**kwargs)
        context['tabla'] = 'tipo_unidad_medida'
        return context
    
class ListadoTiposStock(ListView):
    model = Tipo
    template_name = 'almacen/tipos.html'
    context_object_name = 'tipos'
    paginate_by = 10
    queryset = Tipo.objects.filter(tabla="tipo_stock",descripcion_campo="tipo_stock").order_by('descripcion_valor')

    def get_context_data(self, **kwargs):
        context = super(ListadoTiposStock, self).get_context_data(**kwargs)
        context['tabla'] = 'tipo_stock'
        return context

class ListadoTiposMovimiento(ListView):
    model = TipoMovimiento
    template_name = 'almacen/tipos_movimiento.html'
    context_object_name = 'tipos_movimiento'
    paginate_by = 10
    queryset = TipoMovimiento.objects.all().order_by('codigo')
    
class ListadoMovimientos(ListView):
    model = Movimiento
    template_name = 'almacen/movimientos.html'
    context_object_name = 'movimientos'
    queryset = Movimiento.objects.filter(estado=Movimiento.STATUS.ACT)    

class ListadoIngresos(ListView):
    model = Movimiento
    template_name = 'almacen/listado_ingresos.html'
    context_object_name = 'movimientos'
    queryset = Movimiento.objects.filter(estado=Movimiento.STATUS.ACT, tipo_movimiento__incrementa=True) 
    
class ListadoSalidas(ListView):
    model = Movimiento
    template_name = 'almacen/listado_salidas.html'
    context_object_name = 'movimientos'
    queryset = Movimiento.objects.filter(estado=Movimiento.STATUS.ACT, tipo_movimiento__incrementa=False) 

class ModificarMovimiento(TemplateView):    
    
    def get(self, request, *args, **kwargs):  
        id_movimiento = kwargs['id_movimiento']
        movimiento = Movimiento.objects.get(id_movimiento=id_movimiento)
        tipo_movimiento = movimiento.tipo_movimiento
        if tipo_movimiento.incrementa:
            return HttpResponseRedirect(reverse('almacen:modificar_ingreso_almacen', args=[movimiento.id_movimiento]))
        else:
            return HttpResponseRedirect(reverse('almacen:modificar_salida_almacen', args=[movimiento.id_movimiento]))   
    
class ModificarIngresoAlmacen(UpdateView):
    template_name = 'almacen/ingreso_almacen.html'
    form_class = MovimientoForm
    model = Movimiento
    
    def get_form_kwargs(self):
        kwargs = super(ModificarIngresoAlmacen, self).get_form_kwargs()
        kwargs['tipo_movimiento'] = 'I'
        return kwargs
    
    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        if self.object.estado == Movimiento.STATUS.ACT:            
            form_class = self.get_form_class()
            form = self.get_form(form_class)
            detalles = DetalleMovimiento.objects.filter(movimiento=self.object).order_by('nro_detalle')
            detalles_data = []
            for detalle in detalles:
                try:
                    d = {'orden_compra': detalle.detalle_orden_compra.pk,
                         'codigo': detalle.detalle_orden_compra.detalle_cotizacion.detalle_requerimiento.producto.codigo,
                         'nombre': detalle.detalle_orden_compra.detalle_cotizacion.detalle_requerimiento.producto.descripcion,
                         'unidad': detalle.detalle_orden_compra.detalle_cotizacion.detalle_requerimiento.producto.unidad_medida.codigo,
                         'cantidad': detalle.cantidad,
                         'precio': detalle.precio,
                         'valor': detalle.valor }
                except:
                    d = {'orden_compra': '0',
                         'codigo': detalle.producto.codigo,
                         'nombre': detalle.producto.descripcion,
                         'unidad': detalle.producto.unidad_medida.codigo,
                         'cantidad': detalle.cantidad,
                         'precio': detalle.precio,
                         'valor': detalle.valor }
                detalles_data.append(d)
            detalle_ingreso_formset = DetalleIngresoFormSet(initial=detalles_data)
            return self.render_to_response(self.get_context_data(form=form,
                                                                 detalle_ingreso_formset=detalle_ingreso_formset))            
        else:
            return HttpResponseRedirect(reverse('almacen:listado_ingresos'))
    
    def get_initial(self):
        initial = super(ModificarIngresoAlmacen, self).get_initial()
        movimiento = self.object
        initial['id_movimiento'] = movimiento.id_movimiento
        initial['fecha'] = movimiento.fecha_operacion.strftime('%d/%m/%Y')
        initial['hora'] = movimiento.fecha_operacion.strftime('%H : %M : %S')
        initial['almacen'] = movimiento.almacen
        initial['tipo_movimiento'] = movimiento.tipo_movimiento
        initial['doc_referencia'] = movimiento.referencia     
        initial['tipo_documento'] = movimiento.tipo_documento
        initial['serie'] = movimiento.serie
        initial['numero'] = movimiento.numero
        initial['total'] = movimiento.total
        initial['observaciones'] = movimiento.observaciones
        return initial 
        
    def get_context_data(self, **kwargs):
        movimiento = self.object        
        context = super(ModificarIngresoAlmacen, self).get_context_data(**kwargs)
        context['movimiento'] = movimiento
        return context
    
    def post(self, request, *args, **kwargs):                      
        self.object = self.get_object()
        form_class = self.get_form_class()
        form = self.get_form(form_class)
        detalle_ingreso_formset = DetalleIngresoFormSet(request.POST)
        if form.is_valid() and detalle_ingreso_formset.is_valid():
            return self.form_valid(form, detalle_ingreso_formset)
        else:
            return self.form_invalid(form, detalle_ingreso_formset)
    
    def form_valid(self, form, detalle_ingreso_formset):
        try:
            with transaction.atomic():
                if self.object.referencia:
                    self.object.eliminar_referencia()
                self.object.eliminar_kardex()
                self.object.eliminar_detalles()
                self.object = form.save()
                referencia = self.object.referencia
                detalles = []
                cont = 1                
                for detalle_ingreso_form in detalle_ingreso_formset:
                    orden_compra = detalle_ingreso_form.cleaned_data.get('orden_compra')
                    codigo = detalle_ingreso_form.cleaned_data.get('codigo') 
                    cantidad = detalle_ingreso_form.cleaned_data.get('cantidad')
                    precio = detalle_ingreso_form.cleaned_data.get('precio')
                    valor = detalle_ingreso_form.cleaned_data.get('valor')                    
                    if cantidad and precio and valor:
                        try:
                            detalle_orden_compra = DetalleOrdenCompra.objects.get(pk=orden_compra)
                            detalle_movimiento = DetalleMovimiento(detalle_orden_compra=detalle_orden_compra,
                                                                   nro_detalle=cont,
                                                                   movimiento=self.object,
                                                                   producto=Producto.objects.get(pk=codigo),
                                                                   cantidad=cantidad,
                                                                   precio=precio,
                                                                   valor = valor) 
                        except:
                            detalle_movimiento = DetalleMovimiento(nro_detalle=cont,
                                                                   movimiento=self.object,
                                                                   producto=Producto.objects.get(pk=codigo),
                                                                   cantidad=cantidad,
                                                                   precio=precio,
                                                                   valor = valor)
                        detalles.append(detalle_movimiento)                        
                        cont = cont + 1
                DetalleMovimiento.objects.bulk_create(detalles, referencia) 
                return HttpResponseRedirect(reverse('almacen:detalle_movimiento', args=[self.object.id_movimiento]))
        except IntegrityError:
            messages.error(self.request, 'Error guardando la cotizacion.')
        
    def form_invalid(self, form, detalle_ingreso_formset):
        return self.render_to_response(self.get_context_data(form=form))
    
class ModificarSalidaAlmacen(UpdateView):
    template_name = 'almacen/salida_almacen.html'
    form_class = MovimientoForm
    model = Movimiento
    
    def get_form_kwargs(self):
        kwargs = super(ModificarSalidaAlmacen, self).get_form_kwargs()
        kwargs['tipo_movimiento'] = 'S'
        return kwargs
    
    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        form_class = self.get_form_class()
        form = self.get_form(form_class)
        detalles = DetalleMovimiento.objects.filter(movimiento = self.object)
        detalles_data = []
        for detalle in detalles:
            d = {'codigo': detalle.producto.pk,
                 'nombre': detalle.producto.descripcion,
                 'unidad': detalle.producto.unidad_medida,
                 'cantidad': detalle.cantidad,
                 'precio': detalle.precio,
                 'valor': detalle.valor }
            detalles_data.append(d)
        detalle_salida_formset = DetalleSalidaFormSet(initial=detalles_data)
        return self.render_to_response(self.get_context_data(form=form,
                                                             detalle_salida_formset = detalle_salida_formset))        
    
    def get_initial(self):
        initial = super(ModificarSalidaAlmacen, self).get_initial()
        movimiento = self.object
        self.detalles = DetalleMovimiento.objects.filter(movimiento=movimiento)
        initial['id_movimiento'] = movimiento.id_movimiento
        initial['fecha'] = movimiento.fecha_operacion.strftime('%d/%m/%Y')
        initial['hora'] = movimiento.fecha_operacion.strftime('%H : %M : %S')
        initial['almacenes'] = movimiento.almacen
        initial['tipos_salida'] = movimiento.tipo_movimiento
        initial['oficina'] = movimiento.oficina
        initial['referencia'] = movimiento.referencia     
        initial['doc_referencia'] = movimiento.tipo_documento
        initial['serie'] = movimiento.serie
        initial['numero'] = movimiento.numero
        initial['total'] = movimiento.total
        initial['observaciones'] = movimiento.observaciones 
        initial['cdetalles'] = self.detalles.count()
        return initial 
        
    def get_context_data(self, **kwargs):
        movimiento = self.object       
        context = super(ModificarSalidaAlmacen, self).get_context_data(**kwargs)
        context['movimiento'] = movimiento
        context['detalles'] = self.detalles        
        return context
               
    def post(self, request, *args, **kwargs):                      
        self.object = self.get_object()
        form_class = self.get_form_class()
        form = self.get_form(form_class)
        detalle_salida_formset = DetalleSalidaFormSet(request.POST)
        if form.is_valid() and detalle_salida_formset.is_valid():
            return self.form_valid(form, detalle_salida_formset)
        else:
            return self.form_invalid(form, detalle_salida_formset)
    
    def form_valid(self, form, detalle_salida_formset):
        try:
            with transaction.atomic():
                if self.object.referencia:
                    self.object.eliminar_referencia()
                self.object.eliminar_detalles()
                self.object.eliminar_kardex()
                self.object = form.save()
                referencia = self.object.referencia
                detalles = []
                cont = 1                
                for detalle_salida_form in detalle_salida_formset:
                    codigo = detalle_salida_form.cleaned_data.get('codigo') 
                    cantidad = detalle_salida_form.cleaned_data.get('cantidad')
                    precio = detalle_salida_form.cleaned_data.get('precio')
                    valor = detalle_salida_form.cleaned_data.get('valor')
                    if cantidad and precio and valor:
                        detalle_movimiento = DetalleMovimiento(nro_detalle=cont,
                                                               movimiento=self.object,
                                                               producto=Producto.objects.get(pk=codigo),
                                                               cantidad=cantidad,
                                                               precio=precio,
                                                               valor = valor) 
                        detalles.append(detalle_movimiento)                        
                        cont = cont + 1
                DetalleMovimiento.objects.bulk_create(detalles, referencia) 
                return HttpResponseRedirect(reverse('almacen:detalle_movimiento', args=[self.object.id_movimiento]))
        except IntegrityError:
            messages.error(self.request, 'Error guardando la cotizacion.')
        
    def form_invalid(self, form, detalle_ingreso_formset):
        return self.render_to_response(self.get_context_data(form=form))
    
class ModificarAlmacen(UpdateView):
    model = Almacen
    template_name = 'almacen/modificar_almacen.html'
    form_class = AlmacenForm
    success_url = reverse_lazy('almacen:almacenes')
    
class ModificarPedido(UpdateView):    
    template_name = 'almacen/modificar_pedido.html'
    form_class = PedidoForm
    model = Pedido
    
    def get_form_kwargs(self):
        kwargs = super(ModificarPedido, self).get_form_kwargs()
        kwargs['request'] = self.request
        return kwargs
    
    def get_initial(self):
        initial = super(ModificarPedido, self).get_initial()
        pedido = self.object        
        initial['fecha'] = pedido.fecha.strftime('%d/%m/%Y')
        initial['observaciones'] = pedido.observaciones        
        return initial 
    
    def get_context_data(self, **kwargs):
        pedido = self.object
        detalles = DetallePedido.objects.filter(pedido=pedido).order_by('nro_detalle')
        cant_detalles = detalles.count()
        context = super(ModificarPedido, self).get_context_data(**kwargs)
        context['pedido'] = pedido
        context['detalles'] = detalles
        context['cant_detalles'] = cant_detalles
        return context
    
    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        if self.object.estado == Pedido.STATUS.PEND:            
            form_class = self.get_form_class()
            form = self.get_form(form_class)
            detalles = DetallePedido.objects.filter(pedido = self.object).order_by('nro_detalle')
            detalles_data = []
            for detalle in detalles:
                d = {'codigo': detalle.producto.codigo,
                     'nombre': detalle.producto.descripcion,
                     'unidad': detalle.producto.unidad_medida.codigo,
                     'cantidad': detalle.cantidad}
                detalles_data.append(d)
            detalle_pedido_formset=DetallePedidoFormSet(initial=detalles_data)
            return self.render_to_response(self.get_context_data(form=form,
                                                                 detalle_pedido_formset=detalle_pedido_formset))
    
    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        form_class = self.get_form_class()
        form = self.get_form(form_class)
        detalle_pedido_formset = DetallePedidoFormSet(request.POST)
        if form.is_valid() and detalle_pedido_formset.is_valid():
            return self.form_valid(form, detalle_pedido_formset)
        else:
            return self.form_invalid(form, detalle_pedido_formset)
    
    def form_valid(self, form, detalle_pedido_formset):
        try:
            with transaction.atomic():
                self.object = form.save()
                DetallePedido.objects.filter(pedido=self.object).delete()
                detalles = []
                cont = 1                
                for detalle_pedido_form in detalle_pedido_formset:
                    codigo = detalle_pedido_form.cleaned_data.get('codigo')
                    cantidad = detalle_pedido_form.cleaned_data.get('cantidad')
                    if cantidad:
                        detalle_pedido = DetallePedido(nro_detalle = cont,
                                                       pedido = self.object,
                                                       cantidad = cantidad) 
                        detalles.append(detalle_pedido)                        
                        cont = cont + 1
                DetallePedido.objects.bulk_create(detalles)                
                return HttpResponseRedirect(reverse('almacen:detalle_pedido', args=[self.object.codigo]))
        except IntegrityError:
                messages.error(self.request, 'Error guardando la cotizacion.')
        
    def form_invalid(self, form, detalle_pedido_formset):
        return self.render_to_response(self.get_context_data(form=form,
                                                             detalle_pedido_formset = detalle_pedido_formset))
    
class RegistrarIngresoAlmacen(CreateView):
    template_name = 'almacen/ingreso_almacen.html'
    form_class = MovimientoForm
    model = Movimiento
    
    def get_initial(self):
        initial = super(RegistrarIngresoAlmacen, self).get_initial()
        initial['total'] = 0        
        return initial
    
    def get_form_kwargs(self):
        kwargs = super(RegistrarIngresoAlmacen, self).get_form_kwargs()
        kwargs['tipo_movimiento'] = 'I'
        return kwargs
    
    def get(self, request, *args, **kwargs):
        self.object = None
        cod_tipo_mov = 'I00'
        tipos_ingreso = TipoMovimiento.objects.filter(incrementa=True).exclude(codigo=cod_tipo_mov)        
        if not tipos_ingreso:
            return HttpResponseRedirect(reverse('almacen:crear_tipo_movimiento'))
        almacenes = Almacen.objects.all()
        cant_suministros = Producto.objects.count()
        if almacenes.count()>0:
            if cant_suministros > 0:                    
                form_class = self.get_form_class()
                form = self.get_form(form_class)
                detalle_ingreso_formset=DetalleIngresoFormSet()
                return self.render_to_response(self.get_context_data(form=form,
                                                                     detalle_ingreso_formset=detalle_ingreso_formset))                
        return HttpResponseRedirect(reverse('almacen:tablero'))
    
    def post(self, request, *args, **kwargs):                      
        self.object = None
        form_class = self.get_form_class()
        form = self.get_form(form_class)
        detalle_ingreso_formset = DetalleIngresoFormSet(request.POST)
        if form.is_valid() and detalle_ingreso_formset.is_valid():
            return self.form_valid(form, detalle_ingreso_formset)
        else:
            return self.form_invalid(form, detalle_ingreso_formset)
    
    def form_valid(self, form, detalle_ingreso_formset):
        try:
            with transaction.atomic():
                self.object = form.save()
                referencia = self.object.referencia
                detalles = []
                cont = 1                
                for detalle_ingreso_form in detalle_ingreso_formset:
                    orden_compra = detalle_ingreso_form.cleaned_data.get('orden_compra')
                    codigo = detalle_ingreso_form.cleaned_data.get('codigo') 
                    cantidad = detalle_ingreso_form.cleaned_data.get('cantidad')
                    precio = detalle_ingreso_form.cleaned_data.get('precio')
                    valor = detalle_ingreso_form.cleaned_data.get('valor')
                    if cantidad and precio and valor:
                        try:
                            detalle_orden_compra = DetalleOrdenCompra.objects.get(pk=orden_compra)
                            detalle_movimiento = DetalleMovimiento(detalle_orden_compra=detalle_orden_compra,
                                                                   nro_detalle=cont,
                                                                   movimiento=self.object,
                                                                   producto=Producto.objects.get(pk=codigo),
                                                                   cantidad=cantidad,
                                                                   precio=precio,
                                                                   valor = valor)
                        except:
                            detalle_movimiento = DetalleMovimiento(nro_detalle=cont,
                                                                   movimiento=self.object,
                                                                   producto=Producto.objects.get(pk=codigo),
                                                                   cantidad=cantidad,
                                                                   precio=precio,
                                                                   valor = valor)
                        detalles.append(detalle_movimiento)                        
                        cont = cont + 1
                DetalleMovimiento.objects.bulk_create(detalles,referencia) 
                return HttpResponseRedirect(reverse('almacen:detalle_movimiento', args=[self.object.id_movimiento]))
        except IntegrityError:
                messages.error(self.request, 'Error guardando la cotizacion.')
        
    def form_invalid(self, form, detalle_ingreso_formset):
        print detalle_ingreso_formset
        return self.render_to_response(self.get_context_data(form=form))
        
class RegistrarSalidaAlmacen(CreateView):
    form_class = MovimientoForm
    template_name = "almacen/salida_almacen.html"
    model = Movimiento
    
    def get_form_kwargs(self):
        kwargs = super(RegistrarSalidaAlmacen, self).get_form_kwargs()
        kwargs['tipo_movimiento'] = 'S'
        return kwargs
    
    def get_initial(self):
        initial = super(RegistrarSalidaAlmacen, self).get_initial()
        initial['total'] = 0        
        return initial
    
    def get(self, request, *args, **kwargs):
        self.object = None
        tipos_salida = TipoMovimiento.objects.filter(incrementa=False)
        if not tipos_salida:
            return HttpResponseRedirect(reverse('almacen:crear_tipo_movimiento'))    
        almacenes = Almacen.objects.filter()  
        if not almacenes:
            return HttpResponseRedirect(reverse('almacen:crear_almacen'))      
        else:
            form_class = self.get_form_class()
            form = self.get_form(form_class)
            detalle_salida_formset=DetalleSalidaFormSet()
            return self.render_to_response(self.get_context_data(form=form,
                                                                 detalle_salida_formset=detalle_salida_formset))
    
    def post(self, request, *args, **kwargs):                      
        self.object = None
        form_class = self.get_form_class()
        form = self.get_form(form_class)
        detalle_salida_formset = DetalleSalidaFormSet(request.POST)
        if form.is_valid() and detalle_salida_formset.is_valid():
            return self.form_valid(form, detalle_salida_formset)
        else:
            return self.form_invalid(form, detalle_salida_formset)
    
    def form_valid(self, form, detalle_salida_formset):
        try:
            with transaction.atomic():
                self.object = form.save()
                referencia = self.object.referencia
                detalles = []
                cont = 1                
                for detalle_salida_form in detalle_salida_formset:
                    codigo = detalle_salida_form.cleaned_data.get('codigo') 
                    cantidad = detalle_salida_form.cleaned_data.get('cantidad')
                    precio = detalle_salida_form.cleaned_data.get('precio')
                    valor = detalle_salida_form.cleaned_data.get('valor')
                    if cantidad and precio and valor:
                        detalle_movimiento = DetalleMovimiento(nro_detalle=cont,
                                                               movimiento=self.object,
                                                               producto=Producto.objects.get(pk=codigo),
                                                               cantidad=cantidad,
                                                               precio=precio,
                                                               valor = valor) 
                        detalles.append(detalle_movimiento)                        
                        cont = cont + 1
                DetalleMovimiento.objects.bulk_create(detalles, referencia) 
                return HttpResponseRedirect(reverse('almacen:detalle_movimiento', args=[self.object.id_movimiento]))
        except IntegrityError:
                messages.error(self.request, 'Error guardando la cotizacion.')
        
    def form_invalid(self, form, detalle_salida_formset):
        return self.render_to_response(self.get_context_data(form=form,
                                                             detalle_salida_formset = detalle_salida_formset))
    
class ReporteExcelAlmacenes(TemplateView):
    
    def get(self, request, *args, **kwargs):
        almacenes = Almacen.objects.filter(estado=True).order_by('codigo')
        wb = Workbook()
        ws = wb.active
        ws['B1'] = 'REPORTE DE ALMACENES'
        ws.merge_cells('B1:J1')
        ws['B3'] = 'CODIGO'
        ws['C3'] = 'DESCRIPCIÓN'
        cont=4
        for almacen in almacenes:
            ws.cell(row=cont,column=2).value = almacen.codigo
            ws.cell(row=cont,column=3).value = almacen.descripcion
            cont = cont + 1
        nombre_archivo ="ListadoAlmacenes.xlsx" 
        response = HttpResponse(content_type="application/ms-excel") 
        contenido = "attachment; filename={0}".format(nombre_archivo)
        response["Content-Disposition"] = contenido
        wb.save(response)
        return response
    
class ReporteExcelTiposMovimientos(TemplateView):
    
    def get(self, request, *args, **kwargs):
        tipos = TipoMovimiento.objects.filter(estado=True).order_by('codigo')
        wb = Workbook()
        ws = wb.active
        ws['B1'] = 'REPORTE DE TIPOS DE MOVIMIENTOS'
        ws.merge_cells('B1:J1')
        ws['B3'] = 'CODIGO'
        ws['C3'] = 'DESCRIPCIÓN'
        cont=4
        for tipo in tipos:
            ws.cell(row=cont,column=2).value = tipo.codigo
            ws.cell(row=cont,column=3).value = tipo.descripcion
            cont = cont + 1
        nombre_archivo ="MaestroTiposMovimientos.xlsx" 
        response = HttpResponse(content_type="application/ms-excel") 
        contenido = "attachment; filename={0}".format(nombre_archivo)
        response["Content-Disposition"] = contenido
        wb.save(response)
        return response

class ReporteExcelKardexProducto(FormView):
    template_name = 'almacen/reporte_kardex_producto.html'
    form_class = FormularioKardexProducto
    
    def obtener_mes_anterior(self,mes,anio):
        if(mes<1):
            mes = 12
            anio = int(anio) - 1
        else:
            mes = int(mes) - 1
        return mes,anio

    def post(self, request, *args, **kwargs):
        cod_prod = request.POST['cod_producto']
        producto = Producto.objects.get(codigo=cod_prod)
        mes = request.POST['meses']
        anio = request.POST['anios']
        almacen = request.POST['almacenes']
        wb = Workbook()
        ws = wb.active
        ws['B1'] = u'Almacén: '+ almacen
        ws['E1'] = 'Periodo: '+ mes+'-'+ anio        
        ws['B3'] = 'FECHA'
        ws['C3'] = 'NRO_DOC'
        ws['D3']= 'TIPO_MOV'
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
        ws.cell(row=cont,column=2).value = 'Codigo: '+ producto.codigo
        ws.cell(row=cont,column=4).value = u" Denominación: " + producto.descripcion
        ws.cell(row=cont,column=11).value = " Unidad: " + producto.unidad_medida.descripcion
        cont = cont + 1
        mes_ant, anio_ant = self.obtener_mes_anterior(mes, anio)
        listado_kardex_ant = Kardex.objects.filter(almacen__codigo =  almacen,fecha_operacion__year=anio_ant,fecha_operacion__month=mes_ant,producto=producto.codigo).order_by('producto__descripcion','fecha_operacion','cantidad_salida','created')
        if len(listado_kardex_ant)>0:
            c_s_i = listado_kardex_ant.aggregate(Sum('cantidad_total'))
            cant_saldo_inicial=c_s_i['cantidad_total__sum']
            v_s_i = listado_kardex_ant.aggregate(Sum('valor_total'))
            valor_saldo_inicial=v_s_i['valor_total__sum']
        else:
            cant_saldo_inicial = 0
            valor_saldo_inicial = 0
        ws.cell(row=cont,column=8).value = "SALDO INICIAL:"
        ws.cell(row=cont,column=10).value = "Cantidad: "
        ws.cell(row=cont,column=11).value = cant_saldo_inicial
        ws.cell(row=cont,column=11).number_format = '#.00000'
        ws.cell(row=cont,column=12).value = "Valor: "
        ws.cell(row=cont,column=13).value = valor_saldo_inicial
        ws.cell(row=cont,column=13).number_format = '#.00000'
        cont = cont + 1
        listado_kardex = Kardex.objects.filter(almacen__codigo =  almacen,fecha_operacion__year=anio,fecha_operacion__month=mes,producto=producto.codigo).order_by('producto__descripcion','fecha_operacion','cantidad_salida','created')
        if len(listado_kardex)>0:
            cantidad_ingreso = listado_kardex.aggregate(Sum('cantidad_ingreso'))
            cantidad_salida = listado_kardex.aggregate(Sum('cantidad_salida'))
            cantidad_total = listado_kardex.aggregate(Sum('cantidad_total'))
            valor_ingreso = listado_kardex.aggregate(Sum('valor_ingreso'))
            valor_salida = listado_kardex.aggregate(Sum('valor_salida'))
            valor_total = listado_kardex.aggregate(Sum('valor_total'))
            t_cantidad_i = cantidad_ingreso['cantidad_ingreso__sum']
            t_cantidad_s= cantidad_salida['cantidad_salida__sum']
            t_cantidad_t= cantidad_total['cantidad_total__sum']
            t_valor_i= valor_ingreso['valor_ingreso__sum']
            t_valor_s= valor_salida['valor_salida__sum']
            t_valor_t= valor_total['valor_total__sum']
            for kardex in listado_kardex:
                ws.cell(row=cont,column=2).value = kardex.fecha_operacion
                ws.cell(row=cont,column=2).number_format = 'dd/mm/yyyy'
                ws.cell(row=cont,column=3).value = kardex.movimiento.id_movimiento
                ws.cell(row=cont,column=4).value = kardex.movimiento.tipo_movimiento.codigo
                ws.cell(row=cont,column=5).value = kardex.cantidad_ingreso
                ws.cell(row=cont,column=6).value = kardex.precio_ingreso
                ws.cell(row=cont,column=6).number_format = '#.00000'
                ws.cell(row=cont,column=7).value = kardex.valor_ingreso
                ws.cell(row=cont,column=7).number_format = '#.00000'
                ws.cell(row=cont,column=8).value = kardex.cantidad_salida
                ws.cell(row=cont,column=9).value = kardex.precio_salida
                ws.cell(row=cont,column=9).number_format = '#.00000'
                ws.cell(row=cont,column=10).value = kardex.valor_salida
                ws.cell(row=cont,column=10).number_format = '#.00000'
                ws.cell(row=cont,column=11).value = kardex.cantidad_total
                ws.cell(row=cont,column=12).value = kardex.precio_total
                ws.cell(row=cont,column=12).number_format = '#.00000'
                ws.cell(row=cont,column=13).value = kardex.valor_total
                ws.cell(row=cont,column=13).number_format = '#.00000'
                cont = cont + 1
            ws.cell(row=cont,column=5).value = t_cantidad_i
            ws.cell(row=cont,column=7).value = t_valor_i
            ws.cell(row=cont,column=7).number_format = '#.00000'
            ws.cell(row=cont,column=8).value = t_cantidad_s
            ws.cell(row=cont,column=10).value = t_valor_s
            ws.cell(row=cont,column=10).number_format = '#.00000'
            ws.cell(row=cont,column=11).value = t_cantidad_t
            ws.cell(row=cont,column=13).value = t_valor_t
            ws.cell(row=cont,column=13).number_format = '#.00000'
            cont = cont + 2
        else:
            ws.cell(row=cont,column=5).value = 0
            ws.cell(row=cont,column=6).value = 0
            ws.cell(row=cont,column=6).number_format = '#.00000'
            ws.cell(row=cont,column=7).value = 0
            ws.cell(row=cont,column=7).number_format = '#.00000'
            ws.cell(row=cont,column=8).value = 0
            ws.cell(row=cont,column=9).value = 0
            ws.cell(row=cont,column=9).number_format = '#.00000'
            ws.cell(row=cont,column=10).value = 0
            ws.cell(row=cont,column=10).number_format = '#.00000'
            ws.cell(row=cont,column=11).value = 0
            ws.cell(row=cont,column=12).value = 0
            ws.cell(row=cont,column=12).number_format = '#.00000'
            ws.cell(row=cont,column=13).value = 0
            ws.cell(row=cont,column=13).number_format = '#.00000'
            cont = cont + 1
            ws.cell(row=cont,column=5).value = 0
            ws.cell(row=cont,column=7).value = 0
            ws.cell(row=cont,column=7).number_format = '#.00000'
            ws.cell(row=cont,column=8).value = 0
            ws.cell(row=cont,column=10).value = 0
            ws.cell(row=cont,column=10).number_format = '#.00000'
            ws.cell(row=cont,column=11).value = cant_saldo_inicial
            ws.cell(row=cont,column=13).value = valor_saldo_inicial
            ws.cell(row=cont,column=13).number_format = '#.00000' 
            cont = cont + 2
        nombre_archivo ="ReporteExcelKardexProducto.xlsx" 
        response = HttpResponse(content_type="application/ms-excel") 
        contenido = "attachment; filename={0}".format(nombre_archivo)
        response["Content-Disposition"] = contenido
        wb.save(response)
        return response
    
class ReporteExcelKardex(FormView):
    template_name = 'almacen/reporte_kardex.html'
    form_class = FormularioKardexProducto

    def obtener_mes_anterior(self,mes,anio):
        if(mes<1):
            mes = 12
            anio = int(anio) - 1
        else:
            mes = int(mes) - 1
        return mes,anio

    def post(self, request, *args, **kwargs):
        mes = request.POST['meses']
        anio = request.POST['anios']
        almacen = request.POST['almacenes']
        productos = Kardex.objects.filter(almacen__codigo=almacen).order_by('producto').distinct('producto__codigo')
        wb = Workbook()
        ws = wb.active
        ws['B1'] = u'Almacén: '+ almacen
        ws['E1'] = 'Periodo: '+ mes+'-'+ anio
        ws['B3'] = 'FECHA'
        ws['C3'] = 'NRO_DOC'
        ws['D3']= 'TIPO_MOV'
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
        for prod in productos:
            producto = prod.producto
            ws.cell(row=cont,column=2).value = 'Codigo: '+ producto.codigo
            ws.cell(row=cont,column=4).value = u" Denominación: " + producto.descripcion
            ws.cell(row=cont,column=11).value = " Unidad: " + producto.unidad_medida.descripcion
            cont = cont + 1
            mes_ant, anio_ant = self.obtener_mes_anterior(mes, anio)
            listado_kardex_ant = Kardex.objects.filter(almacen__codigo =  almacen,fecha_operacion__year=anio_ant,fecha_operacion__month=mes_ant,producto=producto.codigo).order_by('producto__descripcion','fecha_operacion','cantidad_salida','created')
            if len(listado_kardex_ant)>0:
                c_s_i = listado_kardex_ant.aggregate(Sum('cantidad_total'))
                cant_saldo_inicial=c_s_i['cantidad_total__sum']
                v_s_i = listado_kardex_ant.aggregate(Sum('valor_total'))
                valor_saldo_inicial=v_s_i['valor_total__sum']
            else:
                cant_saldo_inicial = 0
                valor_saldo_inicial = 0
            ws.cell(row=cont,column=8).value = "SALDO INICIAL:"
            ws.cell(row=cont,column=10).value = "Cantidad: "
            ws.cell(row=cont,column=11).value = cant_saldo_inicial
            ws.cell(row=cont,column=11).number_format = '#.00000'
            ws.cell(row=cont,column=12).value = "Valor: "
            ws.cell(row=cont,column=13).value = valor_saldo_inicial
            ws.cell(row=cont,column=13).number_format = '#.00000'
            cont = cont + 1
            listado_kardex = Kardex.objects.filter(almacen__codigo =  almacen,fecha_operacion__year=anio,fecha_operacion__month=mes,producto=producto.codigo).order_by('producto__descripcion','fecha_operacion','cantidad_salida','created')
            if len(listado_kardex)>0:
                cantidad_ingreso = listado_kardex.aggregate(Sum('cantidad_ingreso'))
                cantidad_salida = listado_kardex.aggregate(Sum('cantidad_salida'))
                cantidad_total = listado_kardex.aggregate(Sum('cantidad_total'))
                valor_ingreso = listado_kardex.aggregate(Sum('valor_ingreso'))
                valor_salida = listado_kardex.aggregate(Sum('valor_salida'))
                valor_total = listado_kardex.aggregate(Sum('valor_total'))
                t_cantidad_i = cantidad_ingreso['cantidad_ingreso__sum']
                t_cantidad_s= cantidad_salida['cantidad_salida__sum']
                t_cantidad_t= cantidad_total['cantidad_total__sum']
                t_valor_i= valor_ingreso['valor_ingreso__sum']
                t_valor_s= valor_salida['valor_salida__sum']
                t_valor_t= valor_total['valor_total__sum']
                for kardex in listado_kardex:
                    ws.cell(row=cont,column=2).value = kardex.fecha_operacion
                    ws.cell(row=cont,column=2).number_format = 'dd/mm/yyyy'
                    ws.cell(row=cont,column=3).value = kardex.movimiento.id_movimiento
                    ws.cell(row=cont,column=4).value = kardex.movimiento.tipo_movimiento.codigo
                    ws.cell(row=cont,column=5).value = kardex.cantidad_ingreso
                    ws.cell(row=cont,column=6).value = kardex.precio_ingreso
                    ws.cell(row=cont,column=6).number_format = '#.00000'
                    ws.cell(row=cont,column=7).value = kardex.valor_ingreso
                    ws.cell(row=cont,column=7).number_format = '#.00000'
                    ws.cell(row=cont,column=8).value = kardex.cantidad_salida
                    ws.cell(row=cont,column=9).value = kardex.precio_salida
                    ws.cell(row=cont,column=9).number_format = '#.00000'
                    ws.cell(row=cont,column=10).value = kardex.valor_salida
                    ws.cell(row=cont,column=10).number_format = '#.00000'
                    ws.cell(row=cont,column=11).value = kardex.cantidad_total
                    ws.cell(row=cont,column=12).value = kardex.precio_total
                    ws.cell(row=cont,column=12).number_format = '#.00000'
                    ws.cell(row=cont,column=13).value = kardex.valor_total
                    ws.cell(row=cont,column=13).number_format = '#.00000'
                    cont = cont + 1
                ws.cell(row=cont,column=5).value = t_cantidad_i
                ws.cell(row=cont,column=7).value = t_valor_i
                ws.cell(row=cont,column=7).number_format = '#.00000'
                ws.cell(row=cont,column=8).value = t_cantidad_s
                ws.cell(row=cont,column=10).value = t_valor_s
                ws.cell(row=cont,column=10).number_format = '#.00000'
                ws.cell(row=cont,column=11).value = t_cantidad_t
                ws.cell(row=cont,column=13).value = t_valor_t
                ws.cell(row=cont,column=13).number_format = '#.00000'
                cont = cont + 2
            else:
                ws.cell(row=cont,column=5).value = 0
                ws.cell(row=cont,column=6).value = 0
                ws.cell(row=cont,column=6).number_format = '#.00000'
                ws.cell(row=cont,column=7).value = 0
                ws.cell(row=cont,column=7).number_format = '#.00000'
                ws.cell(row=cont,column=8).value = 0
                ws.cell(row=cont,column=9).value = 0
                ws.cell(row=cont,column=9).number_format = '#.00000'
                ws.cell(row=cont,column=10).value = 0
                ws.cell(row=cont,column=10).number_format = '#.00000'
                ws.cell(row=cont,column=11).value = 0
                ws.cell(row=cont,column=12).value = 0
                ws.cell(row=cont,column=12).number_format = '#.00000'
                ws.cell(row=cont,column=13).value = 0
                ws.cell(row=cont,column=13).number_format = '#.00000'
                cont = cont + 1
                ws.cell(row=cont,column=5).value = 0
                ws.cell(row=cont,column=7).value = 0
                ws.cell(row=cont,column=7).number_format = '#.00000'
                ws.cell(row=cont,column=8).value = 0
                ws.cell(row=cont,column=10).value = 0
                ws.cell(row=cont,column=10).number_format = '#.00000'
                ws.cell(row=cont,column=11).value = cant_saldo_inicial
                ws.cell(row=cont,column=13).value = valor_saldo_inicial
                ws.cell(row=cont,column=13).number_format = '#.00000' 
                cont = cont + 2
        nombre_archivo ="ReporteExcelKardex.xlsx" 
        response = HttpResponse(content_type="application/ms-excel") 
        contenido = "attachment; filename={0}".format(nombre_archivo)
        response["Content-Disposition"] = contenido
        wb.save(response)
        return response

class ReporteStock(FormView):
    template_name = 'almacen/reporte_stock.html'
    form_class = FormularioReporteStock
    
    def post(self, request, *args, **kwargs):
        r_almacen = request.POST['almacenes']
        return HttpResponseRedirect(reverse('almacen:reporte_excel_stock',args=[r_almacen]))
    
class ReporteExcelStock(TemplateView):
        
    def get(self, request, *args, **kwargs):
        codigo_almacen = kwargs['pk']
        almacen = Almacen.objects.get(codigo=codigo_almacen)
        control_productos = ControlProductoAlmacen.objects.filter(almacen = almacen).order_by('producto')
        wb = Workbook()
        ws = wb.active
        ws['B1'] = 'Almacen: '+ almacen.descripcion
        ws.merge_cells('B1:E1')
        ws['B3'] = 'CODIGO'
        ws['C3'] = 'DESCRIPCION'
        ws['D3'] = 'UNIDAD'
        ws['E3']= 'CANTIDAD'        
        cont = 4
        for control in control_productos:
            ws.cell(row=cont,column=2).value = control.producto.codigo
            ws.cell(row=cont,column=3).value = control.producto.descripcion
            ws.cell(row=cont,column=4).value = control.producto.unidad_medida.codigo
            ws.cell(row=cont,column=5).value = control.stock
            cont = cont + 1
        nombre_archivo ="ReporteStock.xlsx" 
        response = HttpResponse(content_type="application/ms-excel") 
        contenido = "attachment; filename={0}".format(nombre_archivo)
        response["Content-Disposition"] = contenido
        wb.save(response)
        return response

class ReporteExcelMovimientos(FormView):
    form_class = FormularioReporteMovimientos
    template_name = "reporte_movimientos.html"    

    def form_valid(self, form):
        data = form.cleaned_data
        tipo_busqueda = data['tipo_busqueda']
        p_almacen = data['almacenes']
        p_tipo_movimiento = data['tipos_movimiento']
        almacen = Almacen.objects.get(codigo=p_almacen)
        tipo_movimiento = TipoMovimiento.objects.get(codigo=p_tipo_movimiento)
        wb = Workbook()
        ws = wb.active
        if tipo_busqueda=='F':
            p_fecha_inicio = data['fecha_inicio']
            p_fecha_final = data['fecha_fin']
            anio = int(p_fecha_inicio[6:])        
            mes = int(p_fecha_inicio[3:5])
            dia = int(p_fecha_inicio[0:2])
            fecha_inicio = datetime.datetime(anio,mes,dia,23,59,59)
            anio = int(p_fecha_final[6:])        
            mes = int(p_fecha_final[3:5])
            dia = int(p_fecha_final[0:2])
            fecha_final = datetime.datetime(anio,mes,dia,23,59,59)            
            ws['B1'] = 'REPORTE DE MOVIMIENTOS POR FECHA'
            ws.merge_cells('B1:H1')
            ws['B2'] = 'ALMACEN: '+ almacen.descripcion
            ws.merge_cells('B2:D2')
            ws['E2'] = 'TIPO DE MOVIMIENTO: '+ tipo_movimiento.descripcion
            ws.merge_cells('E2:H2')
            ws['B3'] = 'DESDE'
            ws['C3'] = p_fecha_inicio
            ws['C3'].number_format = 'dd/mm/yyyy'
            ws['D3'] = 'HASTA'
            ws['E3'] = p_fecha_final
            ws['F3'].number_format = 'dd/mm/yyyy'        
            movimientos = Movimiento.objects.filter(fecha_operacion__range=[fecha_inicio, fecha_final],tipo_movimiento=tipo_movimiento,almacen=almacen)                                    
        elif tipo_busqueda=='M':
            mes = data['mes'].strip()
            annio = data['annio'].strip()            
            ws['B1'] = 'REPORTE DE MOVIMIENTOS POR MES'
            ws.merge_cells('B1:H1')
            ws['B2'] = 'ALMACEN: '+ almacen.descripcion
            ws.merge_cells('B2:D2')
            ws['E2'] = 'TIPO DE MOVIMIENTO: '+ tipo_movimiento.descripcion
            ws.merge_cells('E2:H2')
            ws['B3'] = 'MES'
            ws['C3'] = mes
            ws['D3'] = 'AÑO'
            ws['E3'] = annio                    
            movimientos = Movimiento.objects.filter(fecha_operacion__month=mes,fecha_operacion__year=annio,tipo_movimiento=tipo_movimiento,almacen=almacen)
        elif tipo_busqueda=='A':
            annio = data['annio'].strip()
            ws['B1'] = 'REPORTE DE MOVIMIENTOS POR AÑO'
            ws.merge_cells('B1:H1')
            ws['B2'] = 'ALMACEN: '+ almacen.descripcion
            ws.merge_cells('B2:D2')
            ws['E2'] = 'TIPO DE MOVIMIENTO: '+ tipo_movimiento.descripcion
            ws.merge_cells('E2:H2')
            ws['B3'] = 'AÑO'
            ws['C3'] = annio
            movimientos = Movimiento.objects.filter(fecha_operacion__year=annio,tipo_movimiento=tipo_movimiento,almacen=almacen)
        ws['B5'] = 'ID_MOVIMIENTO'
        ws['C5'] = 'TIPO_DOCUMENTO'
        ws['D5'] = 'SERIE'
        ws['E5'] = 'NUMERO'
        ws['F5'] = 'FECHA_OPERACION'
        ws['G5'] = 'OBSERVACION'
        ws['H5'] = 'FECHA_CREACION'
        cont=6
        for movimiento in movimientos:
            ws.cell(row=cont,column=2).value = movimiento.id_movimiento
            ws.cell(row=cont,column=3).value = movimiento.tipo_documento
            ws.cell(row=cont,column=4).value = movimiento.serie
            ws.cell(row=cont,column=5).value = movimiento.numero
            ws.cell(row=cont,column=6).value = movimiento.fecha_operacion
            ws.cell(row=cont,column=6).number_format = 'dd/mm/yyyy hh:mm:ss'
            ws.cell(row=cont,column=7).value = movimiento.observacion
            ws.cell(row=cont,column=8).value = movimiento.created    
            ws.cell(row=cont,column=8).number_format = 'dd/mm/yyyy hh:mm:ss'        
            cont = cont + 1
        nombre_archivo ="ReporteMovimientosPorFecha.xlsx" 
        response = HttpResponse(content_type="application/ms-excel") 
        contenido = "attachment; filename={0}".format(nombre_archivo)
        response["Content-Disposition"] = contenido
        wb.save(response)
        return response
        
class ReporteExcelMovimientosPorFecha(View):
    
    def get(self, request, *args, **kwargs):
        p_fecha_inicio = kwargs['fecha_inicio']
        p_fecha_final = kwargs['fecha_fin']
        p_almacen = kwargs['almacen']
        p_tipo_movimiento = kwargs['tipo_movimiento']
        anio = int(p_fecha_inicio[6:])        
        mes = int(p_fecha_inicio[3:5])
        dia = int(p_fecha_inicio[0:2])
        fecha_inicio = datetime.datetime(anio,mes,dia,23,59,59)
        anio = int(p_fecha_final[6:])        
        mes = int(p_fecha_final[3:5])
        dia = int(p_fecha_final[0:2])
        fecha_final = datetime.datetime(anio,mes,dia,23,59,59)
        almacen = Almacen.objects.get(codigo=p_almacen)
        tipo_movimiento = TipoMovimiento.objects.get(codigo=p_tipo_movimiento)
        wb = Workbook()
        ws = wb.active
        ws['B1'] = 'REPORTE DE MOVIMIENTOS POR FECHA'
        ws.merge_cells('B1:H1')
        ws['B2'] = 'ALMACEN: '+ almacen.descripcion
        ws.merge_cells('B2:D2')
        ws['E2'] = 'TIPO DE MOVIMIENTO: '+ tipo_movimiento.descripcion
        ws.merge_cells('E2:H2')
        ws['B3'] = 'DESDE'
        ws['C3'] = p_fecha_inicio
        ws['C3'].number_format = 'dd/mm/yyyy'
        ws['D3'] = 'HASTA'
        ws['E3'] = p_fecha_final
        ws['F3'].number_format = 'dd/mm/yyyy'        
        movimientos = Movimiento.objects.filter(fecha_operacion__range=[fecha_inicio, fecha_final],tipo_movimiento=tipo_movimiento,almacen=almacen)
        ws['B5'] = 'ID_MOVIMIENTO'
        ws['C5'] = 'TIPO_DOCUMENTO'
        ws['D5'] = 'SERIE'
        ws['E5'] = 'NUMERO'
        ws['F5'] = 'FECHA_OPERACION'
        ws['G5'] = 'OBSERVACION'
        ws['H5'] = 'FECHA_CREACION'
        cont=6
        for movimiento in movimientos:
            ws.cell(row=cont,column=2).value = movimiento.id_movimiento
            ws.cell(row=cont,column=3).value = movimiento.tipo_documento
            ws.cell(row=cont,column=4).value = movimiento.serie
            ws.cell(row=cont,column=5).value = movimiento.numero
            ws.cell(row=cont,column=6).value = movimiento.fecha_operacion
            ws.cell(row=cont,column=6).number_format = 'dd/mm/yyyy hh:mm:ss'
            ws.cell(row=cont,column=7).value = movimiento.observacion
            ws.cell(row=cont,column=8).value = movimiento.created    
            ws.cell(row=cont,column=8).number_format = 'dd/mm/yyyy hh:mm:ss'        
            cont = cont + 1
        nombre_archivo ="ReporteMovimientosPorFecha.xlsx" 
        response = HttpResponse(content_type="application/ms-excel") 
        contenido = "attachment; filename={0}".format(nombre_archivo)
        response["Content-Disposition"] = contenido
        wb.save(response)
        return response
    
class ReportePDFMovimiento(View):
    
    def cabecera(self,pdf,movimiento,y):
        archivo_imagen = os.path.join(settings.MEDIA_ROOT,str(empresa.logo))
        pdf.drawImage(archivo_imagen, 40, y-50, 120, 90,preserveAspectRatio=True)  
        pdf.setFont("Times-Roman", 14)
        if movimiento.tipo_movimiento.incrementa:
            pdf.drawString(220, y, u"NOTA DE INGRESO N°")
        else:
            pdf.drawString(220, y, u"NOTA DE SALIDA N°")
        pdf.setFont("Times-Roman", 13)
        pdf.drawString(250, y-20, movimiento.id_movimiento)
        pdf.setFont("Times-Roman", 10)
        pdf.drawString(420, y-20, "FECHA: "+movimiento.fecha_operacion.strftime('%d/%m/%y'))
        pdf.setFont("Times-Roman", 10)
        try:
            if movimiento.referencia.cotizacion is not None:
                pdf.drawString(40, y-50, u"PROVEEDOR: "+movimiento.referencia.cotizacion.proveedor.razon_social)
            else:
                pdf.drawString(40, y-50, u"PROVEEDOR: "+movimiento.referencia.proveedor.razon_social)
            y = y - 70
        except:
            y = y - 50
        pdf.drawString(40, y, u"OPERACIÓN: "+movimiento.tipo_movimiento.descripcion)
        pdf.drawString(40, y-20, u"ALMACÉN: "+movimiento.almacen.codigo+"-"+movimiento.almacen.descripcion)
        try:
            pdf.drawString(40, y-40, u"ORDEN DE COMPRA: "+movimiento.referencia.codigo)
            y = y - 60
        except:
            y = y - 40
        return y            
    
    def cuadro_total(self,pdf,y,movimiento):
        pdf.drawString(445, y-15, u"TOTAL: ")
        total = [[str(movimiento.total)]]
        tabla_total = Table(total,colWidths=[2.5 * cm])
        tabla_total.setStyle(TableStyle(
            [
                ('GRID', (0, 0), (0, 2), 1, colors.black),
                ('FONTSIZE', (0, 0), (-1, -1), 8),
                ('ALIGN',(0,0),(-1,-1),'RIGHT'),
            ]
        ))
        tabla_total.wrapOn(pdf, 800, 600)
        y = y - 20
        tabla_total.drawOn(pdf, 494,y)
        return y
    
    def cuadro_observaciones(self,pdf,y,movimiento):
        p = ParagraphStyle('parrafos')
        p.alignment = TA_JUSTIFY 
        p.fontSize = 10
        p.fontName="Times-Roman"
        obs=Paragraph("Observaciones: "+movimiento.observaciones,p)
        observaciones = [[obs]]
        tabla_observaciones = Table(observaciones,colWidths=[18.50 * cm], rowHeights=1.8 * cm)
        tabla_observaciones.setStyle(TableStyle(
            [
                ('GRID', (0, 0), (0, 2), 1, colors.black),
                ('FONTSIZE', (0, 0), (-1, -1), 8),
                ('ALIGN',(0,0),(-1,-1),'LEFT'),
                ('VALIGN',(0,0),(-1,-1),'TOP'),
            ]
        ))
        tabla_observaciones.wrapOn(pdf, 800, 600)
        y = y - 60
        tabla_observaciones.drawOn(pdf, 40,y)
        if y<=80:
            pdf.setFont("Times-Roman", 8)
            pdf.drawString(210, 20,"DIRECCION")
            pdf.showPage()            
            y=800
        return y  
            
    def detalle(self,pdf,y,movimiento):
        encabezados = ('Item', 'Cantidad', 'Unidad', u'Descripción','Precio','Total')
        detalles = [(detalle.nro_detalle, detalle.cantidad, detalle.producto.unidad_medida.codigo, detalle.producto.descripcion, detalle.precio,detalle.valor) for detalle in DetalleMovimiento.objects.filter(movimiento=movimiento)]
        size = 30
        listas = [detalles[i:i+size] for i  in range(0, len(detalles), size)]
        cant_listas = len(listas)
        cont_listas = 0
        if cant_listas==1:
            y = y - 20*len(listas[0])
        else:
            y = y - 550
        for lista in listas:
            cont_listas = cont_listas + 1
            detalle_orden = Table([encabezados] + lista,colWidths=[1.5 * cm, 2.5 * cm, 1.5 * cm,8.5* cm, 2 * cm, 2.5 * cm])
            detalle_orden.setStyle(TableStyle(
                [
                    ('GRID', (0, 0), (-1, -1), 1, colors.black), 
                    ('FONTSIZE', (0, 0), (-1, -1), 8),  
                    ('ALIGN',(4,0),(-1,-1),'RIGHT'),           
                ]
            ))
            detalle_orden.wrapOn(pdf, 800, 600)
            detalle_orden.drawOn(pdf, 40,y)            
            if not len(lista)<30:
                if cont_listas < cant_listas:
                    pdf.setFont("Times-Roman", 8)
                    pdf.drawString(210, 20,"DIRECCION")
                    pdf.showPage()
                    y = 640
        return y
    
    def firmas(self,y,pdf):
        configuracion = Configuracion.objects.first()
        oficina_administracion = configuracion.administracion
        presupuesto = configuracion.presupuesto
        logistica = configuracion.logistica
        pdf.line(70, y-80, 200, y-80)
        pdf.line(390, y-80, 520, y-80)
        pdf.setFont("Times-Roman", 8)
        pdf.drawString(73, y-90,oficina_administracion.nombre)
        pdf.drawString(415, y-90,logistica.nombre)
    
    def get(self, request, *args, **kwargs):         
        id_movimiento = kwargs['id_movimiento']
        movimiento = Movimiento.objects.get(id_movimiento=id_movimiento)        
        response = HttpResponse(content_type='application/pdf')
        #response['Content-Disposition'] = 'attachment; filename="resume.pdf"'
        buffer = BytesIO()
        pdf = canvas.Canvas(buffer)  
        y=800
        y=self.cabecera(pdf, movimiento, y)
        y=self.detalle(pdf, y, movimiento)
        y=self.cuadro_total(pdf, y, movimiento)
        y=self.cuadro_observaciones(pdf, y, movimiento)
        self.firmas(y, pdf)
        pdf.drawString(210, 20,empresa.direccion())            
        pdf.save()
        pdf = buffer.getvalue()
        buffer.close()
        response.write(pdf)
        return response

class ReportePDFProductos(View):    
    
    def get(self, request, *args, **kwargs): 
        response = HttpResponse(content_type='application/pdf')
        pdf_name = "clientes.pdf"  # llamado clientes
        # la linea 26 es por si deseas descargar el pdf a tu computadora
        # response['Content-Disposition'] = 'attachment; filename=%s' % pdf_name
        buff = BytesIO()
        doc = SimpleDocTemplate(buff,
                                pagesize=letter,
                                rightMargin=40,
                                leftMargin=40,
                                topMargin=60,
                                bottomMargin=18,
                                )
        clientes = []
        styles = getSampleStyleSheet()
        header = Paragraph("Listado de Clientes", styles['Heading1'])
        clientes.append(header)
        headings = ('Nombre', 'Email', 'Edad', 'Direccion')
        allclientes = [(p.codigo, p.descripcion, p.precio_mercado, p.grupo_suministros) for p in Producto.objects.all()]
            
        t = Table([headings] + allclientes)
        t.setStyle(TableStyle(
            [
                ('GRID', (0, 0), (3, -1), 1, colors.dodgerblue),
                ('LINEBELOW', (0, 0), (-1, 0), 2, colors.darkblue),
                ('BACKGROUND', (0, 0), (-1, 0), colors.dodgerblue)
            ]
        ))
        clientes.append(t)
        doc.build(clientes)
        response.write(buff.getvalue())
        buff.close()
        return response

class PopupCrearTipoStock(FormView):
    template_name = 'almacen/popup_crear_tipo_stock.html'
    form_class = TipoStockForm
    success_url = reverse_lazy('almacen:crear_suministro')

    def form_valid(self, form):
        form.save()
        return super(PopupCrearTipoStock, self).form_valid(form)
    
class VerificarSolicitaDocumento(TemplateView):
    
    def get(self, request, *args, **kwargs):
        tipo = request.GET['tipo']
        tipo_movimiento = TipoMovimiento.objects.get(codigo=tipo)
        json_object = {'solicita_documento': tipo_movimiento.solicita_documento}
        return JsonResponse(json_object)
    
class VerificarPideReferencia(TemplateView):
    
    def get(self, request, *args, **kwargs):
        tipo = request.GET['tipo']
        tipo_movimiento = TipoMovimiento.objects.get(codigo=tipo)
        json_object = {'pide_refencia': tipo_movimiento.pide_referencia}
        return JsonResponse(json_object)
    
class VerificarStockParaPedido(TemplateView):
    
    def get(self, request, *args, **kwargs):
        almacen = request.GET['almacen']
        pedido = request.GET['pedido']
        detalles = DetallePedido.objects.filter(pedido__codigo = pedido, estado=DetallePedido.STATUS.PEND).order_by('nro_detalle')
        lista_detalles = []
        for detalle in detalles:
            try:
                control_producto = ControlProductoAlmacen.objects.get(almacen__codigo = almacen,producto__codigo = detalle.producto.codigo)
                stock = control_producto.stock
                precio = control_producto.precio
            except ControlProductoAlmacen.DoesNotExist:
                stock = 0
                precio = 0            
            if stock <> 0:                
                detalle_json = {}       
                detalle_json['codigo_detalle'] = detalle.id
                detalle_json['codigo_producto'] = detalle.producto.codigo                
                detalle_json['nombre_producto'] = detalle.producto.descripcion
                detalle_json['unidad_producto'] = detalle.producto.unidad_medida.descripcion
                cantidad = detalle.cantidad-detalle.cantidad_atendida
                if cantidad > stock:
                    cantidad = stock
                valor = cantidad * precio
                detalle_json['cantidad'] = str(cantidad) 
                detalle_json['precio'] = str(precio) 
                detalle_json['valor'] = str(valor)
                lista_detalles.append(detalle_json)
        data = json.dumps(lista_detalles)
        return HttpResponse(data, 'application/json')