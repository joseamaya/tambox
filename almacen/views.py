# -*- coding: utf-8 -*- 
from django.utils import timezone
from django.shortcuts import render

from almacen.models import Almacen, Movimiento, Kardex, TipoMovimiento, DetalleMovimiento, ControlProductoAlmacen, \
    Pedido, DetallePedido
from django.http import HttpResponse, HttpResponseRedirect
from django.urls import reverse, reverse_lazy
import datetime
from django.views.generic import TemplateView, FormView, View, ListView
from almacen.forms import AlmacenForm, TipoMovimientoForm, FormularioReporteMovimientos, \
    FormularioKardexProducto, CargarInventarioInicialForm, MovimientoForm, \
    DetalleIngresoFormSet, DetalleSalidaFormSet, PedidoForm, DetallePedidoFormSet, \
    AprobacionPedidoForm, FormularioReprocesoPrecio, \
    FormularioMovimientosProducto, FormularioConsultaStock, FormularioConsultaInventario
from decimal import Decimal, InvalidOperation
from io import BytesIO
from reportlab.platypus import SimpleDocTemplate, Paragraph, TableStyle
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.platypus import Table
from django.http import JsonResponse
from compras.models import DetalleOrdenCompra
from openpyxl import Workbook
import simplejson
import json
from django.views.generic.detail import DetailView
from django.views.generic.edit import UpdateView, CreateView
from administracion.models import Puesto
import locale
from contabilidad.models import TipoDocumento
from contabilidad.forms import UploadForm
from seguridad.permisos import requiere
from django.utils.decorators import method_decorator
from django.db.models import Q
from django.db import transaction, IntegrityError
from django.core.exceptions import ObjectDoesNotExist
from django.contrib import messages
from productos.models import Producto
from almacen.mail import correo_creacion_pedido
from almacen.reports import ReporteMovimiento, ReporteKardexPDF, ReporteKardexExcel, reporte_inventario
from tambox.configuracion import logistica
from tambox.vistas import CargarCsvMixin, SoloAjaxMixin
from datetime import date

locale.setlocale(locale.LC_ALL, "")


class Tablero(View):

    def get(self, request, *args, **kwargs):
        cod_mov_invent_ini = 'I00'
        cod_mov_ingreso_compra = 'I01'
        cod_mov_salida_pedido = 'S01'
        lista_notificaciones = []
        cant_almacenes = Almacen.objects.count()
        cant_tipos_movimientos_ingreso = TipoMovimiento.objects.filter(increases=True).exclude(
            code=cod_mov_invent_ini).count()
        cant_tipos_movimientos_salida = TipoMovimiento.objects.filter(increases=False).count()
        tipo_movimiento, creado = TipoMovimiento.objects.get_or_create(code=cod_mov_invent_ini,
                                                                       defaults={'description': 'INVENTARIO INICIAL',
                                                                                 'sunat_code': '16',
                                                                                 'increases': True,
                                                                                 'is_active': True})
        if creado:
            lista_notificaciones.append("Se ha creado el tipo de movimiento inventario inicial")
        tipo_movimiento, creado = TipoMovimiento.objects.get_or_create(code=cod_mov_ingreso_compra,
                                                                       defaults={'description': 'INGRESO POR COMPRA',
                                                                                 'sunat_code': '02',
                                                                                 'increases': True,
                                                                                 'requires_reference': True,
                                                                                 'is_active': True})
        if creado:
            lista_notificaciones.append("Se ha creado el tipo de movimiento Ingreso por Compra")
        tipo_movimiento, creado = TipoMovimiento.objects.get_or_create(code=cod_mov_salida_pedido,
                                                                       defaults={'description': 'SALIDA POR PEDIDO',
                                                                                 'sunat_code': '10',
                                                                                 'increases': False,
                                                                                 'requires_reference': True,
                                                                                 'is_active': True})
        inventario_inicial = Movimiento.objects.filter(tipo_movimiento__code=cod_mov_invent_ini).count()
        if creado:
            lista_notificaciones.append("Se ha creado el tipo de movimiento Salida por Pedido")
        if cant_almacenes == 0:
            lista_notificaciones.append("No se ha creado ningún almacen")
        if cant_tipos_movimientos_ingreso == 0:
            lista_notificaciones.append("No se ha creado ningún tipo de movimiento de ingreso")
        if cant_tipos_movimientos_salida == 0:
            lista_notificaciones.append("No se ha creado ningún tipo de movimiento de salida")
        if inventario_inicial == 0:
            lista_notificaciones.append("No se ha realizado el inventario inicial")
        context = {'notificaciones': lista_notificaciones}
        return render(request, 'almacen/tablero_almacen.html', context)


