# -*- coding: utf-8 -*- 
from django.utils import timezone
from django.shortcuts import render

from almacen.models import Warehouse, Movement, Kardex, MovementType, MovementDetail, WarehouseProductControl, \
    Order, OrderDetail
from django.http import HttpResponse, HttpResponseRedirect
from django.urls import reverse, reverse_lazy
import datetime
from django.views.generic import TemplateView, FormView, View, ListView
from almacen.forms import WarehouseForm, MovementTypeForm, MovementReportForm, \
    KardexProductForm, InitialInventoryImportForm, MovementForm, \
    InboundDetailFormSet, OutboundDetailFormSet, OrderForm, OrderDetailFormSet, \
    OrderApprovalForm, PriceReprocessForm, \
    ProductMovementForm, StockQueryForm, InventoryQueryForm
from decimal import Decimal, InvalidOperation
from io import BytesIO
from reportlab.platypus import SimpleDocTemplate, Paragraph, TableStyle
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.platypus import Table
from django.http import JsonResponse
from compras.models import PurchaseOrderDetail
from openpyxl import Workbook
import simplejson
import json
from django.views.generic.detail import DetailView
from django.views.generic.edit import UpdateView, CreateView
from administracion.models import Position
import locale
from contabilidad.models import DocumentType
from contabilidad.forms import UploadForm
from seguridad.permisos import requiere
from django.utils.decorators import method_decorator
from django.db.models import Q
from django.db import transaction, IntegrityError
from django.core.exceptions import ObjectDoesNotExist
from django.contrib import messages
from productos.models import Product
from almacen.mail import correo_creacion_pedido
from almacen.reports import MovementReport, KardexPdfReport, KardexExcelReport, reporte_inventario
from tambox.configuracion import logistica
from tambox.vistas import CargarCsvMixin, SoloAjaxMixin
from datetime import date

locale.setlocale(locale.LC_ALL, "")


class Dashboard(View):

    def get(self, request, *args, **kwargs):
        cod_mov_invent_ini = 'I00'
        cod_mov_ingreso_compra = 'I01'
        cod_mov_salida_pedido = 'S01'
        lista_notificaciones = []
        cant_almacenes = Warehouse.objects.count()
        cant_tipos_movimientos_ingreso = MovementType.objects.filter(increases=True).exclude(
            code=cod_mov_invent_ini).count()
        cant_tipos_movimientos_salida = MovementType.objects.filter(increases=False).count()
        movement_type, creado = MovementType.objects.get_or_create(code=cod_mov_invent_ini,
                                                                       defaults={'description': 'INVENTARIO INICIAL',
                                                                                 'sunat_code': '16',
                                                                                 'increases': True,
                                                                                 'is_active': True})
        if creado:
            lista_notificaciones.append("Se ha creado el tipo de movimiento inventario inicial")
        movement_type, creado = MovementType.objects.get_or_create(code=cod_mov_ingreso_compra,
                                                                       defaults={'description': 'INGRESO POR COMPRA',
                                                                                 'sunat_code': '02',
                                                                                 'increases': True,
                                                                                 'requires_reference': True,
                                                                                 'is_active': True})
        if creado:
            lista_notificaciones.append("Se ha creado el tipo de movimiento Ingreso por Compra")
        movement_type, creado = MovementType.objects.get_or_create(code=cod_mov_salida_pedido,
                                                                       defaults={'description': 'SALIDA POR PEDIDO',
                                                                                 'sunat_code': '10',
                                                                                 'increases': False,
                                                                                 'requires_reference': True,
                                                                                 'is_active': True})
        inventario_inicial = Movement.objects.filter(movement_type__code=cod_mov_invent_ini).count()
        if creado:
            lista_notificaciones.append("Se ha creado el tipo de movimiento Salida por Pedido")
        if cant_almacenes == 0:
            lista_notificaciones.append("No se ha creado ningún almacén")
        if cant_tipos_movimientos_ingreso == 0:
            lista_notificaciones.append("No se ha creado ningún tipo de movimiento de ingreso")
        if cant_tipos_movimientos_salida == 0:
            lista_notificaciones.append("No se ha creado ningún tipo de movimiento de salida")
        if inventario_inicial == 0:
            lista_notificaciones.append("No se ha realizado el inventario inicial")
        context = {'notificaciones': lista_notificaciones}
        return render(request, 'almacen/tablero_almacen.html', context)