class AprobarPedido(CreateView):
    form_class = AprobacionPedidoForm
    template_name = 'almacen/aprobar_pedido.html'
    model = Movimiento

    @method_decorator(requiere('almacen.aprobar_pedido'))
    def dispatch(self, *args, **kwargs):
        self.code = kwargs['code']
        return super(AprobarPedido, self).dispatch(*args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super(AprobarPedido, self).get_form_kwargs()
        kwargs['request'] = self.request
        return kwargs

    def get_initial(self):
        initial = super(AprobarPedido, self).get_initial()
        initial['cod_pedido'] = self.code
        return initial

    def get_context_data(self, **kwargs):
        pedido = Pedido.objects.get(code=self.code)
        context = super(AprobarPedido, self).get_context_data(**kwargs)
        context['pedido'] = pedido
        return context

    def get(self, request, *args, **kwargs):
        self.object = None
        form_class = self.get_form_class()
        form = self.get_form(form_class)
        pedido = Pedido.objects.get(code=self.code)
        try:
            trabajador = self.request.user.worker
        except ObjectDoesNotExist:
            return HttpResponseRedirect(reverse('administracion:crear_trabajador'))
        try:
            puestos = trabajador.positions.all().filter(is_active=True)
            if trabajador.firma == '':
                return HttpResponseRedirect(reverse('administracion:modificar_trabajador'))
            if puestos[0].is_leadership and puestos[0].oficina == logistica():
                form_class = self.get_form_class()
                form = self.get_form(form_class)
                detalles = DetallePedido.objects.filter(pedido=pedido, status=DetallePedido.STATUS.PEND)
                detalles_data = []
                for detalle in detalles:
                    d = {'pedido': detalle.id,
                         'code': detalle.producto.code,
                         'name': detalle.producto.description,
                         'unidad': detalle.producto.unidad_medida.code,
                         'quantity': detalle.quantity
                         }
                    detalles_data.append(d)
                detalle_salida_formset = DetalleSalidaFormSet(initial=detalles_data)
                return self.render_to_response(self.get_context_data(form=form,
                                                                     detalle_salida_formset=detalle_salida_formset))
            else:
                return HttpResponseRedirect(reverse('seguridad:permiso_denegado'))
        except (IndexError, ObjectDoesNotExist):
            return HttpResponseRedirect(reverse('seguridad:permiso_denegado'))

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
                pedido = self.object.pedido
                detalles = []
                cont = 1
                for detalle_salida_form in detalle_salida_formset:
                    detalle_pedido = detalle_salida_form.cleaned_data.get('pedido')
                    code = detalle_salida_form.cleaned_data.get('code')
                    quantity = detalle_salida_form.cleaned_data.get('quantity')
                    price = detalle_salida_form.cleaned_data.get('price')
                    amount = detalle_salida_form.cleaned_data.get('amount')
                    if quantity and price and amount:
                        detalle_movimiento = DetalleMovimiento(line_number=cont,
                                                               movimiento=self.object,
                                                               producto=Producto.objects.get(pk=code),
                                                               detalle_pedido=DetallePedido.objects.get(
                                                                   pk=detalle_pedido),
                                                               quantity=quantity,
                                                               price=price)
                        detalles.append(detalle_movimiento)
                        cont = cont + 1
                DetalleMovimiento.objects.bulk_create(detalles, None, pedido)
                return HttpResponseRedirect(reverse('almacen:detalle_movimiento', args=[self.object.id_movimiento]))
        except IntegrityError:
            messages.error(self.request, 'Error guardando la cotizacion.')

    def form_invalid(self, form, detalle_salida_formset):
        return self.render_to_response(self.get_context_data(form=form,
                                                             detalle_salida_formset=detalle_salida_formset))


class BusquedaProductosAlmacen(SoloAjaxMixin, TemplateView):

    parametros_requeridos = ('description', 'almacen')

    def get(self, request, *args, **kwargs):
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            lista_productos = []
            description = request.GET['description']
            almacen = request.GET['almacen']
            ids = list(Kardex.objects.filter(producto__description__icontains=description,
                                             almacen__id=almacen)
                       .order_by('producto_id').distinct('producto_id')
                       .values_list('producto_id', flat=True)[:20])
            ultimos = Kardex.ultimos_por_producto(ids, almacen__id=almacen)
            for producto_id in ids:
                control = ultimos[producto_id]
                producto_json = {}
                producto_json['label'] = control.producto.description
                producto_json['code'] = control.producto.code
                producto_json['description'] = control.producto.description
                producto_json['unidad'] = control.producto.unidad_medida.description
                try:
                    price = round(control.total_amount / control.total_quantity, 5)
                except (TypeError, ZeroDivisionError):
                    price = 0
                producto_json['price'] = str(price)
                lista_productos.append(producto_json)
            data = json.dumps(lista_productos)
            return HttpResponse(data, 'application/json')


class CargarAlmacenes(CargarCsvMixin, FormView):
    template_name = 'almacen/cargar_almacenes.html'
    form_class = UploadForm
    success_url = reverse_lazy('almacen:almacenes')

    def procesar_fila(self, fila):
        Almacen.objects.create(code=fila[0],
                               description=fila[1])


class CargarInventarioInicial(CargarCsvMixin, FormView):
    template_name = 'almacen/cargar_inventario_inicial.html'
    form_class = CargarInventarioInicialForm

    def obtener_fecha_hora(self, r_date, r_hora):
        r_hora = r_hora.replace(" ", "")
        anio = int(r_date[6:])
        month = int(r_date[3:5])
        dia = int(r_date[0:2])
        horas = int(r_hora[0:2])
        minutos = int(r_hora[3:5])
        # segundos = int(r_hora[6:8])
        date = timezone.make_aware(datetime.datetime(anio, month, dia, horas, minutos))
        return date

    def form_valid(self, form):
        data = form.cleaned_data
        tipo_movimiento = TipoMovimiento.objects.filter(code='I00').first()
        document_type = TipoDocumento.objects.filter(sunat_code='PEC').first()
        faltantes = []
        if tipo_movimiento is None:
            faltantes.append('Falta el tipo de movimiento "I00" (INVENTARIO INICIAL): '
                             'entra al tablero de Almacen para crearlo y vuelve a cargar el file.')
        if document_type is None:
            faltantes.append('Falta el tipo de documento "PEC" (PECOSA): '
                             'entra al tablero de Contabilidad para crearlo y vuelve a cargar el file.')
        if faltantes:
            return self.render_to_response(self.get_context_data(form=form,
                                                                 notificaciones=faltantes))
        self.operation_date = self.obtener_fecha_hora(data['date'], data['hora'])
        self.cont_detalles = 1
        self.detalles = []
        with transaction.atomic():
            self.movimiento = Movimiento.objects.create(tipo_movimiento=tipo_movimiento,
                                                        document_type=document_type,
                                                        almacen=data['almacenes'],
                                                        operation_date=self.operation_date,
                                                        notes='INVENTARIO INICIAL',
                                                        series='SALDO',
                                                        number='INICIAL')
            respuesta = super(CargarInventarioInicial, self).form_valid(form)
            DetalleMovimiento.objects.bulk_create(self.detalles, None, None)
            self.movimiento.save()
        return respuesta

    def procesar_fila(self, fila):
        try:
            producto = Producto.objects.get(description=fila[0].strip())
            quantity = Decimal(fila[1])
            try:
                price = Decimal(fila[2])
            except InvalidOperation:
                price = ''
            try:
                amount = Decimal(fila[3])
            except InvalidOperation:
                amount = ''
            if price == '':
                try:
                    price = amount / quantity
                except (InvalidOperation, ZeroDivisionError):
                    price = 0
            if amount == '':
                amount = quantity * price
            self.detalles.append(DetalleMovimiento(line_number=self.cont_detalles,
                                                  movimiento=self.movimiento,
                                                  producto=producto,
                                                  quantity=quantity,
                                                  price=price,
                                                  amount=amount))
            self.cont_detalles = self.cont_detalles + 1
        except Producto.DoesNotExist:
            pass

    def get_success_url(self):
        return reverse('almacen:detalle_movimiento', args=[self.movimiento.id_movimiento])


class CrearTipoMovimiento(CreateView):
    template_name = 'almacen/tipo_movimiento.html'
    form_class = TipoMovimientoForm
    success_url = reverse_lazy('almacen:tipos_movimientos')

    @method_decorator(requiere('almacen.add_tipomovimiento'))
    def dispatch(self, *args, **kwargs):
        return super(CrearTipoMovimiento, self).dispatch(*args, **kwargs)

    def get_success_url(self):
        return reverse('almacen:detalle_tipo_movimiento', args=[self.object.pk])


class CrearAlmacen(FormView):
    template_name = 'almacen/almacen.html'
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


class CrearDetalleSalida(SoloAjaxMixin, TemplateView):

    def get(self, request, *args, **kwargs):
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            lista_detalles = []
            det = {}
            det['code'] = ''
            det['name'] = ''
            det['quantity'] = '0'
            det['price'] = '0'
            det['unidad'] = ''
            det['amount'] = '0'
            lista_detalles.append(det)
            formset = DetalleSalidaFormSet(initial=lista_detalles)
            lista_json = []
            for form in formset:
                detalle_json = {}
                detalle_json['code'] = str(form['code'])
                detalle_json['name'] = str(form['name'])
                detalle_json['quantity'] = str(form['quantity'])
                detalle_json['price'] = str(form['price'])
                detalle_json['unidad'] = str(form['unidad'])
                detalle_json['amount'] = str(form['amount'])
                lista_json.append(detalle_json)
            data = json.dumps(lista_json)
            return HttpResponse(data, 'application/json')


class CrearDetallePedido(SoloAjaxMixin, TemplateView):

    def get(self, request, *args, **kwargs):
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            lista_detalles = []
            det = {}
            det['code'] = ''
            det['name'] = ''
            det['quantity'] = '0'
            det['unidad'] = ''
            lista_detalles.append(det)
            formset = DetallePedidoFormSet(initial=lista_detalles)
            lista_json = []
            for form in formset:
                detalle_json = {}
                detalle_json['code'] = str(form['code'])
                detalle_json['name'] = str(form['name'])
                detalle_json['quantity'] = str(form['quantity'])
                detalle_json['unidad'] = str(form['unidad'])
                lista_json.append(detalle_json)
            data = json.dumps(lista_json)
            return HttpResponse(data, 'application/json')


class CrearDetalleIngreso(SoloAjaxMixin, TemplateView):

    def get(self, request, *args, **kwargs):
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            lista_detalles = []
            det = {}
            det['orden_compra'] = '0'
            det['code'] = ''
            det['name'] = ''
            det['quantity'] = '0'
            det['price'] = '0'
            det['unidad'] = ''
            det['amount'] = '0'
            lista_detalles.append(det)
            formset = DetalleIngresoFormSet(initial=lista_detalles)
            lista_json = []
            for form in formset:
                detalle_json = {}
                detalle_json['orden_compra'] = str(form['orden_compra'])
                detalle_json['code'] = str(form['code'])
                detalle_json['name'] = str(form['name'])
                detalle_json['quantity'] = str(form['quantity'])
                detalle_json['price'] = str(form['price'])
                detalle_json['unidad'] = str(form['unidad'])
                detalle_json['amount'] = str(form['amount'])
                lista_json.append(detalle_json)
            data = json.dumps(lista_json)
            return HttpResponse(data, 'application/json')


class CrearPedido(CreateView):
    template_name = 'almacen/pedido.html'
    form_class = PedidoForm
    model = Pedido

    @method_decorator(requiere('almacen.add_pedido'))
    def dispatch(self, *args, **kwargs):
        try:
            trabajador = self.request.user.worker
        except ObjectDoesNotExist:
            return HttpResponseRedirect(reverse('administracion:crear_trabajador'))
        if trabajador.firma == '':
            return HttpResponseRedirect(reverse('administracion:modificar_trabajador', args=[trabajador.pk]))
        puesto = trabajador.puesto
        if puesto is None:
            return HttpResponseRedirect(reverse('administracion:crear_puesto'))
        if puesto.is_leadership or puesto.is_assistant:
            return super(CrearPedido, self).dispatch(*args, **kwargs)
        else:
            return HttpResponseRedirect(reverse('seguridad:permiso_denegado'))

    def get(self, request, *args, **kwargs):
        self.object = None
        form_class = self.get_form_class()
        form = self.get_form(form_class)
        detalle_pedido_formset = DetallePedidoFormSet()
        return self.render_to_response(self.get_context_data(form=form,
                                                             detalle_pedido_formset=detalle_pedido_formset))

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
                    code = detalle_pedido_form.cleaned_data.get('code')
                    quantity = detalle_pedido_form.cleaned_data.get('quantity')
                    if code and quantity:
                        producto = Producto.objects.get(code=code)
                        detalles.append(DetallePedido(pedido=self.object,
                                                      line_number=cont,
                                                      producto=producto,
                                                      quantity=quantity))
                        cont = cont + 1
                DetallePedido.objects.bulk_create(detalles)
                puesto_jefe_logistica = Puesto.objects.get(oficina=logistica(), is_leadership=True, is_active=True)
                jefe_logistica = puesto_jefe_logistica.trabajador
                destinatario = jefe_logistica.user.email
                correo_creacion_pedido(destinatario, self.object)
                return HttpResponseRedirect(reverse('almacen:detalle_pedido', args=[self.object.pk]))
        except IntegrityError:
            messages.error(self.request, 'Error guardando el pedido.')

    def form_invalid(self, form, detalle_pedido_formset):
        return self.render_to_response(self.get_context_data(form=form,
                                                             detalle_pedido_formset=detalle_pedido_formset))


class ConsultaStock(SoloAjaxMixin, TemplateView):

    parametros_requeridos = ('almacen', 'code')
    def get(self, request, *args, **kwargs):
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            almacen = request.GET['almacen']
            code = request.GET['code']
            control_producto = Kardex.objects.filter(producto__code=code,
                                                     almacen__id=almacen).latest('operation_date')
            producto_json = {}
            producto_json['stock'] = control_producto.total_quantity
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
    http_method_names = ['post']

    @method_decorator(requiere('almacen.delete_almacen'))
    def dispatch(self, *args, **kwargs):
        return super(EliminarAlmacen, self).dispatch(*args, **kwargs)

    def post(self, request, *args, **kwargs):
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            code = request.POST['code']
            almacen = Almacen.objects.get(pk=code)
            almacen_json = {}
            almacen_json['code'] = almacen.code
            almacen_json['description'] = almacen.description
            if len(almacen.movements.all()) > 0:
                almacen_json['relaciones'] = 'SI'
            else:
                almacen_json['relaciones'] = 'NO'
                Almacen.objects.filter(pk=code).update(is_active=False)
            data = simplejson.dumps(almacen_json)
            return HttpResponse(data, 'application/json')


class EliminarMovimiento(TemplateView):
    http_method_names = ['post']

    @method_decorator(requiere('almacen.delete_movimiento'))
    def dispatch(self, *args, **kwargs):
        return super(EliminarMovimiento, self).dispatch(*args, **kwargs)

    def post(self, request, *args, **kwargs):
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            id_movimiento = request.POST['id_movimiento']
            movimiento = Movimiento.objects.get(pk=id_movimiento)
            orden = movimiento.referencia
            pedido = movimiento.pedido
            if orden is not None:
                movimiento.eliminar_referencia()
            if pedido is not None:
                movimiento.eliminar_pedido()
            detalle_kardex = Kardex.objects.filter(movimiento=movimiento)
            for kardex in detalle_kardex:
                control = ControlProductoAlmacen.objects.get(producto=kardex.producto, almacen=kardex.almacen)
                if kardex.in_quantity > 0:
                    control.stock = control.stock - kardex.in_quantity
                elif kardex.out_quantity > 0:
                    control.stock = control.stock + kardex.out_quantity
                control.save()
                kardex.delete()
            Movimiento.objects.filter(pk=id_movimiento).update(status=Movimiento.STATUS.CANC, referencia=None)
            DetalleMovimiento.objects.filter(movimiento=movimiento).delete()
            movimiento_json = {}
            movimiento_json['id_movimiento'] = id_movimiento
            data = simplejson.dumps(movimiento_json)
            return HttpResponse(data, 'application/json')


class EliminarPedido(TemplateView):
    http_method_names = ['post']

    @method_decorator(requiere('almacen.delete_pedido'))
    def dispatch(self, *args, **kwargs):
        return super(EliminarPedido, self).dispatch(*args, **kwargs)

    def post(self, request, *args, **kwargs):
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            code = request.POST['code']
            pedido = Pedido.objects.get(pk=code)
            movimientos = pedido.movements.all()
            almacen_json = {}
            almacen_json['code'] = pedido.code
            if len(movimientos) > 0:
                almacen_json['movimientos'] = 'SI'
            else:
                almacen_json['movimientos'] = 'NO'
                with transaction.atomic():
                    Pedido.objects.filter(code=code).update(status=Pedido.STATUS.CANC)
                    DetallePedido.objects.filter(pedido=pedido).delete()
            data = simplejson.dumps(almacen_json)
            return HttpResponse(data, 'application/json')


class ListadoAprobacionPedidos(ListView):
    model = Pedido
    template_name = 'almacen/listado_pedidos.html'
    context_object_name = 'pedidos'

    @method_decorator(
        requiere('almacen.ver_tabla_aprobacion_pedidos'))
    def dispatch(self, *args, **kwargs):
        try:
            trabajador = self.request.user.worker
        except ObjectDoesNotExist:
            return HttpResponseRedirect(reverse('administracion:crear_trabajador'))
        try:
            puestos = trabajador.positions.all().filter(is_active=True)
            if trabajador.firma == '':
                return HttpResponseRedirect(reverse('administracion:modificar_trabajador'))
            if puestos[0].is_leadership and puestos[0].oficina == logistica():
                return super(ListadoAprobacionPedidos, self).dispatch(*args, **kwargs)
            else:
                return HttpResponseRedirect(reverse('seguridad:permiso_denegado'))
        except (IndexError, ObjectDoesNotExist):
            return HttpResponseRedirect(reverse('seguridad:permiso_denegado'))

    def get_queryset(self):
        queryset = Pedido.objects.filter(~Q(status=Pedido.STATUS.APROB))
        return queryset


class ListadoAlmacenes(ListView):
    model = Almacen
    template_name = 'almacen/almacenes.html'
    context_object_name = 'almacenes'
    queryset = Almacen.objects.all().order_by('description')


class ListadoPedidos(ListView):
    model = Pedido
    template_name = 'almacen/listado_pedidos.html'
    context_object_name = 'pedidos'
    queryset = Pedido.objects.exclude(status=Pedido.STATUS.CANC).order_by('code')


class ListadoTiposMovimiento(ListView):
    model = TipoMovimiento
    template_name = 'almacen/tipos_movimiento.html'
    context_object_name = 'tipos_movimiento'
    paginate_by = 10
    queryset = TipoMovimiento.objects.all().order_by('code')


class ListadoMovimientos(ListView):
    model = Movimiento
    template_name = 'almacen/movimientos.html'
    context_object_name = 'movimientos'
    queryset = Movimiento.objects.filter(status=Movimiento.STATUS.ACT)


class ListadoIngresos(ListView):
    model = Movimiento
    template_name = 'almacen/listado_ingresos.html'
    context_object_name = 'movimientos'
    queryset = Movimiento.objects.filter(status=Movimiento.STATUS.ACT, tipo_movimiento__increases=True)


class ListadoSalidas(ListView):
    model = Movimiento
    template_name = 'almacen/listado_salidas.html'
    context_object_name = 'movimientos'
    queryset = Movimiento.objects.filter(status=Movimiento.STATUS.ACT, tipo_movimiento__increases=False)


class ListadoMovimientosPorPedido(ListView):
    model = Movimiento
    template_name = 'almacen/movimientos.html'
    context_object_name = 'movimientos'

    @method_decorator(requiere('almacen.ver_tabla_movimientos'))
    def dispatch(self, *args, **kwargs):
        return super(ListadoMovimientosPorPedido, self).dispatch(*args, **kwargs)

    def get_queryset(self):
        pedido = Pedido.objects.get(pk=self.kwargs['pedido'])
        queryset = pedido.movements.all()
        return queryset


class ModificarMovimiento(TemplateView):

    @method_decorator(requiere('almacen.change_movimiento'))
    def dispatch(self, *args, **kwargs):
        return super(ModificarMovimiento, self).dispatch(*args, **kwargs)

    def get(self, request, *args, **kwargs):
        pk = kwargs['pk']
        movimiento = Movimiento.objects.get(pk=pk)
        if movimiento.status == Movimiento.STATUS.CANC:
            return HttpResponseRedirect(reverse('seguridad:permiso_denegado'))
        tipo_movimiento = movimiento.tipo_movimiento
        if tipo_movimiento.increases:
            return HttpResponseRedirect(reverse('almacen:modificar_ingreso_almacen', args=[movimiento.pk]))
        else:
            return HttpResponseRedirect(reverse('almacen:modificar_salida_almacen', args=[movimiento.pk]))


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
        if self.object.status == Movimiento.STATUS.ACT:
            form_class = self.get_form_class()
            form = self.get_form(form_class)
            detalles = DetalleMovimiento.objects.filter(movimiento=self.object).order_by('line_number')
            detalles_data = []
            for detalle in detalles:
                if detalle.detalle_orden_compra is not None:
                    if detalle.detalle_orden_compra.detalle_cotizacion is not None:
                        d = {'orden_compra': detalle.detalle_orden_compra.pk,
                             'code': detalle.detalle_orden_compra.detalle_cotizacion.detalle_requerimiento.producto.code,
                             'name': detalle.detalle_orden_compra.detalle_cotizacion.detalle_requerimiento.producto.description,
                             'unidad': detalle.detalle_orden_compra.detalle_cotizacion.detalle_requerimiento.producto.unidad_medida.code,
                             'quantity': detalle.quantity,
                             'price': detalle.price,
                             'amount': detalle.amount}
                    else:
                        d = {'orden_compra': detalle.detalle_orden_compra.pk,
                             'code': detalle.detalle_orden_compra.producto.code,
                             'name': detalle.detalle_orden_compra.producto.description,
                             'unidad': detalle.detalle_orden_compra.producto.unidad_medida.code,
                             'quantity': detalle.quantity,
                             'price': detalle.price,
                             'amount': detalle.amount}
                else:
                    d = {'orden_compra': '0',
                         'code': detalle.producto.code,
                         'name': detalle.producto.description,
                         'unidad': detalle.producto.unidad_medida.code,
                         'quantity': detalle.quantity,
                         'price': detalle.price,
                         'amount': detalle.amount}
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
        initial['date'] = movimiento.operation_date.strftime('%d/%m/%Y')
        initial['hora'] = movimiento.operation_date.strftime('%H : %M : %S')
        initial['almacen'] = movimiento.almacen
        initial['tipo_movimiento'] = movimiento.tipo_movimiento
        initial['doc_referencia'] = movimiento.referencia
        initial['document_type'] = movimiento.document_type
        initial['series'] = movimiento.series
        initial['number'] = movimiento.number
        initial['total'] = movimiento.total
        initial['notes'] = movimiento.notes
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
                    code = detalle_ingreso_form.cleaned_data.get('code')
                    quantity = detalle_ingreso_form.cleaned_data.get('quantity')
                    price = detalle_ingreso_form.cleaned_data.get('price')
                    amount = detalle_ingreso_form.cleaned_data.get('amount')
                    if quantity and price and amount:
                        try:
                            detalle_orden_compra = DetalleOrdenCompra.objects.get(pk=orden_compra)
                            detalle_movimiento = DetalleMovimiento(detalle_orden_compra=detalle_orden_compra,
                                                                   line_number=cont,
                                                                   movimiento=self.object,
                                                                   producto=Producto.objects.get(pk=code),
                                                                   quantity=quantity,
                                                                   price=price,
                                                                   amount=amount)
                        except ObjectDoesNotExist:
                            detalle_movimiento = DetalleMovimiento(line_number=cont,
                                                                   movimiento=self.object,
                                                                   producto=Producto.objects.get(pk=code),
                                                                   quantity=quantity,
                                                                   price=price,
                                                                   amount=amount)
                        detalles.append(detalle_movimiento)
                        cont = cont + 1
                DetalleMovimiento.objects.bulk_create(detalles, referencia, None)
                return HttpResponseRedirect(reverse('almacen:detalle_movimiento', args=[self.object.pk]))
        except IntegrityError:
            messages.error(self.request, 'Error guardando la cotizacion.')

    def form_invalid(self, form, detalle_ingreso_formset):
        return self.render_to_response(self.get_context_data(form=form,
                                                             detalle_ingreso_formset=detalle_ingreso_formset))


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
        detalles = DetalleMovimiento.objects.filter(movimiento=self.object)
        detalles_data = []
        for detalle in detalles:
            try:
                d = {'pedido': detalle.detalle_pedido.pk,
                     'code': detalle.producto.pk,
                     'name': detalle.producto.description,
                     'unidad': detalle.producto.unidad_medida,
                     'quantity': detalle.quantity,
                     'price': detalle.price,
                     'amount': detalle.amount}
            except (ObjectDoesNotExist, AttributeError):
                d = {'pedido': 0,
                     'code': detalle.producto.pk,
                     'name': detalle.producto.description,
                     'unidad': detalle.producto.unidad_medida,
                     'quantity': detalle.quantity,
                     'price': detalle.price,
                     'amount': detalle.amount}
            detalles_data.append(d)
        detalle_salida_formset = DetalleSalidaFormSet(initial=detalles_data)
        return self.render_to_response(self.get_context_data(form=form,
                                                             detalle_salida_formset=detalle_salida_formset))

    def get_initial(self):
        initial = super(ModificarSalidaAlmacen, self).get_initial()
        movimiento = self.object
        self.detalles = DetalleMovimiento.objects.filter(movimiento=movimiento)
        initial['id_movimiento'] = movimiento.id_movimiento
        initial['date'] = movimiento.operation_date.strftime('%d/%m/%Y')
        initial['hora'] = movimiento.operation_date.strftime('%H : %M : %S')
        initial['almacenes'] = movimiento.almacen
        initial['tipos_salida'] = movimiento.tipo_movimiento
        initial['oficina'] = movimiento.oficina
        initial['referencia'] = movimiento.referencia
        initial['doc_referencia'] = movimiento.document_type
        initial['series'] = movimiento.series
        initial['number'] = movimiento.number
        initial['total'] = movimiento.total
        initial['notes'] = movimiento.notes
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
                    detalle_pedido = detalle_salida_form.cleaned_data.get('pedido')
                    code = detalle_salida_form.cleaned_data.get('code')
                    quantity = detalle_salida_form.cleaned_data.get('quantity')
                    price = detalle_salida_form.cleaned_data.get('price')
                    amount = detalle_salida_form.cleaned_data.get('amount')
                    if quantity and price and amount:
                        try:
                            det_ped = DetallePedido.objects.get(pk=detalle_pedido)
                        except ObjectDoesNotExist:
                            det_ped = None
                        detalle_movimiento = DetalleMovimiento(line_number=cont,
                                                               movimiento=self.object,
                                                               detalle_pedido=det_ped,
                                                               producto=Producto.objects.get(pk=code),
                                                               quantity=quantity,
                                                               price=price,
                                                               amount=amount)
                        detalles.append(detalle_movimiento)
                        cont = cont + 1
                DetalleMovimiento.objects.bulk_create(detalles, referencia, self.object.pedido)
                return HttpResponseRedirect(reverse('almacen:detalle_movimiento', args=[self.object.pk]))
        except IntegrityError:
            messages.error(self.request, 'Error guardando la cotizacion.')

    def form_invalid(self, form, detalle_salida_formset):
        return self.render_to_response(self.get_context_data(form=form,
                                                             detalle_salida_formset=detalle_salida_formset))


class ModificarAlmacen(UpdateView):
    model = Almacen
    template_name = 'almacen/almacen.html'
    form_class = AlmacenForm
    success_url = reverse_lazy('almacen:almacenes')


class ModificarPedido(UpdateView):
    template_name = 'almacen/pedido.html'
    form_class = PedidoForm
    model = Pedido

    @method_decorator(requiere('almacen.change_pedido'))
    def dispatch(self, *args, **kwargs):
        pedido = self.get_object()
        if pedido.status == Pedido.STATUS.PEND:
            return super(ModificarPedido, self).dispatch(*args, **kwargs)
        else:
            return HttpResponseRedirect(reverse('seguridad:permiso_denegado'))

    def get_form_kwargs(self):
        kwargs = super(ModificarPedido, self).get_form_kwargs()
        kwargs['request'] = self.request
        return kwargs

    def get_initial(self):
        initial = super(ModificarPedido, self).get_initial()
        pedido = self.object
        initial['date'] = pedido.date.strftime('%d/%m/%Y')
        initial['notes'] = pedido.notes
        return initial

    def get_context_data(self, **kwargs):
        pedido = self.object
        detalles = DetallePedido.objects.filter(pedido=pedido).order_by('line_number')
        cant_detalles = detalles.count()
        context = super(ModificarPedido, self).get_context_data(**kwargs)
        context['pedido'] = pedido
        context['detalles'] = detalles
        context['cant_detalles'] = cant_detalles
        return context

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        if self.object.status == Pedido.STATUS.PEND:
            form_class = self.get_form_class()
            form = self.get_form(form_class)
            detalles = DetallePedido.objects.filter(pedido=self.object).order_by('line_number')
            detalles_data = []
            for detalle in detalles:
                d = {'code': detalle.producto.code,
                     'name': detalle.producto.description,
                     'unidad': detalle.producto.unidad_medida.code,
                     'quantity': detalle.quantity}
                detalles_data.append(d)
            detalle_pedido_formset = DetallePedidoFormSet(initial=detalles_data)
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
                    code = detalle_pedido_form.cleaned_data.get('code')
                    quantity = detalle_pedido_form.cleaned_data.get('quantity')
                    if code and quantity:
                        producto = Producto.objects.get(code=code)
                        detalles.append(DetallePedido(pedido=self.object,
                                                      line_number=cont,
                                                      producto=producto,
                                                      quantity=quantity))
                        cont = cont + 1
                DetallePedido.objects.bulk_create(detalles)
                return HttpResponseRedirect(reverse('almacen:detalle_pedido', args=[self.object.code]))
        except IntegrityError:
            messages.error(self.request, 'Error guardando la cotizacion.')

    def form_invalid(self, form, detalle_pedido_formset):
        return self.render_to_response(self.get_context_data(form=form,
                                                             detalle_pedido_formset=detalle_pedido_formset))


class MovimientosPorProducto(FormView):
    template_name = 'almacen/movimientos_por_producto.html'
    form_class = FormularioMovimientosProducto

    def form_valid(self, form):
        data = form.cleaned_data
        desde = data['desde']
        hasta = data['hasta']
        almacen = data['almacen']
        producto = Producto.objects.get(code=data['producto'])
        return self.obtener_movimientos(desde, hasta, almacen, producto)

    def obtener_movimientos(self, desde, hasta, almacen, producto):
        detalles = DetalleMovimiento.objects.filter(movimiento__almacen=almacen,
                                                    producto=producto,
                                                    movimiento__operation_date__gte=desde,
                                                    movimiento__operation_date__lte=hasta).order_by(
            'movimiento__operation_date')
        wb = Workbook()
        ws = wb.active
        ws['B1'] = u'Producto: ' + producto.description
        ws.merge_cells('B1:I1')
        ws['B2'] = u'Almacén: ' + almacen.description
        ws.merge_cells('B2:D2')
        ws['E2'] = 'Periodo: Desde: ' + desde.strftime('%d/%m/%Y') + ' Hasta: ' + hasta.strftime('%d/%m/%Y')
        ws.merge_cells('E2:H2')
        ws['B4'] = 'MOVIMIENTO'
        ws['C4'] = 'TIPO MOV.'
        ws['D4'] = 'ORDEN COMPRA'
        ws['E4'] = 'PEDIDO'
        ws['F4'] = 'FECHA OPERACION'
        ws['G4'] = 'CANTIDAD'
        ws['H4'] = 'PRECIO'
        ws['I4'] = 'VALOR'
        cont = 5
        for detalle in detalles:
            ws.cell(row=cont, column=2).value = str(detalle.movimiento)
            ws.cell(row=cont, column=3).value = str(detalle.movimiento.tipo_movimiento)
            if detalle.movimiento.referencia is not None:
                ws.cell(row=cont, column=4).value = str(detalle.movimiento.referencia)
            else:
                ws.cell(row=cont, column=4).value = ""
            if detalle.movimiento.pedido is not None:
                ws.cell(row=cont, column=5).value = str(detalle.movimiento.pedido)
            else:
                ws.cell(row=cont, column=5).value = ""
            ws.cell(row=cont, column=6).value = detalle.movimiento.operation_date.strftime('%d/%m/%Y %H : %M : %S')
            ws.cell(row=cont, column=7).value = detalle.quantity
            ws.cell(row=cont, column=8).value = detalle.price
            ws.cell(row=cont, column=9).value = detalle.amount
            cont = cont + 1
        nombre_archivo = "MovimientosPorProducto.xlsx"
        response = HttpResponse(content_type="application/ms-excel")
        contenido = "attachment; filename={0}".format(nombre_archivo)
        response["Content-Disposition"] = contenido
        wb.save(response)
        return response


class RegistrarIngresoAlmacen(CreateView):
    template_name = 'almacen/ingreso_almacen.html'
    form_class = MovimientoForm
    model = Movimiento

    def get_initial(self):
        initial = super(RegistrarIngresoAlmacen, self).get_initial()
        initial['date'] = date.today().strftime('%d/%m/%Y')
        initial['total'] = 0
        return initial

    def get_form_kwargs(self):
        kwargs = super(RegistrarIngresoAlmacen, self).get_form_kwargs()
        kwargs['tipo_movimiento'] = 'I'
        return kwargs

    def get(self, request, *args, **kwargs):
        self.object = None
        cod_tipo_mov = 'I00'
        tipos_ingreso = TipoMovimiento.objects.filter(increases=True).exclude(code=cod_tipo_mov)
        if not tipos_ingreso:
            return HttpResponseRedirect(reverse('almacen:crear_tipo_movimiento'))
        almacenes = Almacen.objects.all()
        cant_suministros = Producto.objects.count()
        if almacenes.count() > 0:
            if cant_suministros > 0:
                form_class = self.get_form_class()
                form = self.get_form(form_class)
                detalle_ingreso_formset = DetalleIngresoFormSet()
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
                    code = detalle_ingreso_form.cleaned_data.get('code')
                    quantity = detalle_ingreso_form.cleaned_data.get('quantity')
                    price = detalle_ingreso_form.cleaned_data.get('price')
                    amount = detalle_ingreso_form.cleaned_data.get('amount')
                    if quantity and price and amount:
                        try:
                            detalle_orden_compra = DetalleOrdenCompra.objects.get(pk=orden_compra)
                            detalle_movimiento = DetalleMovimiento(detalle_orden_compra=detalle_orden_compra,
                                                                   line_number=cont,
                                                                   movimiento=self.object,
                                                                   producto=Producto.objects.get(pk=code),
                                                                   quantity=quantity,
                                                                   price=price,
                                                                   amount=amount)
                        except ObjectDoesNotExist:
                            detalle_movimiento = DetalleMovimiento(line_number=cont,
                                                                   movimiento=self.object,
                                                                   producto=Producto.objects.get(pk=code),
                                                                   quantity=quantity,
                                                                   price=price,
                                                                   amount=amount)
                        detalles.append(detalle_movimiento)
                        cont = cont + 1
                DetalleMovimiento.objects.bulk_create(detalles, referencia, None)
                return HttpResponseRedirect(reverse('almacen:detalle_movimiento', args=[self.object.pk]))
        except IntegrityError:
            messages.error(self.request, 'Error guardando la cotizacion.')

    def form_invalid(self, form, detalle_ingreso_formset):
        return self.render_to_response(self.get_context_data(form=form,
                                                             detalle_ingreso_formset=detalle_ingreso_formset))


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
        initial['date'] = date.today().strftime('%d/%m/%Y')
        return initial

    def get(self, request, *args, **kwargs):
        self.object = None
        tipos_salida = TipoMovimiento.objects.filter(increases=False)
        if not tipos_salida:
            return HttpResponseRedirect(reverse('almacen:crear_tipo_movimiento'))
        almacenes = Almacen.objects.filter()
        if not almacenes:
            return HttpResponseRedirect(reverse('almacen:crear_almacen'))
        else:
            form_class = self.get_form_class()
            form = self.get_form(form_class)
            detalle_salida_formset = DetalleSalidaFormSet()
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
                    code = detalle_salida_form.cleaned_data.get('code')
                    quantity = detalle_salida_form.cleaned_data.get('quantity')
                    price = detalle_salida_form.cleaned_data.get('price')
                    amount = detalle_salida_form.cleaned_data.get('amount')
                    if quantity and price and amount:
                        detalle_movimiento = DetalleMovimiento(line_number=cont,
                                                               movimiento=self.object,
                                                               producto=Producto.objects.get(pk=code),
                                                               quantity=quantity,
                                                               price=price,
                                                               amount=amount)
                        detalles.append(detalle_movimiento)
                        cont = cont + 1
                DetalleMovimiento.objects.bulk_create(detalles, referencia, None)
                return HttpResponseRedirect(reverse('almacen:detalle_movimiento', args=[self.object.pk]))
        except IntegrityError:
            messages.error(self.request, 'Error guardando la cotizacion.')

    def form_invalid(self, form, detalle_salida_formset):
        return self.render_to_response(self.get_context_data(form=form,
                                                             detalle_salida_formset=detalle_salida_formset))


class ReporteExcelAlmacenes(TemplateView):

    def get(self, request, *args, **kwargs):
        almacenes = Almacen.objects.filter(is_active=True).order_by('code')
        wb = Workbook()
        ws = wb.active
        ws['B1'] = 'REPORTE DE ALMACENES'
        ws.merge_cells('B1:J1')
        ws['B3'] = 'CODIGO'
        ws['C3'] = 'DESCRIPCIÓN'
        cont = 4
        for almacen in almacenes:
            ws.cell(row=cont, column=2).value = almacen.code
            ws.cell(row=cont, column=3).value = almacen.description
            cont = cont + 1
        nombre_archivo = "ListadoAlmacenes.xlsx"
        response = HttpResponse(content_type="application/ms-excel")
        contenido = "attachment; filename={0}".format(nombre_archivo)
        response["Content-Disposition"] = contenido
        wb.save(response)
        return response


class ReporteExcelTiposMovimientos(TemplateView):

    def get(self, request, *args, **kwargs):
        tipos = TipoMovimiento.objects.filter(is_active=True).order_by('code')
        wb = Workbook()
        ws = wb.active
        ws['B1'] = 'REPORTE DE TIPOS DE MOVIMIENTOS'
        ws.merge_cells('B1:J1')
        ws['B3'] = 'CODIGO'
        ws['C3'] = 'DESCRIPCIÓN'
        cont = 4
        for tipo in tipos:
            ws.cell(row=cont, column=2).value = tipo.code
            ws.cell(row=cont, column=3).value = tipo.description
            cont = cont + 1
        nombre_archivo = "MaestroTiposMovimientos.xlsx"
        response = HttpResponse(content_type="application/ms-excel")
        contenido = "attachment; filename={0}".format(nombre_archivo)
        response["Content-Disposition"] = contenido
        wb.save(response)
        return response


class RespuestaReporteMixin(object):
    """Armado de la respuesta HTTP de los reportes que se descargan como file."""

    def _respuesta_pdf(self, contenido, nombre_archivo):
        response = HttpResponse(content_type='application/pdf')
        response['Content-Disposition'] = 'attachment; filename=' + nombre_archivo
        response.write(contenido)
        return response

    def _respuesta_excel(self, excel, nombre_archivo):
        response = HttpResponse(content_type="application/ms-excel")
        response["Content-Disposition"] = "attachment; filename={0}".format(nombre_archivo)
        excel.save(response)
        return response


class ReporteKardexProducto(RespuestaReporteMixin, FormView):
    template_name = 'almacen/reporte_kardex_producto.html'
    form_class = FormularioKardexProducto

    REPORTES_EXCEL = {
        'S': ('obtener_formato_sunat_unidades_fisicas_producto', 'InventarioPermanenteUnidadesFisicas.xlsx'),
        'V': ('obtener_formato_sunat_valorizado_producto', 'InventarioPermanenteValorizado.xlsx'),
        None: ('obtener_formato_normal_producto', 'ReporteExcelKardexProducto.xlsx'),
    }

    REPORTES_PDF = {
        'S': ('imprimir_formato_sunat_unidades_fisicas_producto', 'InventarioPermanenteUnidadesFisicas.pdf'),
        'V': ('imprimir_formato_sunat_valorizado_producto', 'InventarioPermanenteValorizado.pdf'),
    }

    def _formato_sunat(self, formato_sunat):
        return formato_sunat if formato_sunat in ('S', 'V') else None

    def form_valid(self, form):
        data = form.cleaned_data
        cod_prod = data.get('cod_producto')
        producto = Producto.objects.get(code=cod_prod)
        desde = data.get('desde')
        hasta = data.get('hasta')
        almacen = data.get('almacenes')
        formato_sunat = data.get('formato_sunat')
        formatos = data.get('formatos')

        if formatos == 'XLS':
            metodo, nombre_archivo = self.REPORTES_EXCEL[self._formato_sunat(formato_sunat)]
            excel = getattr(ReporteKardexExcel(), metodo)(producto, desde, hasta, almacen)
            return self._respuesta_excel(excel, nombre_archivo)
        if formatos == 'PDF':
            clave = self._formato_sunat(formato_sunat)
            if clave not in self.REPORTES_PDF:
                return HttpResponse('Este reporte no esta disponible en PDF para la combinacion elegida.',
                                    status=404)
            metodo, nombre_archivo = self.REPORTES_PDF[clave]
            reporte = ReporteKardexPDF('A4', desde, hasta, almacen, False)
            return self._respuesta_pdf(getattr(reporte, metodo)(producto), nombre_archivo)
        return HttpResponse('Formato no soportado.', status=400)


class ReporteKardex(RespuestaReporteMixin, FormView):
    template_name = 'almacen/reporte_kardex.html'
    form_class = FormularioKardexProducto

    def form_valid(self, form):
        data = form.cleaned_data
        desde = data.get('desde')
        hasta = data['hasta']
        almacen = data.get('almacenes')
        formato_sunat = data.get('formato_sunat')
        formatos = data.get('formatos')
        consolidado = data['consolidado']

        clave = self._clave_reporte(consolidado, formato_sunat)
        if formatos == 'XLS':
            return self._reporte_excel(clave, desde, hasta, almacen)
        if formatos == 'PDF':
            return self._reporte_pdf(clave, desde, hasta, almacen)
        return HttpResponse('Formato no soportado.', status=400)

    REPORTES_PDF = {
        ('P', None): ('imprimir_formato_consolidado_productos', False, 'ResumenMensualDeAlmacen.pdf'),
        ('G', None): ('imprimir_formato_consolidado_grupos', True, 'ResumenMensualDeAlmacenPorGruposYCuentas.pdf'),
        (None, 'S'): ('imprimir_formato_sunat_unidades_fisicas_todos', False,
                      'InventarioPermanenteUnidadesFisicas.pdf'),
        (None, 'V'): ('imprimir_formato_sunat_valorizado_todos', False, 'InventarioPermanenteValorizado.pdf'),
    }

    REPORTES_EXCEL = {
        ('P', None): ('obtener_consolidado_productos', 'ReporteConsolidadoKardexExcel.xlsx'),
        ('G', None): ('obtener_consolidado_grupos', 'ReporteConsolidadoCuentasContablesAlmacen.xlsx'),
        (None, 'S'): ('obtener_formato_sunat_unidades_fisicas_todos', 'InventarioPermanenteUnidadesFisicas.xlsx'),
        (None, 'V'): ('obtener_formato_sunat_valorizado_todos', 'InventarioPermanenteValorizado.xlsx'),
        (None, None): ('obtener_formato_normal_todos', 'ReporteFormatoNormalKardexTodosLosProductos.xlsx'),
    }

    def _clave_reporte(self, consolidado, formato_sunat):
        if consolidado in ('P', 'G'):
            return (consolidado, None)
        return (None, formato_sunat if formato_sunat in ('S', 'V') else None)

    def _reporte_pdf(self, clave, desde, hasta, almacen):
        if clave not in self.REPORTES_PDF:
            return HttpResponse('Este reporte no esta disponible en PDF para la combinacion elegida.', status=404)
        metodo, agrupado, nombre_archivo = self.REPORTES_PDF[clave]
        reporte = ReporteKardexPDF('A4', desde, hasta, almacen, agrupado)
        return self._respuesta_pdf(getattr(reporte, metodo)(), nombre_archivo)

    def _reporte_excel(self, clave, desde, hasta, almacen):
        metodo, nombre_archivo = self.REPORTES_EXCEL[clave]
        reporte = ReporteKardexExcel()
        return self._respuesta_excel(getattr(reporte, metodo)(desde, hasta, almacen), nombre_archivo)


class ReprocesoPrecio(FormView):
    template_name = 'almacen/reproceso_precio.html'
    form_class = FormularioReprocesoPrecio

    def reprocesar_precio_producto(self, producto, almacen, desde):
        detalles = Kardex.objects.filter(producto=producto,
                                         almacen=almacen,
                                         operation_date__gte=desde).order_by('operation_date')
        indice = 0
        for detalle in detalles:
            try:
                anterior = detalles[indice - 1]
                cantidad_ant = anterior.total_quantity
                valor_ant = anterior.total_amount
                precio_ant = Decimal(round(valor_ant / cantidad_ant, 8))
            except (IndexError, ZeroDivisionError, TypeError):
                cantidad_ant = 0
                precio_ant = 0
                valor_ant = 0
            tipo_mov = detalle.movimiento.tipo_movimiento
            if tipo_mov.increases:
                detalle.total_quantity = cantidad_ant + detalle.in_quantity
                detalle.total_price = detalle.in_price
                detalle.total_amount = valor_ant + detalle.in_amount
            else:
                detalle.out_price = precio_ant
                detalle.out_amount = detalle.out_quantity * detalle.out_price
                detalle.total_quantity = cantidad_ant - detalle.out_quantity
                detalle.total_amount = valor_ant - detalle.out_amount
                try:
                    detalle.total_price = detalle.total_amount / detalle.total_quantity
                except ZeroDivisionError:
                    detalle.total_price = 0
            detalle.save()
            indice = indice + 1

    def form_valid(self, form):
        data = form.cleaned_data
        desde = data['desde']
        almacen = data['almacen']
        seleccion = data['seleccion']
        if seleccion == 'P':
            cod_prod = data['producto']
            producto = Producto.objects.get(code=cod_prod)
            self.reprocesar_precio_producto(producto, almacen, desde)
        else:
            listado_kardex = Kardex.objects.filter(almacen=almacen).order_by('producto').distinct('producto__code')
            for kardex in listado_kardex:
                self.reprocesar_precio_producto(kardex.producto, almacen, desde)
        return HttpResponseRedirect(reverse('almacen:tablero'))


class StockProductos(FormView):
    form_class = FormularioConsultaStock
    template_name = 'almacen/stock_productos.html'

    def get_initial(self):
        initial = super(StockProductos, self).get_initial()
        initial['desde'] = date.today().strftime('%d/%m/%Y')
        return initial

    def form_valid(self, form):
        data = form.cleaned_data
        almacen = data['almacen']
        description = data['description']
        productos = list(Producto.objects.filter(description__icontains=description)
                         .select_related('unidad_medida').order_by('description'))
        wb = Workbook()
        ws = wb.active
        ws['B1'] = 'STOCK DE PRODUCTOS'
        ws.merge_cells('B1:E1')
        ws['B3'] = 'CODIGO'
        ws['C3'] = 'DESCRIPCION'
        ws['D3'] = 'UNIDAD'
        ws['E3'] = 'CANTIDAD'
        ws['F3'] = 'PRECIO'
        ws['G3'] = 'VALOR'
        ws.column_dimensions["B"].width = 12
        ws.column_dimensions["C"].width = 40
        cont = 4
        ultimos = Kardex.ultimos_por_producto(productos, almacen=almacen)
        for producto in productos:
            kardex = ultimos.get(producto.pk)
            code = producto.code
            description = producto.description
            if kardex is None:
                unidad_medida = producto.unidad_medida.code
                stock = 0
                price = 0
                amount = 0
            else:
                unidad_medida = producto.unidad_medida.description
                stock = kardex.total_quantity
                price = kardex.total_price
                amount = kardex.total_amount
            ws.cell(row=cont, column=2).value = code
            ws.cell(row=cont, column=3).value = description
            ws.cell(row=cont, column=4).value = unidad_medida
            ws.cell(row=cont, column=5).value = stock

            temp_precio = format(price, '.3f')
            if temp_precio == '-0.000':
                price = format(abs(price), '.3f')
            else:
                price = format(price, '.3f')
            ws.cell(row=cont, column=6).value = price
            ws.cell(row=cont, column=6).number_format = '#.000'
            temp_valor = format(amount, '.3f')
            if temp_valor == '-0.000':
                amount = format(abs(amount), '.3f')
            else:
                amount = format(amount, '.3f')
            ws.cell(row=cont, column=7).value = amount
            ws.cell(row=cont, column=7).number_format = '#.000'
            cont = cont + 1
        nombre_archivo = "ReporteStock.xlsx"
        response = HttpResponse(content_type="application/ms-excel")
        contenido = "attachment; filename={0}".format(nombre_archivo)
        response["Content-Disposition"] = contenido
        wb.save(response)
        return response


class ListadoStockProducto(SoloAjaxMixin, TemplateView):

    parametros_requeridos = ('description', 'almacen')

    def get(self, request, *args, **kwargs):
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            description = request.GET['description']
            almacen = request.GET['almacen']
            lista_productos = []
            productos = list(Producto.objects.filter(description__icontains=description)
                             .select_related('unidad_medida').order_by('description'))
            ultimos = Kardex.ultimos_por_producto(productos, almacen__pk=almacen)
            for producto in productos:
                kardex = ultimos.get(producto.pk)
                kardex_json = {}
                kardex_json['code'] = producto.code
                kardex_json['label'] = producto.description
                kardex_json['unidad'] = producto.unidad_medida.code
                kardex_json['stock'] = kardex.total_quantity if kardex else 0
                lista_productos.append(kardex_json)
            data = simplejson.dumps(lista_productos)
            return HttpResponse(data, 'application/json')


class ReporteExcelMovimientos(FormView):
    form_class = FormularioReporteMovimientos
    template_name = "almacen/reporte_movimientos.html"

    def form_valid(self, form):
        data = form.cleaned_data
        tipo_busqueda = data['tipo_busqueda']
        p_almacen = data['almacenes']
        p_tipo_movimiento = data['tipos_movimiento']
        almacen = Almacen.objects.get(code=p_almacen)
        tipo_movimiento = TipoMovimiento.objects.get(code=p_tipo_movimiento)
        wb = Workbook()
        ws = wb.active
        if tipo_busqueda == 'F':
            start_date = data['desde']
            fecha_final = data['hasta']
            ws['B1'] = 'REPORTE DE MOVIMIENTOS POR FECHA'
            ws.merge_cells('B1:H1')
            ws['B2'] = 'ALMACEN: ' + almacen.description
            ws.merge_cells('B2:D2')
            ws['E2'] = 'TIPO DE MOVIMIENTO: ' + tipo_movimiento.description
            ws.merge_cells('E2:H2')
            ws['B3'] = 'DESDE'
            ws['C3'] = start_date
            ws['C3'].number_format = 'dd/mm/yyyy'
            ws['D3'] = 'HASTA'
            ws['E3'] = fecha_final
            ws['F3'].number_format = 'dd/mm/yyyy'
            movimientos = Movimiento.objects.filter(operation_date__range=[start_date, fecha_final],
                                                    tipo_movimiento=tipo_movimiento, almacen=almacen)
        elif tipo_busqueda == 'M':
            month = data['month'].strip()
            year = data['year'].strip()
            ws['B1'] = 'REPORTE DE MOVIMIENTOS POR MES'
            ws.merge_cells('B1:H1')
            ws['B2'] = 'ALMACEN: ' + almacen.description
            ws.merge_cells('B2:D2')
            ws['E2'] = 'TIPO DE MOVIMIENTO: ' + tipo_movimiento.description
            ws.merge_cells('E2:H2')
            ws['B3'] = 'MES'
            ws['C3'] = month
            ws['D3'] = 'AÑO'
            ws['E3'] = year
            movimientos = Movimiento.objects.filter(operation_date__month=month,
                                                    operation_date__year=year,
                                                    tipo_movimiento=tipo_movimiento,
                                                    almacen=almacen)
        elif tipo_busqueda == 'A':
            year = data['year'].strip()
            ws['B1'] = 'REPORTE DE MOVIMIENTOS POR AÑO'
            ws.merge_cells('B1:H1')
            ws['B2'] = 'ALMACEN: ' + almacen.description
            ws.merge_cells('B2:D2')
            ws['E2'] = 'TIPO DE MOVIMIENTO: ' + tipo_movimiento.description
            ws.merge_cells('E2:H2')
            ws['B3'] = 'AÑO'
            ws['C3'] = year
            movimientos = Movimiento.objects.filter(operation_date__year=year,
                                                    tipo_movimiento=tipo_movimiento,
                                                    almacen=almacen)
        ws['B5'] = 'ID_MOVIMIENTO'
        ws['C5'] = 'TIPO_DOCUMENTO'
        ws['D5'] = 'SERIE'
        ws['E5'] = 'NUMERO'
        ws['F5'] = 'FECHA_OPERACION'
        ws['G5'] = 'OBSERVACION'
        ws['H5'] = 'FECHA_CREACION'
        ws['I5'] = 'ESTADO'
        cont = 6
        movimientos = movimientos.order_by('operation_date')
        for movimiento in movimientos:
            ws.cell(row=cont, column=2).value = movimiento.id_movimiento
            try:
                ws.cell(row=cont, column=3).value = movimiento.document_type.description
            except ObjectDoesNotExist:
                ws.cell(row=cont, column=3).value = '--'
            ws.cell(row=cont, column=4).value = movimiento.series
            ws.cell(row=cont, column=5).value = movimiento.number
            ws.cell(row=cont, column=6).value = movimiento.operation_date
            ws.cell(row=cont, column=6).number_format = 'dd/mm/yyyy hh:mm:ss'
            ws.cell(row=cont, column=7).value = movimiento.notes
            ws.cell(row=cont, column=8).value = movimiento.created
            ws.cell(row=cont, column=8).number_format = 'dd/mm/yyyy hh:mm:ss'
            ws.cell(row=cont, column=9).value = movimiento.status
            cont = cont + 1
        nombre_archivo = "ReporteMovimientosPorFecha.xlsx"
        response = HttpResponse(content_type="application/ms-excel")
        contenido = "attachment; filename={0}".format(nombre_archivo)
        response["Content-Disposition"] = contenido
        wb.save(response)
        return response


class ReporteExcelMovimientosPorFecha(View):

    def get(self, request, *args, **kwargs):
        p_start_date = kwargs['start_date']
        p_fecha_final = kwargs['end_date']
        p_almacen = kwargs['almacen']
        p_tipo_movimiento = kwargs['tipo_movimiento']
        anio = int(p_start_date[6:])
        month = int(p_start_date[3:5])
        dia = int(p_start_date[0:2])
        start_date = timezone.make_aware(datetime.datetime(anio, month, dia, 23, 59, 59))
        anio = int(p_fecha_final[6:])
        month = int(p_fecha_final[3:5])
        dia = int(p_fecha_final[0:2])
        fecha_final = timezone.make_aware(datetime.datetime(anio, month, dia, 23, 59, 59))
        almacen = Almacen.objects.get(code=p_almacen)
        tipo_movimiento = TipoMovimiento.objects.get(code=p_tipo_movimiento)
        wb = Workbook()
        ws = wb.active
        ws['B1'] = 'REPORTE DE MOVIMIENTOS POR FECHA'
        ws.merge_cells('B1:H1')
        ws['B2'] = 'ALMACEN: ' + almacen.description
        ws.merge_cells('B2:D2')
        ws['E2'] = 'TIPO DE MOVIMIENTO: ' + tipo_movimiento.description
        ws.merge_cells('E2:H2')
        ws['B3'] = 'DESDE'
        ws['C3'] = p_start_date
        ws['C3'].number_format = 'dd/mm/yyyy'
        ws['D3'] = 'HASTA'
        ws['E3'] = p_fecha_final
        ws['F3'].number_format = 'dd/mm/yyyy'
        movimientos = Movimiento.objects.filter(operation_date__range=[start_date, fecha_final],
                                                tipo_movimiento=tipo_movimiento, almacen=almacen)
        ws['B5'] = 'ID_MOVIMIENTO'
        ws['C5'] = 'TIPO_DOCUMENTO'
        ws['D5'] = 'SERIE'
        ws['E5'] = 'NUMERO'
        ws['F5'] = 'FECHA_OPERACION'
        ws['G5'] = 'OBSERVACION'
        ws['H5'] = 'FECHA_CREACION'
        cont = 6
        for movimiento in movimientos:
            ws.cell(row=cont, column=2).value = movimiento.id_movimiento
            ws.cell(row=cont, column=3).value = movimiento.document_type
            ws.cell(row=cont, column=4).value = movimiento.series
            ws.cell(row=cont, column=5).value = movimiento.number
            ws.cell(row=cont, column=6).value = movimiento.operation_date
            ws.cell(row=cont, column=6).number_format = 'dd/mm/yyyy hh:mm:ss'
            ws.cell(row=cont, column=7).value = movimiento.observacion
            ws.cell(row=cont, column=8).value = movimiento.created
            ws.cell(row=cont, column=8).number_format = 'dd/mm/yyyy hh:mm:ss'
            cont = cont + 1
        nombre_archivo = "ReporteMovimientosPorFecha.xlsx"
        response = HttpResponse(content_type="application/ms-excel")
        contenido = "attachment; filename={0}".format(nombre_archivo)
        response["Content-Disposition"] = contenido
        wb.save(response)
        return response


class ReportePDFMovimiento(View):

    def get(self, request, *args, **kwargs):
        id_movimiento = kwargs['id_movimiento']
        movimiento = Movimiento.objects.get(pk=id_movimiento)
        response = HttpResponse(content_type='application/pdf')
        reporte = ReporteMovimiento('A4', movimiento)
        pdf = reporte.imprimir()
        response.write(pdf)
        return response


class ReportePDFProductos(View):

    def get(self, request, *args, **kwargs):
        response = HttpResponse(content_type='application/pdf')
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
        allclientes = [(p.code, p.description, p.precio_mercado, p.grupo_suministros) for p in Producto.objects.all()]

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


class VerificarSolicitaDocumento(SoloAjaxMixin, TemplateView):

    parametros_requeridos = ('tipo',)

    def get(self, request, *args, **kwargs):
        tipo = request.GET['tipo']
        tipo_movimiento = TipoMovimiento.objects.get(pk=tipo)
        json_object = {'solicita_documento': tipo_movimiento.solicita_documento}
        return JsonResponse(json_object)


class VerificarPideReferencia(SoloAjaxMixin, TemplateView):

    parametros_requeridos = ('tipo',)

    def get(self, request, *args, **kwargs):
        tipo = request.GET['tipo']
        tipo_movimiento = TipoMovimiento.objects.get(pk=tipo)
        json_object = {'requires_reference': tipo_movimiento.requires_reference}
        return JsonResponse(json_object)


class VerificarStockParaPedido(SoloAjaxMixin, TemplateView):

    parametros_requeridos = ('almacen', 'pedido')

    def get(self, request, *args, **kwargs):
        almacen = request.GET['almacen']
        pedido = request.GET['pedido']
        detalles = list(DetallePedido.objects.filter(pedido__code=pedido,
                                                     status=DetallePedido.STATUS.PEND)
                        .select_related('producto__unidad_medida').order_by('line_number'))
        ultimos = Kardex.ultimos_por_producto([detalle.producto for detalle in detalles],
                                              almacen__code=almacen)
        lista_detalles = []
        for detalle in detalles:
            control_producto = ultimos.get(detalle.producto_id)
            try:
                stock = control_producto.total_quantity
                price = control_producto.total_amount / stock
            except (AttributeError, ZeroDivisionError):
                stock = 0
                price = 0
            if stock != 0:
                det = {}
                det['pedido'] = detalle.id
                det['code'] = detalle.producto.code
                det['name'] = detalle.producto.description
                det['unidad'] = detalle.producto.unidad_medida.description
                quantity = detalle.quantity - detalle.served_quantity
                if quantity > stock:
                    quantity = stock
                amount = round(quantity * price, 5)
                det['quantity'] = quantity
                det['price'] = round(price, 5)
                det['amount'] = amount
                lista_detalles.append(det)
        formset = DetalleSalidaFormSet(initial=lista_detalles)
        lista_json = []
        for form in formset:
            detalle_json = {}
            detalle_json['pedido'] = str(form['pedido'])
            detalle_json['code'] = str(form['code'])
            detalle_json['name'] = str(form['name'])
            detalle_json['quantity'] = str(form['quantity'])
            detalle_json['price'] = str(form['price'])
            detalle_json['unidad'] = str(form['unidad'])
            detalle_json['amount'] = str(form['amount'])
            lista_json.append(detalle_json)
        data = json.dumps(lista_json)
        return HttpResponse(data, 'application/json')


class Inventario(RespuestaReporteMixin, FormView):
    form_class = FormularioConsultaInventario
    template_name = 'almacen/inventario.html'

    def get_initial(self):
        initial = super(Inventario, self).get_initial()
        initial['desde'] = date.today().strftime('%d/%m/%Y')
        return initial

    def form_valid(self, form):
        return self._respuesta_excel(reporte_inventario(form.cleaned_data['desde']),
                                     'ReporteInventario.xlsx')