class OrderApprove(CreateView):
    form_class = OrderApprovalForm
    template_name = 'almacen/aprobar_pedido.html'
    model = Movement

    @method_decorator(requiere('almacen.aprobar_pedido'))
    def dispatch(self, *args, **kwargs):
        self.code = kwargs['code']
        return super(OrderApprove, self).dispatch(*args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super(OrderApprove, self).get_form_kwargs()
        kwargs['request'] = self.request
        return kwargs

    def get_initial(self):
        initial = super(OrderApprove, self).get_initial()
        initial['cod_pedido'] = self.code
        return initial

    def get_context_data(self, **kwargs):
        order = Order.objects.get(code=self.code)
        context = super(OrderApprove, self).get_context_data(**kwargs)
        context['order'] = order
        return context

    def get(self, request, *args, **kwargs):
        self.object = None
        form_class = self.get_form_class()
        form = self.get_form(form_class)
        order = Order.objects.get(code=self.code)
        try:
            worker = self.request.user.worker
        except ObjectDoesNotExist:
            return HttpResponseRedirect(reverse('administracion:crear_trabajador'))
        try:
            puestos = worker.positions.all().filter(is_active=True)
            if worker.signature == '':
                return HttpResponseRedirect(reverse('administracion:modificar_trabajador'))
            if puestos[0].is_leadership and puestos[0].office == logistica():
                form_class = self.get_form_class()
                form = self.get_form(form_class)
                detalles = OrderDetail.objects.filter(order=order, status=OrderDetail.STATUS.PEND)
                detalles_data = []
                for detalle in detalles:
                    d = {'order': detalle.id,
                         'code': detalle.product.code,
                         'name': detalle.product.description,
                         'unidad': detalle.product.unit_of_measure.code,
                         'quantity': detalle.quantity
                         }
                    detalles_data.append(d)
                detalle_salida_formset = OutboundDetailFormSet(initial=detalles_data)
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
        detalle_salida_formset = OutboundDetailFormSet(request.POST)
        if form.is_valid() and detalle_salida_formset.is_valid():
            return self.form_valid(form, detalle_salida_formset)
        else:
            return self.form_invalid(form, detalle_salida_formset)

    def form_valid(self, form, detalle_salida_formset):
        try:
            with transaction.atomic():
                self.object = form.save()
                order = self.object.order
                detalles = []
                cont = 1
                for detalle_salida_form in detalle_salida_formset:
                    order_detail = detalle_salida_form.cleaned_data.get('order')
                    code = detalle_salida_form.cleaned_data.get('code')
                    quantity = detalle_salida_form.cleaned_data.get('quantity')
                    price = detalle_salida_form.cleaned_data.get('price')
                    amount = detalle_salida_form.cleaned_data.get('amount')
                    if quantity and price and amount:
                        detalle_movimiento = MovementDetail(line_number=cont,
                                                               movement=self.object,
                                                               product=Product.objects.get(pk=code),
                                                               order_detail=OrderDetail.objects.get(
                                                                   pk=order_detail),
                                                               quantity=quantity,
                                                               price=price)
                        detalles.append(detalle_movimiento)
                        cont = cont + 1
                MovementDetail.objects.bulk_create(detalles, None, order)
                return HttpResponseRedirect(reverse('almacen:detalle_movimiento', args=[self.object.movement_id]))
        except IntegrityError:
            messages.error(self.request, 'Error guardando la cotizacion.')

    def form_invalid(self, form, detalle_salida_formset):
        return self.render_to_response(self.get_context_data(form=form,
                                                             detalle_salida_formset=detalle_salida_formset))


class ProductWarehouseSearch(SoloAjaxMixin, TemplateView):

    parametros_requeridos = ('description', 'warehouse')

    def get(self, request, *args, **kwargs):
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            lista_productos = []
            description = request.GET['description']
            warehouse = request.GET['warehouse']
            ids = list(Kardex.objects.filter(product__description__icontains=description,
                                             warehouse__id=warehouse)
                       .order_by('product_id').distinct('product_id')
                       .values_list('product_id', flat=True)[:20])
            ultimos = Kardex.ultimos_por_producto(ids, warehouse__id=warehouse)
            for product_id in ids:
                control = ultimos[product_id]
                producto_json = {}
                producto_json['label'] = control.product.description
                producto_json['code'] = control.product.code
                producto_json['description'] = control.product.description
                producto_json['unidad'] = control.product.unit_of_measure.description
                try:
                    price = round(control.total_amount / control.total_quantity, 5)
                except (TypeError, ZeroDivisionError):
                    price = 0
                producto_json['price'] = str(price)
                lista_productos.append(producto_json)
            data = json.dumps(lista_productos)
            return HttpResponse(data, 'application/json')


class WarehouseImport(CargarCsvMixin, FormView):
    template_name = 'almacen/cargar_almacenes.html'
    form_class = UploadForm
    success_url = reverse_lazy('almacen:almacenes')

    def procesar_fila(self, fila):
        Warehouse.objects.create(code=fila[0],
                               description=fila[1])


class InitialInventoryImport(CargarCsvMixin, FormView):
    template_name = 'almacen/cargar_inventario_inicial.html'
    form_class = InitialInventoryImportForm

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
        movement_type = MovementType.objects.filter(code='I00').first()
        document_type = DocumentType.objects.filter(sunat_code='PEC').first()
        faltantes = []
        if movement_type is None:
            faltantes.append('Falta el tipo de movimiento "I00" (INVENTARIO INICIAL): '
                             'entra al tablero de Almacen para crearlo y vuelve a cargar el archivo.')
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
            self.movement = Movement.objects.create(movement_type=movement_type,
                                                        document_type=document_type,
                                                        warehouse=data['almacenes'],
                                                        operation_date=self.operation_date,
                                                        notes='INVENTARIO INICIAL',
                                                        series='SALDO',
                                                        number='INICIAL')
            respuesta = super(InitialInventoryImport, self).form_valid(form)
            MovementDetail.objects.bulk_create(self.detalles, None, None)
            self.movement.save()
        return respuesta

    def procesar_fila(self, fila):
        try:
            product = Product.objects.get(description=fila[0].strip())
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
            self.detalles.append(MovementDetail(line_number=self.cont_detalles,
                                                  movement=self.movement,
                                                  product=product,
                                                  quantity=quantity,
                                                  price=price,
                                                  amount=amount))
            self.cont_detalles = self.cont_detalles + 1
        except Product.DoesNotExist:
            pass

    def get_success_url(self):
        return reverse('almacen:detalle_movimiento', args=[self.movement.movement_id])


class MovementTypeCreate(CreateView):
    template_name = 'almacen/tipo_movimiento.html'
    form_class = MovementTypeForm
    success_url = reverse_lazy('almacen:tipos_movimientos')

    @method_decorator(requiere('almacen.add_movementtype'))
    def dispatch(self, *args, **kwargs):
        return super(MovementTypeCreate, self).dispatch(*args, **kwargs)

    def get_success_url(self):
        return reverse('almacen:detalle_tipo_movimiento', args=[self.object.pk])


class WarehouseCreate(FormView):
    template_name = 'almacen/almacen.html'
    form_class = WarehouseForm
    success_url = reverse_lazy('almacen:almacenes')

    def form_valid(self, form):
        form.save()
        return super(WarehouseCreate, self).form_valid(form)


'''class OutboundDetailCreate(FormView):
    template_name = 'almacen/crear_detalle_salida.html'
    form_class = MovementDetailForm
    success_url = reverse_lazy('almacen:crear_detalle_salida')
    
    def get(self, request, *args, **kwargs):
        self.warehouse = kwargs['warehouse']
        return super(OutboundDetailCreate, self).get(request, *args, **kwargs)
    
    def get_initial(self):
        initial = super(OutboundDetailCreate, self).get_initial()        
        initial['warehouse'] = self.warehouse       
        return initial

    def form_valid(self, form):
        form.save()
        return super(OutboundDetailCreate, self).form_valid(form)'''


class OutboundDetailCreate(SoloAjaxMixin, TemplateView):

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
            formset = OutboundDetailFormSet(initial=lista_detalles)
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


class OrderDetailCreate(SoloAjaxMixin, TemplateView):

    def get(self, request, *args, **kwargs):
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            lista_detalles = []
            det = {}
            det['code'] = ''
            det['name'] = ''
            det['quantity'] = '0'
            det['unidad'] = ''
            lista_detalles.append(det)
            formset = OrderDetailFormSet(initial=lista_detalles)
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


class InboundDetailCreate(SoloAjaxMixin, TemplateView):

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
            formset = InboundDetailFormSet(initial=lista_detalles)
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


class OrderCreate(CreateView):
    template_name = 'almacen/pedido.html'
    form_class = OrderForm
    model = Order
    context_object_name = 'order'

    @method_decorator(requiere('almacen.add_order'))
    def dispatch(self, *args, **kwargs):
        try:
            worker = self.request.user.worker
        except ObjectDoesNotExist:
            return HttpResponseRedirect(reverse('administracion:crear_trabajador'))
        if worker.signature == '':
            return HttpResponseRedirect(reverse('administracion:modificar_trabajador', args=[worker.pk]))
        puesto = worker.puesto
        if puesto is None:
            return HttpResponseRedirect(reverse('administracion:crear_puesto'))
        if puesto.is_leadership or puesto.is_assistant:
            return super(OrderCreate, self).dispatch(*args, **kwargs)
        else:
            return HttpResponseRedirect(reverse('seguridad:permiso_denegado'))

    def get(self, request, *args, **kwargs):
        self.object = None
        form_class = self.get_form_class()
        form = self.get_form(form_class)
        detalle_pedido_formset = OrderDetailFormSet()
        return self.render_to_response(self.get_context_data(form=form,
                                                             detalle_pedido_formset=detalle_pedido_formset))

    def get_form_kwargs(self):
        kwargs = super(OrderCreate, self).get_form_kwargs()
        kwargs['request'] = self.request
        return kwargs

    def post(self, request, *args, **kwargs):
        self.object = None
        form_class = self.get_form_class()
        form = self.get_form(form_class)
        detalle_pedido_formset = OrderDetailFormSet(request.POST)
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
                        product = Product.objects.get(code=code)
                        detalles.append(OrderDetail(order=self.object,
                                                      line_number=cont,
                                                      product=product,
                                                      quantity=quantity))
                        cont = cont + 1
                OrderDetail.objects.bulk_create(detalles)
                puesto_jefe_logistica = Position.objects.get(office=logistica(), is_leadership=True, is_active=True)
                jefe_logistica = puesto_jefe_logistica.worker
                destinatario = jefe_logistica.user.email
                correo_creacion_pedido(destinatario, self.object)
                return HttpResponseRedirect(reverse('almacen:order_detail', args=[self.object.pk]))
        except IntegrityError:
            messages.error(self.request, 'Error guardando el pedido.')

    def form_invalid(self, form, detalle_pedido_formset):
        return self.render_to_response(self.get_context_data(form=form,
                                                             detalle_pedido_formset=detalle_pedido_formset))


class StockQuery(SoloAjaxMixin, TemplateView):

    parametros_requeridos = ('warehouse', 'code')
    def get(self, request, *args, **kwargs):
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            warehouse = request.GET['warehouse']
            code = request.GET['code']
            control_producto = Kardex.objects.filter(product__code=code,
                                                     warehouse__id=warehouse).latest('operation_date')
            producto_json = {}
            producto_json['stock'] = control_producto.total_quantity
            data = simplejson.dumps(producto_json)
            return HttpResponse(data, 'application/json')


class WarehouseDetail(DetailView):
    model = Warehouse
    template_name = 'almacen/detalle_almacen.html'


class MovementTypeDetail(DetailView):
    model = MovementType
    template_name = 'almacen/detalle_tipo_movimiento.html'


class OrderDetailView(DetailView):
    model = Order
    context_object_name = 'order'
    template_name = 'almacen/detalle_pedido.html'


class MovementDetailView(DetailView):
    model = Movement
    context_object_name = 'movement'
    template_name = 'almacen/detalle_movimiento.html'


class WarehouseDelete(TemplateView):
    http_method_names = ['post']

    @method_decorator(requiere('almacen.delete_warehouse'))
    def dispatch(self, *args, **kwargs):
        return super(WarehouseDelete, self).dispatch(*args, **kwargs)

    def post(self, request, *args, **kwargs):
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            code = request.POST['code']
            warehouse = Warehouse.objects.get(pk=code)
            almacen_json = {}
            almacen_json['code'] = warehouse.code
            almacen_json['description'] = warehouse.description
            if len(warehouse.movements.all()) > 0:
                almacen_json['relaciones'] = 'SI'
            else:
                almacen_json['relaciones'] = 'NO'
                Warehouse.objects.filter(pk=code).update(is_active=False)
            data = simplejson.dumps(almacen_json)
            return HttpResponse(data, 'application/json')


class MovementDelete(TemplateView):
    http_method_names = ['post']

    @method_decorator(requiere('almacen.delete_movement'))
    def dispatch(self, *args, **kwargs):
        return super(MovementDelete, self).dispatch(*args, **kwargs)

    def post(self, request, *args, **kwargs):
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            movement_id = request.POST['movement_id']
            movement = Movement.objects.get(pk=movement_id)
            order = movement.reference
            order = movement.order
            if order is not None:
                movement.eliminar_referencia()
            if order is not None:
                movement.eliminar_pedido()
            detalle_kardex = Kardex.objects.filter(movement=movement)
            for kardex in detalle_kardex:
                control = WarehouseProductControl.objects.get(product=kardex.product, warehouse=kardex.warehouse)
                if kardex.in_quantity > 0:
                    control.stock = control.stock - kardex.in_quantity
                elif kardex.out_quantity > 0:
                    control.stock = control.stock + kardex.out_quantity
                control.save()
                kardex.delete()
            Movement.objects.filter(pk=movement_id).update(status=Movement.STATUS.CANC, reference=None)
            MovementDetail.objects.filter(movement=movement).delete()
            movimiento_json = {}
            movimiento_json['movement_id'] = movement_id
            data = simplejson.dumps(movimiento_json)
            return HttpResponse(data, 'application/json')


class OrderDelete(TemplateView):
    http_method_names = ['post']

    @method_decorator(requiere('almacen.delete_order'))
    def dispatch(self, *args, **kwargs):
        return super(OrderDelete, self).dispatch(*args, **kwargs)

    def post(self, request, *args, **kwargs):
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            code = request.POST['code']
            order = Order.objects.get(pk=code)
            movimientos = order.movements.all()
            almacen_json = {}
            almacen_json['code'] = order.code
            if len(movimientos) > 0:
                almacen_json['movimientos'] = 'SI'
            else:
                almacen_json['movimientos'] = 'NO'
                with transaction.atomic():
                    Order.objects.filter(code=code).update(status=Order.STATUS.CANC)
                    OrderDetail.objects.filter(order=order).delete()
            data = simplejson.dumps(almacen_json)
            return HttpResponse(data, 'application/json')


class OrderApprovalList(ListView):
    model = Order
    template_name = 'almacen/listado_pedidos.html'
    context_object_name = 'pedidos'

    @method_decorator(
        requiere('almacen.ver_tabla_aprobacion_pedidos'))
    def dispatch(self, *args, **kwargs):
        try:
            worker = self.request.user.worker
        except ObjectDoesNotExist:
            return HttpResponseRedirect(reverse('administracion:crear_trabajador'))
        try:
            puestos = worker.positions.all().filter(is_active=True)
            if worker.signature == '':
                return HttpResponseRedirect(reverse('administracion:modificar_trabajador'))
            if puestos[0].is_leadership and puestos[0].office == logistica():
                return super(OrderApprovalList, self).dispatch(*args, **kwargs)
            else:
                return HttpResponseRedirect(reverse('seguridad:permiso_denegado'))
        except (IndexError, ObjectDoesNotExist):
            return HttpResponseRedirect(reverse('seguridad:permiso_denegado'))

    def get_queryset(self):
        queryset = Order.objects.filter(~Q(status=Order.STATUS.APROB))
        return queryset


class WarehouseList(ListView):
    model = Warehouse
    template_name = 'almacen/almacenes.html'
    context_object_name = 'almacenes'
    queryset = Warehouse.objects.all().order_by('description')


class OrderList(ListView):
    model = Order
    template_name = 'almacen/listado_pedidos.html'
    context_object_name = 'pedidos'
    queryset = Order.objects.exclude(status=Order.STATUS.CANC).order_by('code')


class MovementTypeList(ListView):
    model = MovementType
    template_name = 'almacen/tipos_movimiento.html'
    context_object_name = 'tipos_movimiento'
    paginate_by = 10
    queryset = MovementType.objects.all().order_by('code')


class MovementList(ListView):
    model = Movement
    template_name = 'almacen/movimientos.html'
    context_object_name = 'movimientos'
    queryset = Movement.objects.filter(status=Movement.STATUS.ACT)


class InboundList(ListView):
    model = Movement
    template_name = 'almacen/listado_ingresos.html'
    context_object_name = 'movimientos'
    queryset = Movement.objects.filter(status=Movement.STATUS.ACT, movement_type__increases=True)


class OutboundList(ListView):
    model = Movement
    template_name = 'almacen/listado_salidas.html'
    context_object_name = 'movimientos'
    queryset = Movement.objects.filter(status=Movement.STATUS.ACT, movement_type__increases=False)


class MovementListByOrder(ListView):
    model = Movement
    template_name = 'almacen/movimientos.html'
    context_object_name = 'movimientos'

    @method_decorator(requiere('almacen.ver_tabla_movimientos'))
    def dispatch(self, *args, **kwargs):
        return super(MovementListByOrder, self).dispatch(*args, **kwargs)

    def get_queryset(self):
        order = Order.objects.get(pk=self.kwargs['order'])
        queryset = order.movements.all()
        return queryset


class MovementUpdate(TemplateView):

    @method_decorator(requiere('almacen.change_movement'))
    def dispatch(self, *args, **kwargs):
        return super(MovementUpdate, self).dispatch(*args, **kwargs)

    def get(self, request, *args, **kwargs):
        pk = kwargs['pk']
        movement = Movement.objects.get(pk=pk)
        if movement.status == Movement.STATUS.CANC:
            return HttpResponseRedirect(reverse('seguridad:permiso_denegado'))
        movement_type = movement.movement_type
        if movement_type.increases:
            return HttpResponseRedirect(reverse('almacen:modificar_ingreso_almacen', args=[movement.pk]))
        else:
            return HttpResponseRedirect(reverse('almacen:modificar_salida_almacen', args=[movement.pk]))


class InboundUpdate(UpdateView):
    template_name = 'almacen/ingreso_almacen.html'
    form_class = MovementForm
    model = Movement
    context_object_name = 'movement'

    def get_form_kwargs(self):
        kwargs = super(InboundUpdate, self).get_form_kwargs()
        kwargs['movement_type'] = 'I'
        return kwargs

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        if self.object.status == Movement.STATUS.ACT:
            form_class = self.get_form_class()
            form = self.get_form(form_class)
            detalles = MovementDetail.objects.filter(movement=self.object).order_by('line_number')
            detalles_data = []
            for detalle in detalles:
                if detalle.purchase_order_detail is not None:
                    if detalle.purchase_order_detail.quotation_detail is not None:
                        d = {'orden_compra': detalle.purchase_order_detail.pk,
                             'code': detalle.purchase_order_detail.quotation_detail.requirement_detail.product.code,
                             'name': detalle.purchase_order_detail.quotation_detail.requirement_detail.product.description,
                             'unidad': detalle.purchase_order_detail.quotation_detail.requirement_detail.product.unit_of_measure.code,
                             'quantity': detalle.quantity,
                             'price': detalle.price,
                             'amount': detalle.amount}
                    else:
                        d = {'orden_compra': detalle.purchase_order_detail.pk,
                             'code': detalle.purchase_order_detail.product.code,
                             'name': detalle.purchase_order_detail.product.description,
                             'unidad': detalle.purchase_order_detail.product.unit_of_measure.code,
                             'quantity': detalle.quantity,
                             'price': detalle.price,
                             'amount': detalle.amount}
                else:
                    d = {'orden_compra': '0',
                         'code': detalle.product.code,
                         'name': detalle.product.description,
                         'unidad': detalle.product.unit_of_measure.code,
                         'quantity': detalle.quantity,
                         'price': detalle.price,
                         'amount': detalle.amount}
                detalles_data.append(d)
            detalle_ingreso_formset = InboundDetailFormSet(initial=detalles_data)
            return self.render_to_response(self.get_context_data(form=form,
                                                                 detalle_ingreso_formset=detalle_ingreso_formset))
        else:
            return HttpResponseRedirect(reverse('almacen:listado_ingresos'))

    def get_initial(self):
        initial = super(InboundUpdate, self).get_initial()
        movement = self.object
        initial['movement_id'] = movement.movement_id
        initial['date'] = movement.operation_date.strftime('%d/%m/%Y')
        initial['hora'] = movement.operation_date.strftime('%H : %M : %S')
        initial['warehouse'] = movement.warehouse
        initial['movement_type'] = movement.movement_type
        initial['doc_referencia'] = movement.reference
        initial['document_type'] = movement.document_type
        initial['series'] = movement.series
        initial['number'] = movement.number
        initial['total'] = movement.total
        initial['notes'] = movement.notes
        return initial

    def get_context_data(self, **kwargs):
        movement = self.object
        context = super(InboundUpdate, self).get_context_data(**kwargs)
        context['movement'] = movement
        return context

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        form_class = self.get_form_class()
        form = self.get_form(form_class)
        detalle_ingreso_formset = InboundDetailFormSet(request.POST)
        if form.is_valid() and detalle_ingreso_formset.is_valid():
            return self.form_valid(form, detalle_ingreso_formset)
        else:
            return self.form_invalid(form, detalle_ingreso_formset)

    def form_valid(self, form, detalle_ingreso_formset):
        try:
            with transaction.atomic():
                if self.object.reference:
                    self.object.eliminar_referencia()
                self.object.eliminar_kardex()
                self.object.eliminar_detalles()
                self.object = form.save()
                reference = self.object.reference
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
                            purchase_order_detail = PurchaseOrderDetail.objects.get(pk=orden_compra)
                            detalle_movimiento = MovementDetail(purchase_order_detail=purchase_order_detail,
                                                                   line_number=cont,
                                                                   movement=self.object,
                                                                   product=Product.objects.get(pk=code),
                                                                   quantity=quantity,
                                                                   price=price,
                                                                   amount=amount)
                        except ObjectDoesNotExist:
                            detalle_movimiento = MovementDetail(line_number=cont,
                                                                   movement=self.object,
                                                                   product=Product.objects.get(pk=code),
                                                                   quantity=quantity,
                                                                   price=price,
                                                                   amount=amount)
                        detalles.append(detalle_movimiento)
                        cont = cont + 1
                MovementDetail.objects.bulk_create(detalles, reference, None)
                return HttpResponseRedirect(reverse('almacen:detalle_movimiento', args=[self.object.pk]))
        except IntegrityError:
            messages.error(self.request, 'Error guardando la cotizacion.')

    def form_invalid(self, form, detalle_ingreso_formset):
        return self.render_to_response(self.get_context_data(form=form,
                                                             detalle_ingreso_formset=detalle_ingreso_formset))


class OutboundUpdate(UpdateView):
    template_name = 'almacen/salida_almacen.html'
    form_class = MovementForm
    model = Movement
    context_object_name = 'movement'

    def get_form_kwargs(self):
        kwargs = super(OutboundUpdate, self).get_form_kwargs()
        kwargs['movement_type'] = 'S'
        return kwargs

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        form_class = self.get_form_class()
        form = self.get_form(form_class)
        detalles = MovementDetail.objects.filter(movement=self.object)
        detalles_data = []
        for detalle in detalles:
            try:
                d = {'order': detalle.order_detail.pk,
                     'code': detalle.product.pk,
                     'name': detalle.product.description,
                     'unidad': detalle.product.unit_of_measure,
                     'quantity': detalle.quantity,
                     'price': detalle.price,
                     'amount': detalle.amount}
            except (ObjectDoesNotExist, AttributeError):
                d = {'order': 0,
                     'code': detalle.product.pk,
                     'name': detalle.product.description,
                     'unidad': detalle.product.unit_of_measure,
                     'quantity': detalle.quantity,
                     'price': detalle.price,
                     'amount': detalle.amount}
            detalles_data.append(d)
        detalle_salida_formset = OutboundDetailFormSet(initial=detalles_data)
        return self.render_to_response(self.get_context_data(form=form,
                                                             detalle_salida_formset=detalle_salida_formset))

    def get_initial(self):
        initial = super(OutboundUpdate, self).get_initial()
        movement = self.object
        self.detalles = MovementDetail.objects.filter(movement=movement)
        initial['movement_id'] = movement.movement_id
        initial['date'] = movement.operation_date.strftime('%d/%m/%Y')
        initial['hora'] = movement.operation_date.strftime('%H : %M : %S')
        initial['almacenes'] = movement.warehouse
        initial['tipos_salida'] = movement.movement_type
        initial['office'] = movement.office
        initial['reference'] = movement.reference
        initial['doc_referencia'] = movement.document_type
        initial['series'] = movement.series
        initial['number'] = movement.number
        initial['total'] = movement.total
        initial['notes'] = movement.notes
        initial['cdetalles'] = self.detalles.count()
        return initial

    def get_context_data(self, **kwargs):
        movement = self.object
        context = super(OutboundUpdate, self).get_context_data(**kwargs)
        context['movement'] = movement
        context['detalles'] = self.detalles
        return context

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        form_class = self.get_form_class()
        form = self.get_form(form_class)
        detalle_salida_formset = OutboundDetailFormSet(request.POST)
        if form.is_valid() and detalle_salida_formset.is_valid():
            return self.form_valid(form, detalle_salida_formset)
        else:
            return self.form_invalid(form, detalle_salida_formset)

    def form_valid(self, form, detalle_salida_formset):
        try:
            with transaction.atomic():
                if self.object.reference:
                    self.object.eliminar_referencia()
                self.object.eliminar_detalles()
                self.object.eliminar_kardex()
                self.object = form.save()
                reference = self.object.reference
                detalles = []
                cont = 1
                for detalle_salida_form in detalle_salida_formset:
                    order_detail = detalle_salida_form.cleaned_data.get('order')
                    code = detalle_salida_form.cleaned_data.get('code')
                    quantity = detalle_salida_form.cleaned_data.get('quantity')
                    price = detalle_salida_form.cleaned_data.get('price')
                    amount = detalle_salida_form.cleaned_data.get('amount')
                    if quantity and price and amount:
                        try:
                            det_ped = OrderDetail.objects.get(pk=order_detail)
                        except ObjectDoesNotExist:
                            det_ped = None
                        detalle_movimiento = MovementDetail(line_number=cont,
                                                               movement=self.object,
                                                               order_detail=det_ped,
                                                               product=Product.objects.get(pk=code),
                                                               quantity=quantity,
                                                               price=price,
                                                               amount=amount)
                        detalles.append(detalle_movimiento)
                        cont = cont + 1
                MovementDetail.objects.bulk_create(detalles, reference, self.object.order)
                return HttpResponseRedirect(reverse('almacen:detalle_movimiento', args=[self.object.pk]))
        except IntegrityError:
            messages.error(self.request, 'Error guardando la cotizacion.')

    def form_invalid(self, form, detalle_salida_formset):
        return self.render_to_response(self.get_context_data(form=form,
                                                             detalle_salida_formset=detalle_salida_formset))


class WarehouseUpdate(UpdateView):
    model = Warehouse
    template_name = 'almacen/almacen.html'
    form_class = WarehouseForm
    success_url = reverse_lazy('almacen:almacenes')


class OrderUpdate(UpdateView):
    template_name = 'almacen/pedido.html'
    form_class = OrderForm
    model = Order
    context_object_name = 'order'

    @method_decorator(requiere('almacen.change_order'))
    def dispatch(self, *args, **kwargs):
        order = self.get_object()
        if order.status == Order.STATUS.PEND:
            return super(OrderUpdate, self).dispatch(*args, **kwargs)
        else:
            return HttpResponseRedirect(reverse('seguridad:permiso_denegado'))

    def get_form_kwargs(self):
        kwargs = super(OrderUpdate, self).get_form_kwargs()
        kwargs['request'] = self.request
        return kwargs

    def get_initial(self):
        initial = super(OrderUpdate, self).get_initial()
        order = self.object
        initial['date'] = order.date.strftime('%d/%m/%Y')
        initial['notes'] = order.notes
        return initial

    def get_context_data(self, **kwargs):
        order = self.object
        detalles = OrderDetail.objects.filter(order=order).order_by('line_number')
        cant_detalles = detalles.count()
        context = super(OrderUpdate, self).get_context_data(**kwargs)
        context['order'] = order
        context['detalles'] = detalles
        context['cant_detalles'] = cant_detalles
        return context

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        if self.object.status == Order.STATUS.PEND:
            form_class = self.get_form_class()
            form = self.get_form(form_class)
            detalles = OrderDetail.objects.filter(order=self.object).order_by('line_number')
            detalles_data = []
            for detalle in detalles:
                d = {'code': detalle.product.code,
                     'name': detalle.product.description,
                     'unidad': detalle.product.unit_of_measure.code,
                     'quantity': detalle.quantity}
                detalles_data.append(d)
            detalle_pedido_formset = OrderDetailFormSet(initial=detalles_data)
            return self.render_to_response(self.get_context_data(form=form,
                                                                 detalle_pedido_formset=detalle_pedido_formset))

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        form_class = self.get_form_class()
        form = self.get_form(form_class)
        detalle_pedido_formset = OrderDetailFormSet(request.POST)
        if form.is_valid() and detalle_pedido_formset.is_valid():
            return self.form_valid(form, detalle_pedido_formset)
        else:
            return self.form_invalid(form, detalle_pedido_formset)

    def form_valid(self, form, detalle_pedido_formset):
        try:
            with transaction.atomic():
                self.object = form.save()
                OrderDetail.objects.filter(order=self.object).delete()
                detalles = []
                cont = 1
                for detalle_pedido_form in detalle_pedido_formset:
                    code = detalle_pedido_form.cleaned_data.get('code')
                    quantity = detalle_pedido_form.cleaned_data.get('quantity')
                    if code and quantity:
                        product = Product.objects.get(code=code)
                        detalles.append(OrderDetail(order=self.object,
                                                      line_number=cont,
                                                      product=product,
                                                      quantity=quantity))
                        cont = cont + 1
                OrderDetail.objects.bulk_create(detalles)
                return HttpResponseRedirect(reverse('almacen:order_detail', args=[self.object.code]))
        except IntegrityError:
            messages.error(self.request, 'Error guardando la cotizacion.')

    def form_invalid(self, form, detalle_pedido_formset):
        return self.render_to_response(self.get_context_data(form=form,
                                                             detalle_pedido_formset=detalle_pedido_formset))


class MovementListByProduct(FormView):
    template_name = 'almacen/movimientos_por_producto.html'
    form_class = ProductMovementForm

    def form_valid(self, form):
        data = form.cleaned_data
        desde = data['desde']
        hasta = data['hasta']
        warehouse = data['warehouse']
        product = Product.objects.get(code=data['product'])
        return self.obtener_movimientos(desde, hasta, warehouse, product)

    def obtener_movimientos(self, desde, hasta, warehouse, product):
        detalles = MovementDetail.objects.filter(movement__warehouse=warehouse,
                                                    product=product,
                                                    movement__operation_date__gte=desde,
                                                    movement__operation_date__lte=hasta).order_by(
            'movement__operation_date')
        wb = Workbook()
        ws = wb.active
        ws['B1'] = u'Product: ' + product.description
        ws.merge_cells('B1:I1')
        ws['B2'] = u'Almacén: ' + warehouse.description
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
            ws.cell(row=cont, column=2).value = str(detalle.movement)
            ws.cell(row=cont, column=3).value = str(detalle.movement.movement_type)
            if detalle.movement.reference is not None:
                ws.cell(row=cont, column=4).value = str(detalle.movement.reference)
            else:
                ws.cell(row=cont, column=4).value = ""
            if detalle.movement.order is not None:
                ws.cell(row=cont, column=5).value = str(detalle.movement.order)
            else:
                ws.cell(row=cont, column=5).value = ""
            ws.cell(row=cont, column=6).value = detalle.movement.operation_date.strftime('%d/%m/%Y %H : %M : %S')
            ws.cell(row=cont, column=7).value = detalle.quantity
            ws.cell(row=cont, column=8).value = detalle.price
            ws.cell(row=cont, column=9).value = detalle.amount
            cont = cont + 1
        nombre_archivo = "MovementListByProduct.xlsx"
        response = HttpResponse(content_type="application/ms-excel")
        contenido = "attachment; filename={0}".format(nombre_archivo)
        response["Content-Disposition"] = contenido
        wb.save(response)
        return response


class InboundCreate(CreateView):
    template_name = 'almacen/ingreso_almacen.html'
    form_class = MovementForm
    model = Movement
    context_object_name = 'movement'

    def get_initial(self):
        initial = super(InboundCreate, self).get_initial()
        initial['date'] = date.today().strftime('%d/%m/%Y')
        initial['total'] = 0
        return initial

    def get_form_kwargs(self):
        kwargs = super(InboundCreate, self).get_form_kwargs()
        kwargs['movement_type'] = 'I'
        return kwargs

    def get(self, request, *args, **kwargs):
        self.object = None
        cod_tipo_mov = 'I00'
        tipos_ingreso = MovementType.objects.filter(increases=True).exclude(code=cod_tipo_mov)
        if not tipos_ingreso:
            return HttpResponseRedirect(reverse('almacen:crear_tipo_movimiento'))
        almacenes = Warehouse.objects.all()
        cant_suministros = Product.objects.count()
        if almacenes.count() > 0:
            if cant_suministros > 0:
                form_class = self.get_form_class()
                form = self.get_form(form_class)
                detalle_ingreso_formset = InboundDetailFormSet()
                return self.render_to_response(self.get_context_data(form=form,
                                                                     detalle_ingreso_formset=detalle_ingreso_formset))
        return HttpResponseRedirect(reverse('almacen:tablero'))

    def post(self, request, *args, **kwargs):
        self.object = None
        form_class = self.get_form_class()
        form = self.get_form(form_class)
        detalle_ingreso_formset = InboundDetailFormSet(request.POST)
        if form.is_valid() and detalle_ingreso_formset.is_valid():
            return self.form_valid(form, detalle_ingreso_formset)
        else:
            return self.form_invalid(form, detalle_ingreso_formset)

    def form_valid(self, form, detalle_ingreso_formset):
        try:
            with transaction.atomic():
                self.object = form.save()
                reference = self.object.reference
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
                            purchase_order_detail = PurchaseOrderDetail.objects.get(pk=orden_compra)
                            detalle_movimiento = MovementDetail(purchase_order_detail=purchase_order_detail,
                                                                   line_number=cont,
                                                                   movement=self.object,
                                                                   product=Product.objects.get(pk=code),
                                                                   quantity=quantity,
                                                                   price=price,
                                                                   amount=amount)
                        except ObjectDoesNotExist:
                            detalle_movimiento = MovementDetail(line_number=cont,
                                                                   movement=self.object,
                                                                   product=Product.objects.get(pk=code),
                                                                   quantity=quantity,
                                                                   price=price,
                                                                   amount=amount)
                        detalles.append(detalle_movimiento)
                        cont = cont + 1
                MovementDetail.objects.bulk_create(detalles, reference, None)
                return HttpResponseRedirect(reverse('almacen:detalle_movimiento', args=[self.object.pk]))
        except IntegrityError:
            messages.error(self.request, 'Error guardando la cotizacion.')

    def form_invalid(self, form, detalle_ingreso_formset):
        return self.render_to_response(self.get_context_data(form=form,
                                                             detalle_ingreso_formset=detalle_ingreso_formset))


class OutboundCreate(CreateView):
    form_class = MovementForm
    template_name = "almacen/salida_almacen.html"
    model = Movement
    context_object_name = 'movement'

    def get_form_kwargs(self):
        kwargs = super(OutboundCreate, self).get_form_kwargs()
        kwargs['movement_type'] = 'S'
        return kwargs

    def get_initial(self):
        initial = super(OutboundCreate, self).get_initial()
        initial['total'] = 0
        initial['date'] = date.today().strftime('%d/%m/%Y')
        return initial

    def get(self, request, *args, **kwargs):
        self.object = None
        tipos_salida = MovementType.objects.filter(increases=False)
        if not tipos_salida:
            return HttpResponseRedirect(reverse('almacen:crear_tipo_movimiento'))
        almacenes = Warehouse.objects.filter()
        if not almacenes:
            return HttpResponseRedirect(reverse('almacen:crear_almacen'))
        else:
            form_class = self.get_form_class()
            form = self.get_form(form_class)
            detalle_salida_formset = OutboundDetailFormSet()
            return self.render_to_response(self.get_context_data(form=form,
                                                                 detalle_salida_formset=detalle_salida_formset))

    def post(self, request, *args, **kwargs):
        self.object = None
        form_class = self.get_form_class()
        form = self.get_form(form_class)
        detalle_salida_formset = OutboundDetailFormSet(request.POST)
        if form.is_valid() and detalle_salida_formset.is_valid():
            return self.form_valid(form, detalle_salida_formset)
        else:
            return self.form_invalid(form, detalle_salida_formset)

    def form_valid(self, form, detalle_salida_formset):
        try:
            with transaction.atomic():
                self.object = form.save()
                reference = self.object.reference
                detalles = []
                cont = 1
                for detalle_salida_form in detalle_salida_formset:
                    code = detalle_salida_form.cleaned_data.get('code')
                    quantity = detalle_salida_form.cleaned_data.get('quantity')
                    price = detalle_salida_form.cleaned_data.get('price')
                    amount = detalle_salida_form.cleaned_data.get('amount')
                    if quantity and price and amount:
                        detalle_movimiento = MovementDetail(line_number=cont,
                                                               movement=self.object,
                                                               product=Product.objects.get(pk=code),
                                                               quantity=quantity,
                                                               price=price,
                                                               amount=amount)
                        detalles.append(detalle_movimiento)
                        cont = cont + 1
                MovementDetail.objects.bulk_create(detalles, reference, None)
                return HttpResponseRedirect(reverse('almacen:detalle_movimiento', args=[self.object.pk]))
        except IntegrityError:
            messages.error(self.request, 'Error guardando la cotizacion.')

    def form_invalid(self, form, detalle_salida_formset):
        return self.render_to_response(self.get_context_data(form=form,
                                                             detalle_salida_formset=detalle_salida_formset))


class WarehouseExcelReport(TemplateView):

    def get(self, request, *args, **kwargs):
        almacenes = Warehouse.objects.filter(is_active=True).order_by('code')
        wb = Workbook()
        ws = wb.active
        ws['B1'] = 'REPORTE DE ALMACENES'
        ws.merge_cells('B1:J1')
        ws['B3'] = 'CODIGO'
        ws['C3'] = 'DESCRIPCIÓN'
        cont = 4
        for warehouse in almacenes:
            ws.cell(row=cont, column=2).value = warehouse.code
            ws.cell(row=cont, column=3).value = warehouse.description
            cont = cont + 1
        nombre_archivo = "WarehouseList.xlsx"
        response = HttpResponse(content_type="application/ms-excel")
        contenido = "attachment; filename={0}".format(nombre_archivo)
        response["Content-Disposition"] = contenido
        wb.save(response)
        return response


class MovementTypeExcelReport(TemplateView):

    def get(self, request, *args, **kwargs):
        tipos = MovementType.objects.filter(is_active=True).order_by('code')
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


class ReportResponseMixin(object):
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


class KardexProductReport(ReportResponseMixin, FormView):
    template_name = 'almacen/reporte_kardex_producto.html'
    form_class = KardexProductForm

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
        product = Product.objects.get(code=cod_prod)
        desde = data.get('desde')
        hasta = data.get('hasta')
        warehouse = data.get('almacenes')
        formato_sunat = data.get('formato_sunat')
        formatos = data.get('formatos')

        if formatos == 'XLS':
            metodo, nombre_archivo = self.REPORTES_EXCEL[self._formato_sunat(formato_sunat)]
            excel = getattr(KardexExcelReport(), metodo)(product, desde, hasta, warehouse)
            return self._respuesta_excel(excel, nombre_archivo)
        if formatos == 'PDF':
            clave = self._formato_sunat(formato_sunat)
            if clave not in self.REPORTES_PDF:
                return HttpResponse('Este reporte no esta disponible en PDF para la combinacion elegida.',
                                    status=404)
            metodo, nombre_archivo = self.REPORTES_PDF[clave]
            reporte = KardexPdfReport('A4', desde, hasta, warehouse, False)
            return self._respuesta_pdf(getattr(reporte, metodo)(product), nombre_archivo)
        return HttpResponse('Formato no soportado.', status=400)


class KardexReport(ReportResponseMixin, FormView):
    template_name = 'almacen/reporte_kardex.html'
    form_class = KardexProductForm

    def form_valid(self, form):
        data = form.cleaned_data
        desde = data.get('desde')
        hasta = data['hasta']
        warehouse = data.get('almacenes')
        formato_sunat = data.get('formato_sunat')
        formatos = data.get('formatos')
        consolidado = data['consolidado']

        clave = self._clave_reporte(consolidado, formato_sunat)
        if formatos == 'XLS':
            return self._reporte_excel(clave, desde, hasta, warehouse)
        if formatos == 'PDF':
            return self._reporte_pdf(clave, desde, hasta, warehouse)
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

    def _reporte_pdf(self, clave, desde, hasta, warehouse):
        if clave not in self.REPORTES_PDF:
            return HttpResponse('Este reporte no esta disponible en PDF para la combinacion elegida.', status=404)
        metodo, agrupado, nombre_archivo = self.REPORTES_PDF[clave]
        reporte = KardexPdfReport('A4', desde, hasta, warehouse, agrupado)
        return self._respuesta_pdf(getattr(reporte, metodo)(), nombre_archivo)

    def _reporte_excel(self, clave, desde, hasta, warehouse):
        metodo, nombre_archivo = self.REPORTES_EXCEL[clave]
        reporte = KardexExcelReport()
        return self._respuesta_excel(getattr(reporte, metodo)(desde, hasta, warehouse), nombre_archivo)


class PriceReprocess(FormView):
    template_name = 'almacen/reproceso_precio.html'
    form_class = PriceReprocessForm

    def reprocesar_precio_producto(self, product, warehouse, desde):
        detalles = Kardex.objects.filter(product=product,
                                         warehouse=warehouse,
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
            tipo_mov = detalle.movement.movement_type
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
        warehouse = data['warehouse']
        seleccion = data['seleccion']
        if seleccion == 'P':
            cod_prod = data['product']
            product = Product.objects.get(code=cod_prod)
            self.reprocesar_precio_producto(product, warehouse, desde)
        else:
            listado_kardex = Kardex.objects.filter(warehouse=warehouse).order_by('product').distinct('product__code')
            for kardex in listado_kardex:
                self.reprocesar_precio_producto(kardex.product, warehouse, desde)
        return HttpResponseRedirect(reverse('almacen:tablero'))


class ProductStock(FormView):
    form_class = StockQueryForm
    template_name = 'almacen/stock_productos.html'

    def get_initial(self):
        initial = super(ProductStock, self).get_initial()
        initial['desde'] = date.today().strftime('%d/%m/%Y')
        return initial

    def form_valid(self, form):
        data = form.cleaned_data
        warehouse = data['warehouse']
        description = data['description']
        productos = list(Product.objects.filter(description__icontains=description)
                         .select_related('unit_of_measure').order_by('description'))
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
        ultimos = Kardex.ultimos_por_producto(productos, warehouse=warehouse)
        for product in productos:
            kardex = ultimos.get(product.pk)
            code = product.code
            description = product.description
            if kardex is None:
                unit_of_measure = product.unit_of_measure.code
                stock = 0
                price = 0
                amount = 0
            else:
                unit_of_measure = product.unit_of_measure.description
                stock = kardex.total_quantity
                price = kardex.total_price
                amount = kardex.total_amount
            ws.cell(row=cont, column=2).value = code
            ws.cell(row=cont, column=3).value = description
            ws.cell(row=cont, column=4).value = unit_of_measure
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


class ProductStockList(SoloAjaxMixin, TemplateView):

    parametros_requeridos = ('description', 'warehouse')

    def get(self, request, *args, **kwargs):
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            description = request.GET['description']
            warehouse = request.GET['warehouse']
            lista_productos = []
            productos = list(Product.objects.filter(description__icontains=description)
                             .select_related('unit_of_measure').order_by('description'))
            ultimos = Kardex.ultimos_por_producto(productos, warehouse__pk=warehouse)
            for product in productos:
                kardex = ultimos.get(product.pk)
                kardex_json = {}
                kardex_json['code'] = product.code
                kardex_json['label'] = product.description
                kardex_json['unidad'] = product.unit_of_measure.code
                kardex_json['stock'] = kardex.total_quantity if kardex else 0
                lista_productos.append(kardex_json)
            data = simplejson.dumps(lista_productos)
            return HttpResponse(data, 'application/json')


class MovementExcelReport(FormView):
    form_class = MovementReportForm
    template_name = "almacen/reporte_movimientos.html"

    def form_valid(self, form):
        data = form.cleaned_data
        tipo_busqueda = data['tipo_busqueda']
        p_almacen = data['almacenes']
        p_tipo_movimiento = data['tipos_movimiento']
        warehouse = Warehouse.objects.get(code=p_almacen)
        movement_type = MovementType.objects.get(code=p_tipo_movimiento)
        wb = Workbook()
        ws = wb.active
        if tipo_busqueda == 'F':
            start_date = data['desde']
            fecha_final = data['hasta']
            ws['B1'] = 'REPORTE DE MOVIMIENTOS POR FECHA'
            ws.merge_cells('B1:H1')
            ws['B2'] = 'ALMACEN: ' + warehouse.description
            ws.merge_cells('B2:D2')
            ws['E2'] = 'TIPO DE MOVIMIENTO: ' + movement_type.description
            ws.merge_cells('E2:H2')
            ws['B3'] = 'DESDE'
            ws['C3'] = start_date
            ws['C3'].number_format = 'dd/mm/yyyy'
            ws['D3'] = 'HASTA'
            ws['E3'] = fecha_final
            ws['F3'].number_format = 'dd/mm/yyyy'
            movimientos = Movement.objects.filter(operation_date__range=[start_date, fecha_final],
                                                    movement_type=movement_type, warehouse=warehouse)
        elif tipo_busqueda == 'M':
            month = data['month'].strip()
            year = data['year'].strip()
            ws['B1'] = 'REPORTE DE MOVIMIENTOS POR MES'
            ws.merge_cells('B1:H1')
            ws['B2'] = 'ALMACEN: ' + warehouse.description
            ws.merge_cells('B2:D2')
            ws['E2'] = 'TIPO DE MOVIMIENTO: ' + movement_type.description
            ws.merge_cells('E2:H2')
            ws['B3'] = 'MES'
            ws['C3'] = month
            ws['D3'] = 'AÑO'
            ws['E3'] = year
            movimientos = Movement.objects.filter(operation_date__month=month,
                                                    operation_date__year=year,
                                                    movement_type=movement_type,
                                                    warehouse=warehouse)
        elif tipo_busqueda == 'A':
            year = data['year'].strip()
            ws['B1'] = 'REPORTE DE MOVIMIENTOS POR AÑO'
            ws.merge_cells('B1:H1')
            ws['B2'] = 'ALMACEN: ' + warehouse.description
            ws.merge_cells('B2:D2')
            ws['E2'] = 'TIPO DE MOVIMIENTO: ' + movement_type.description
            ws.merge_cells('E2:H2')
            ws['B3'] = 'AÑO'
            ws['C3'] = year
            movimientos = Movement.objects.filter(operation_date__year=year,
                                                    movement_type=movement_type,
                                                    warehouse=warehouse)
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
        for movement in movimientos:
            ws.cell(row=cont, column=2).value = movement.movement_id
            try:
                ws.cell(row=cont, column=3).value = movement.document_type.description
            except ObjectDoesNotExist:
                ws.cell(row=cont, column=3).value = '--'
            ws.cell(row=cont, column=4).value = movement.series
            ws.cell(row=cont, column=5).value = movement.number
            ws.cell(row=cont, column=6).value = movement.operation_date
            ws.cell(row=cont, column=6).number_format = 'dd/mm/yyyy hh:mm:ss'
            ws.cell(row=cont, column=7).value = movement.notes
            ws.cell(row=cont, column=8).value = movement.created
            ws.cell(row=cont, column=8).number_format = 'dd/mm/yyyy hh:mm:ss'
            ws.cell(row=cont, column=9).value = movement.status
            cont = cont + 1
        nombre_archivo = "ReporteMovimientosPorFecha.xlsx"
        response = HttpResponse(content_type="application/ms-excel")
        contenido = "attachment; filename={0}".format(nombre_archivo)
        response["Content-Disposition"] = contenido
        wb.save(response)
        return response


class MovementExcelReportByDate(View):

    def get(self, request, *args, **kwargs):
        p_start_date = kwargs['start_date']
        p_fecha_final = kwargs['end_date']
        p_almacen = kwargs['warehouse']
        p_tipo_movimiento = kwargs['movement_type']
        anio = int(p_start_date[6:])
        month = int(p_start_date[3:5])
        dia = int(p_start_date[0:2])
        start_date = timezone.make_aware(datetime.datetime(anio, month, dia, 23, 59, 59))
        anio = int(p_fecha_final[6:])
        month = int(p_fecha_final[3:5])
        dia = int(p_fecha_final[0:2])
        fecha_final = timezone.make_aware(datetime.datetime(anio, month, dia, 23, 59, 59))
        warehouse = Warehouse.objects.get(code=p_almacen)
        movement_type = MovementType.objects.get(code=p_tipo_movimiento)
        wb = Workbook()
        ws = wb.active
        ws['B1'] = 'REPORTE DE MOVIMIENTOS POR FECHA'
        ws.merge_cells('B1:H1')
        ws['B2'] = 'ALMACEN: ' + warehouse.description
        ws.merge_cells('B2:D2')
        ws['E2'] = 'TIPO DE MOVIMIENTO: ' + movement_type.description
        ws.merge_cells('E2:H2')
        ws['B3'] = 'DESDE'
        ws['C3'] = p_start_date
        ws['C3'].number_format = 'dd/mm/yyyy'
        ws['D3'] = 'HASTA'
        ws['E3'] = p_fecha_final
        ws['F3'].number_format = 'dd/mm/yyyy'
        movimientos = Movement.objects.filter(operation_date__range=[start_date, fecha_final],
                                                movement_type=movement_type, warehouse=warehouse)
        ws['B5'] = 'ID_MOVIMIENTO'
        ws['C5'] = 'TIPO_DOCUMENTO'
        ws['D5'] = 'SERIE'
        ws['E5'] = 'NUMERO'
        ws['F5'] = 'FECHA_OPERACION'
        ws['G5'] = 'OBSERVACION'
        ws['H5'] = 'FECHA_CREACION'
        cont = 6
        for movement in movimientos:
            ws.cell(row=cont, column=2).value = movement.movement_id
            ws.cell(row=cont, column=3).value = movement.document_type
            ws.cell(row=cont, column=4).value = movement.series
            ws.cell(row=cont, column=5).value = movement.number
            ws.cell(row=cont, column=6).value = movement.operation_date
            ws.cell(row=cont, column=6).number_format = 'dd/mm/yyyy hh:mm:ss'
            ws.cell(row=cont, column=7).value = movement.observacion
            ws.cell(row=cont, column=8).value = movement.created
            ws.cell(row=cont, column=8).number_format = 'dd/mm/yyyy hh:mm:ss'
            cont = cont + 1
        nombre_archivo = "ReporteMovimientosPorFecha.xlsx"
        response = HttpResponse(content_type="application/ms-excel")
        contenido = "attachment; filename={0}".format(nombre_archivo)
        response["Content-Disposition"] = contenido
        wb.save(response)
        return response


class MovementPdfReport(View):

    def get(self, request, *args, **kwargs):
        movement_id = kwargs['movement_id']
        movement = Movement.objects.get(pk=movement_id)
        response = HttpResponse(content_type='application/pdf')
        reporte = MovementReport('A4', movement)
        pdf = reporte.imprimir()
        response.write(pdf)
        return response


class ProductPdfReport(View):

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
        allclientes = [(p.code, p.description, p.precio_mercado, p.grupo_suministros) for p in Product.objects.all()]

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


class VerifyDocumentRequired(SoloAjaxMixin, TemplateView):

    parametros_requeridos = ('tipo',)

    def get(self, request, *args, **kwargs):
        tipo = request.GET['tipo']
        movement_type = MovementType.objects.get(pk=tipo)
        json_object = {'solicita_documento': movement_type.solicita_documento}
        return JsonResponse(json_object)


class VerifyReferenceRequired(SoloAjaxMixin, TemplateView):

    parametros_requeridos = ('tipo',)

    def get(self, request, *args, **kwargs):
        tipo = request.GET['tipo']
        movement_type = MovementType.objects.get(pk=tipo)
        json_object = {'requires_reference': movement_type.requires_reference}
        return JsonResponse(json_object)


class VerifyStockForOrder(SoloAjaxMixin, TemplateView):

    parametros_requeridos = ('warehouse', 'order')

    def get(self, request, *args, **kwargs):
        warehouse = request.GET['warehouse']
        order = request.GET['order']
        detalles = list(OrderDetail.objects.filter(order__code=order,
                                                     status=OrderDetail.STATUS.PEND)
                        .select_related('product__unit_of_measure').order_by('line_number'))
        ultimos = Kardex.ultimos_por_producto([detalle.product for detalle in detalles],
                                              warehouse__code=warehouse)
        lista_detalles = []
        for detalle in detalles:
            control_producto = ultimos.get(detalle.product_id)
            try:
                stock = control_producto.total_quantity
                price = control_producto.total_amount / stock
            except (AttributeError, ZeroDivisionError):
                stock = 0
                price = 0
            if stock != 0:
                det = {}
                det['order'] = detalle.id
                det['code'] = detalle.product.code
                det['name'] = detalle.product.description
                det['unidad'] = detalle.product.unit_of_measure.description
                quantity = detalle.quantity - detalle.served_quantity
                if quantity > stock:
                    quantity = stock
                amount = round(quantity * price, 5)
                det['quantity'] = quantity
                det['price'] = round(price, 5)
                det['amount'] = amount
                lista_detalles.append(det)
        formset = OutboundDetailFormSet(initial=lista_detalles)
        lista_json = []
        for form in formset:
            detalle_json = {}
            detalle_json['order'] = str(form['order'])
            detalle_json['code'] = str(form['code'])
            detalle_json['name'] = str(form['name'])
            detalle_json['quantity'] = str(form['quantity'])
            detalle_json['price'] = str(form['price'])
            detalle_json['unidad'] = str(form['unidad'])
            detalle_json['amount'] = str(form['amount'])
            lista_json.append(detalle_json)
        data = json.dumps(lista_json)
        return HttpResponse(data, 'application/json')


class Inventory(ReportResponseMixin, FormView):
    form_class = InventoryQueryForm
    template_name = 'almacen/inventario.html'

    def get_initial(self):
        initial = super(Inventory, self).get_initial()
        initial['desde'] = date.today().strftime('%d/%m/%Y')
        return initial

    def form_valid(self, form):
        return self._respuesta_excel(reporte_inventario(form.cleaned_data['desde']),
                                     'ReporteInventario.xlsx')
