# -*- coding: utf-8 -*- 
from django.utils import timezone
from django.shortcuts import render

from warehouse.models import Warehouse, Movement, Kardex, MovementType, MovementDetail, WarehouseProductControl,\
    Order, OrderDetail
from django.http import HttpResponse, HttpResponseRedirect
from django.urls import reverse, reverse_lazy
import datetime
from django.views.generic import TemplateView, FormView, View, ListView
from warehouse.forms import WarehouseForm, MovementTypeForm, MovementReportForm,\
    KardexProductForm, InitialInventoryImportForm, MovementForm,\
    InboundDetailFormSet, OutboundDetailFormSet, OrderForm, OrderDetailFormSet,\
    OrderApprovalForm, PriceReprocessForm,\
    ProductMovementForm, StockQueryForm, InventoryQueryForm
from decimal import Decimal, InvalidOperation
from io import BytesIO
from reportlab.platypus import SimpleDocTemplate, Paragraph, TableStyle
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.platypus import Table
from django.http import JsonResponse
from purchases.models import PurchaseOrderDetail
from openpyxl import Workbook
import simplejson
import json
from django.views.generic.detail import DetailView
from django.views.generic.edit import UpdateView, CreateView
from administration.models import Position
import locale
from accounting.models import DocumentType
from accounting.forms import UploadForm
from security.permissions import requires
from django.utils.decorators import method_decorator
from django.db.models import Q
from django.db import transaction, IntegrityError
from django.core.exceptions import ObjectDoesNotExist
from django.contrib import messages
from products.models import Product
from warehouse.mail import order_creation_mail
from warehouse.reports import MovementReport, KardexPdfReport, KardexExcelReport, inventory_report
from tambox.config import logistics
from tambox.views import CsvImportMixin, AjaxOnlyMixin
from datetime import date

locale.setlocale(locale.LC_ALL, "")


class Dashboard(View):

    def get(self, request, *args, **kwargs):
        inventory_initial_movement_code = 'I00'
        purchase_inbound_code = 'I01'
        order_outbound_code = 'S01'
        notification_list = []
        warehouse_count = Warehouse.objects.count()
        inbound_movement_type_count = MovementType.objects.filter(increases=True).exclude(
            code=inventory_initial_movement_code).count()
        outbound_movement_type_count = MovementType.objects.filter(increases=False).count()
        movement_type, creado = MovementType.objects.get_or_create(code=inventory_initial_movement_code,
                                                                       defaults={'description': 'INVENTARIO INICIAL',
                                                                                 'sunat_code': '16',
                                                                                 'increases': True,
                                                                                 'is_active': True})
        if creado:
            notification_list.append("Se ha creado el tipo de movimiento inventario inicial")
        movement_type, creado = MovementType.objects.get_or_create(code=purchase_inbound_code,
                                                                       defaults={'description': 'INGRESO POR COMPRA',
                                                                                 'sunat_code': '02',
                                                                                 'increases': True,
                                                                                 'requires_reference': True,
                                                                                 'is_active': True})
        if creado:
            notification_list.append("Se ha creado el tipo de movimiento Ingreso por Compra")
        movement_type, creado = MovementType.objects.get_or_create(code=order_outbound_code,
                                                                       defaults={'description': 'SALIDA POR PEDIDO',
                                                                                 'sunat_code': '10',
                                                                                 'increases': False,
                                                                                 'requires_reference': True,
                                                                                 'is_active': True})
        inventario_inicial = Movement.objects.filter(movement_type__code=inventory_initial_movement_code).count()
        if creado:
            notification_list.append("Se ha creado el tipo de movimiento Salida por Pedido")
        if warehouse_count == 0:
            notification_list.append("No se ha creado ningún almacén")
        if inbound_movement_type_count == 0:
            notification_list.append("No se ha creado ningún tipo de movimiento de ingreso")
        if outbound_movement_type_count == 0:
            notification_list.append("No se ha creado ningún tipo de movimiento de salida")
        if inventario_inicial == 0:
            notification_list.append("No se ha realizado el inventario inicial")
        context = {'notifications': notification_list}
        return render(request, 'warehouse/warehouse_dashboard.html', context)


class OrderApprove(CreateView):
    form_class = OrderApprovalForm
    template_name = 'warehouse/order_approve.html'
    model = Movement

    @method_decorator(requires('warehouse.aprobar_pedido'))
    def dispatch(self, *args, **kwargs):
        self.code = kwargs['code']
        return super(OrderApprove, self).dispatch(*args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super(OrderApprove, self).get_form_kwargs()
        kwargs['request'] = self.request
        return kwargs

    def get_initial(self):
        initial = super(OrderApprove, self).get_initial()
        initial['order_code'] = self.code
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
            return HttpResponseRedirect(reverse('administration:worker_create'))
        try:
            positions = worker.positions.all().filter(is_active=True)
            if worker.signature == '':
                return HttpResponseRedirect(reverse('administration:worker_update', args=[worker.pk]))
            if positions[0].is_leadership and positions[0].office == logistics():
                form_class = self.get_form_class()
                form = self.get_form(form_class)
                details = OrderDetail.objects.filter(order=order, status=OrderDetail.STATUS.PEND)
                details_data = []
                for detail in details:
                    d = {'order': detail.id,
                         'code': detail.product.code,
                         'name': detail.product.description,
                         'unit': detail.product.unit_of_measure.code,
                         'quantity': detail.quantity
                         }
                    details_data.append(d)
                outbound_detail_formset = OutboundDetailFormSet(initial=details_data)
                return self.render_to_response(self.get_context_data(form=form,
                                                                     outbound_detail_formset=outbound_detail_formset))
            else:
                return HttpResponseRedirect(reverse('security:permission_denied'))
        except (IndexError, ObjectDoesNotExist):
            return HttpResponseRedirect(reverse('security:permission_denied'))

    def post(self, request, *args, **kwargs):
        self.object = None
        form_class = self.get_form_class()
        form = self.get_form(form_class)
        outbound_detail_formset = OutboundDetailFormSet(request.POST)
        if form.is_valid() and outbound_detail_formset.is_valid():
            return self.form_valid(form, outbound_detail_formset)
        else:
            return self.form_invalid(form, outbound_detail_formset)

    def form_valid(self, form, outbound_detail_formset):
        try:
            with transaction.atomic():
                self.object = form.save()
                order = self.object.order
                details = []
                cont = 1
                for outbound_detail_form in outbound_detail_formset:
                    order_detail = outbound_detail_form.cleaned_data.get('order')
                    code = outbound_detail_form.cleaned_data.get('code')
                    quantity = outbound_detail_form.cleaned_data.get('quantity')
                    price = outbound_detail_form.cleaned_data.get('price')
                    amount = outbound_detail_form.cleaned_data.get('amount')
                    if quantity and price and amount:
                        movement_detail = MovementDetail(line_number=cont,
                                                               movement=self.object,
                                                               product=Product.objects.get(pk=code),
                                                               order_detail=OrderDetail.objects.get(
                                                                   pk=order_detail),
                                                               quantity=quantity,
                                                               price=price,
                                                               amount=amount)
                        details.append(movement_detail)
                        cont = cont + 1
                MovementDetail.objects.bulk_create(details, None, order)
                return HttpResponseRedirect(reverse('warehouse:movement_detail_view', args=[self.object.movement_id]))
        except IntegrityError:
            messages.error(self.request, 'Error guardando la cotizacion.')
            return self.form_invalid(form, outbound_detail_formset)

    def form_invalid(self, form, outbound_detail_formset):
        return self.render_to_response(self.get_context_data(form=form,
                                                             outbound_detail_formset=outbound_detail_formset))


class ProductWarehouseSearch(AjaxOnlyMixin, TemplateView):

    required_params = ('description', 'warehouse')

    def get(self, request, *args, **kwargs):
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            product_list = []
            description = request.GET['description']
            warehouse = request.GET['warehouse']
            ids = list(Kardex.objects.filter(product__description__icontains=description,
                                             warehouse__id=warehouse)
                       .order_by('product_id').distinct('product_id')
                       .values_list('product_id', flat=True)[:20])
            last_records = Kardex.last_by_product(ids, warehouse__id=warehouse)
            for product_id in ids:
                control = last_records[product_id]
                product_json = {}
                product_json['label'] = control.product.description
                product_json['code'] = control.product.code
                product_json['description'] = control.product.description
                product_json['unit'] = control.product.unit_of_measure.description
                try:
                    price = round(control.total_amount / control.total_quantity, 5)
                except (TypeError, ZeroDivisionError):
                    price = 0
                product_json['price'] = str(price)
                product_list.append(product_json)
            data = json.dumps(product_list)
            return HttpResponse(data, 'application/json')


class WarehouseImport(CsvImportMixin, FormView):
    template_name = 'warehouse/warehouse_upload.html'
    form_class = UploadForm
    success_url = reverse_lazy('warehouse:warehouse_list')

    def process_row(self, row):
        Warehouse.objects.create(code=row[0],
                               description=row[1])


class InitialInventoryImport(CsvImportMixin, FormView):
    template_name = 'warehouse/initial_stock_upload.html'
    form_class = InitialInventoryImportForm

    def get_datetime(self, r_date, r_hora):
        r_hora = r_hora.replace(" ", "")
        year = int(r_date[6:])
        month = int(r_date[3:5])
        dia = int(r_date[0:2])
        horas = int(r_hora[0:2])
        minutos = int(r_hora[3:5])
        # segundos = int(r_hora[6:8])
        date = timezone.make_aware(datetime.datetime(year, month, dia, horas, minutos))
        return date

    def form_valid(self, form):
        data = form.cleaned_data
        movement_type = MovementType.objects.filter(code='I00').first()
        document_type = DocumentType.objects.filter(sunat_code='PEC').first()
        missing = []
        if movement_type is None:
            missing.append('Falta el tipo de movimiento "I00" (INVENTARIO INICIAL): '
                             'entra al tablero de Almacen para crearlo y vuelve a cargar el archivo.')
        if document_type is None:
            missing.append('Falta el tipo de documento "PEC" (PECOSA): '
                             'entra al tablero de Contabilidad para crearlo y vuelve a cargar el file.')
        if missing:
            return self.render_to_response(self.get_context_data(form=form,
                                                                 notifications=missing))
        self.operation_date = self.get_datetime(data['date'], data['time'])
        self.cont_detalles = 1
        self.details = []
        with transaction.atomic():
            self.movement = Movement.objects.create(movement_type=movement_type,
                                                        document_type=document_type,
                                                        warehouse=data['warehouses'],
                                                        operation_date=self.operation_date,
                                                        notes='INVENTARIO INICIAL',
                                                        series='SALDO',
                                                        number='INICIAL')
            response = super(InitialInventoryImport, self).form_valid(form)
            MovementDetail.objects.bulk_create(self.details, None, None)
            self.movement.save()
        return response

    def process_row(self, row):
        try:
            product = Product.objects.get(description=row[0].strip())
            quantity = Decimal(row[1])
            try:
                price = Decimal(row[2])
            except InvalidOperation:
                price = ''
            try:
                amount = Decimal(row[3])
            except InvalidOperation:
                amount = ''
            if price == '':
                try:
                    price = amount / quantity
                except (InvalidOperation, ZeroDivisionError):
                    price = 0
            if amount == '':
                amount = quantity * price
            self.details.append(MovementDetail(line_number=self.cont_detalles,
                                                  movement=self.movement,
                                                  product=product,
                                                  quantity=quantity,
                                                  price=price,
                                                  amount=amount))
            self.cont_detalles = self.cont_detalles + 1
        except Product.DoesNotExist:
            pass

    def get_success_url(self):
        return reverse('warehouse:movement_detail_view', args=[self.movement.movement_id])


class MovementTypeCreate(CreateView):
    template_name = 'warehouse/movement_type_form.html'
    form_class = MovementTypeForm
    success_url = reverse_lazy('warehouse:movement_type_list')

    @method_decorator(requires('warehouse.add_movementtype'))
    def dispatch(self, *args, **kwargs):
        return super(MovementTypeCreate, self).dispatch(*args, **kwargs)

    def get_success_url(self):
        return reverse('warehouse:movement_type_detail', args=[self.object.pk])


class WarehouseCreate(FormView):
    template_name = 'warehouse/warehouse_form.html'
    form_class = WarehouseForm
    success_url = reverse_lazy('warehouse:warehouse_list')

    def form_valid(self, form):
        form.save()
        return super(WarehouseCreate, self).form_valid(form)




class OutboundDetailCreate(AjaxOnlyMixin, TemplateView):

    def get(self, request, *args, **kwargs):
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            detail_list = []
            det = {}
            det['code'] = ''
            det['name'] = ''
            det['quantity'] = '0'
            det['price'] = '0'
            det['unit'] = ''
            det['amount'] = '0'
            detail_list.append(det)
            formset = OutboundDetailFormSet(initial=detail_list)
            json_list = []
            for form in formset:
                detail_json = {}
                detail_json['code'] = str(form['code'])
                detail_json['name'] = str(form['name'])
                detail_json['quantity'] = str(form['quantity'])
                detail_json['price'] = str(form['price'])
                detail_json['unit'] = str(form['unit'])
                detail_json['amount'] = str(form['amount'])
                json_list.append(detail_json)
            data = json.dumps(json_list)
            return HttpResponse(data, 'application/json')


class OrderDetailCreate(AjaxOnlyMixin, TemplateView):

    def get(self, request, *args, **kwargs):
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            detail_list = []
            det = {}
            det['code'] = ''
            det['name'] = ''
            det['quantity'] = '0'
            det['unit'] = ''
            detail_list.append(det)
            formset = OrderDetailFormSet(initial=detail_list)
            json_list = []
            for form in formset:
                detail_json = {}
                detail_json['code'] = str(form['code'])
                detail_json['name'] = str(form['name'])
                detail_json['quantity'] = str(form['quantity'])
                detail_json['unit'] = str(form['unit'])
                json_list.append(detail_json)
            data = json.dumps(json_list)
            return HttpResponse(data, 'application/json')


class InboundDetailCreate(AjaxOnlyMixin, TemplateView):

    def get(self, request, *args, **kwargs):
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            detail_list = []
            det = {}
            det['purchase_order'] = '0'
            det['code'] = ''
            det['name'] = ''
            det['quantity'] = '0'
            det['price'] = '0'
            det['unit'] = ''
            det['amount'] = '0'
            detail_list.append(det)
            formset = InboundDetailFormSet(initial=detail_list)
            json_list = []
            for form in formset:
                detail_json = {}
                detail_json['purchase_order'] = str(form['purchase_order'])
                detail_json['code'] = str(form['code'])
                detail_json['name'] = str(form['name'])
                detail_json['quantity'] = str(form['quantity'])
                detail_json['price'] = str(form['price'])
                detail_json['unit'] = str(form['unit'])
                detail_json['amount'] = str(form['amount'])
                json_list.append(detail_json)
            data = json.dumps(json_list)
            return HttpResponse(data, 'application/json')


class OrderCreate(CreateView):
    template_name = 'warehouse/order_form.html'
    form_class = OrderForm
    model = Order
    context_object_name = 'order'

    @method_decorator(requires('warehouse.add_order'))
    def dispatch(self, *args, **kwargs):
        try:
            worker = self.request.user.worker
        except ObjectDoesNotExist:
            return HttpResponseRedirect(reverse('administration:worker_create'))
        if worker.signature == '':
            return HttpResponseRedirect(reverse('administration:worker_update', args=[worker.pk]))
        position = worker.position
        if position is None:
            return HttpResponseRedirect(reverse('administration:position_create'))
        if position.is_leadership or position.is_assistant:
            return super(OrderCreate, self).dispatch(*args, **kwargs)
        else:
            return HttpResponseRedirect(reverse('security:permission_denied'))

    def get(self, request, *args, **kwargs):
        self.object = None
        form_class = self.get_form_class()
        form = self.get_form(form_class)
        order_detail_formset = OrderDetailFormSet()
        return self.render_to_response(self.get_context_data(form=form,
                                                             order_detail_formset=order_detail_formset))

    def get_form_kwargs(self):
        kwargs = super(OrderCreate, self).get_form_kwargs()
        kwargs['request'] = self.request
        return kwargs

    def post(self, request, *args, **kwargs):
        self.object = None
        form_class = self.get_form_class()
        form = self.get_form(form_class)
        order_detail_formset = OrderDetailFormSet(request.POST)
        if form.is_valid() and order_detail_formset.is_valid():
            return self.form_valid(form, order_detail_formset)
        else:
            return self.form_invalid(form, order_detail_formset)

    def form_valid(self, form, order_detail_formset):
        try:
            with transaction.atomic():
                self.object = form.save()
                details = []
                cont = 1
                for order_detail_form in order_detail_formset:
                    code = order_detail_form.cleaned_data.get('code')
                    quantity = order_detail_form.cleaned_data.get('quantity')
                    if code and quantity:
                        product = Product.objects.get(code=code)
                        details.append(OrderDetail(order=self.object,
                                                      line_number=cont,
                                                      product=product,
                                                      quantity=quantity))
                        cont = cont + 1
                OrderDetail.objects.bulk_create(details)
                logistics_boss_position = Position.objects.get(office=logistics(), is_leadership=True, is_active=True)
                logistics_boss = logistics_boss_position.worker
                destinatario = logistics_boss.user.email
                order_creation_mail(destinatario, self.object)
                return HttpResponseRedirect(reverse('warehouse:order_detail', args=[self.object.pk]))
        except IntegrityError:
            messages.error(self.request, 'Error guardando el pedido.')

    def form_invalid(self, form, order_detail_formset):
        return self.render_to_response(self.get_context_data(form=form,
                                                             order_detail_formset=order_detail_formset))


class StockQuery(AjaxOnlyMixin, TemplateView):

    required_params = ('warehouse', 'code')
    def get(self, request, *args, **kwargs):
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            warehouse = request.GET['warehouse']
            code = request.GET['code']
            product_control = Kardex.objects.filter(product__code=code,
                                                     warehouse__id=warehouse).latest('operation_date')
            product_json = {}
            product_json['stock'] = product_control.total_quantity
            data = simplejson.dumps(product_json)
            return HttpResponse(data, 'application/json')


class WarehouseDetail(DetailView):
    model = Warehouse
    template_name = 'warehouse/warehouse_detail.html'


class MovementTypeDetail(DetailView):
    model = MovementType
    template_name = 'warehouse/movement_type_detail.html'


class OrderDetailView(DetailView):
    model = Order
    context_object_name = 'order'
    template_name = 'warehouse/order_detail.html'


class MovementDetailView(DetailView):
    model = Movement
    context_object_name = 'movement'
    template_name = 'warehouse/movement_detail.html'


class WarehouseDelete(TemplateView):
    http_method_names = ['post']

    @method_decorator(requires('warehouse.delete_warehouse'))
    def dispatch(self, *args, **kwargs):
        return super(WarehouseDelete, self).dispatch(*args, **kwargs)

    def post(self, request, *args, **kwargs):
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            code = request.POST['code']
            warehouse = Warehouse.objects.get(pk=code)
            warehouse_json = {}
            warehouse_json['code'] = warehouse.code
            warehouse_json['description'] = warehouse.description
            if len(warehouse.movements.all()) > 0:
                warehouse_json['relaciones'] = 'SI'
            else:
                warehouse_json['relaciones'] = 'NO'
                Warehouse.objects.filter(pk=code).update(is_active=False)
            data = simplejson.dumps(warehouse_json)
            return HttpResponse(data, 'application/json')


class MovementDelete(TemplateView):
    http_method_names = ['post']

    @method_decorator(requires('warehouse.delete_movement'))
    def dispatch(self, *args, **kwargs):
        return super(MovementDelete, self).dispatch(*args, **kwargs)

    def post(self, request, *args, **kwargs):
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            movement_id = request.POST['movement_id']
            movement = Movement.objects.get(pk=movement_id)
            order = movement.reference
            order = movement.order
            if order is not None:
                movement.delete_reference()
            if order is not None:
                movement.delete_order()
            kardex_detail = Kardex.objects.filter(movement=movement)
            for kardex in kardex_detail:
                control = WarehouseProductControl.objects.get(product=kardex.product, warehouse=kardex.warehouse)
                if kardex.in_quantity > 0:
                    control.stock = control.stock - kardex.in_quantity
                elif kardex.out_quantity > 0:
                    control.stock = control.stock + kardex.out_quantity
                control.save()
                kardex.delete()
            Movement.objects.filter(pk=movement_id).update(status=Movement.STATUS.CANC, reference=None)
            MovementDetail.objects.filter(movement=movement).delete()
            movement_json = {}
            movement_json['movement_id'] = movement_id
            data = simplejson.dumps(movement_json)
            return HttpResponse(data, 'application/json')


class OrderDelete(TemplateView):
    http_method_names = ['post']

    @method_decorator(requires('warehouse.delete_order'))
    def dispatch(self, *args, **kwargs):
        return super(OrderDelete, self).dispatch(*args, **kwargs)

    def post(self, request, *args, **kwargs):
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            code = request.POST['code']
            order = Order.objects.get(pk=code)
            movements = order.movements.all()
            warehouse_json = {}
            warehouse_json['code'] = order.code
            if len(movements) > 0:
                warehouse_json['movements'] = 'SI'
            else:
                warehouse_json['movements'] = 'NO'
                with transaction.atomic():
                    Order.objects.filter(code=code).update(status=Order.STATUS.CANC)
                    OrderDetail.objects.filter(order=order).delete()
            data = simplejson.dumps(warehouse_json)
            return HttpResponse(data, 'application/json')


class OrderApprovalList(ListView):
    model = Order
    template_name = 'warehouse/order_list.html'
    context_object_name = 'orders'

    @method_decorator(
        requires('warehouse.ver_tabla_aprobacion_pedidos'))
    def dispatch(self, *args, **kwargs):
        try:
            worker = self.request.user.worker
        except ObjectDoesNotExist:
            return HttpResponseRedirect(reverse('administration:worker_create'))
        try:
            positions = worker.positions.all().filter(is_active=True)
            if worker.signature == '':
                return HttpResponseRedirect(reverse('administration:worker_update', args=[worker.pk]))
            if positions[0].is_leadership and positions[0].office == logistics():
                return super(OrderApprovalList, self).dispatch(*args, **kwargs)
            else:
                return HttpResponseRedirect(reverse('security:permission_denied'))
        except (IndexError, ObjectDoesNotExist):
            return HttpResponseRedirect(reverse('security:permission_denied'))

    def get_queryset(self):
        queryset = Order.objects.filter(~Q(status=Order.STATUS.APROB))
        return queryset


class WarehouseList(ListView):
    model = Warehouse
    template_name = 'warehouse/warehouse_list.html'
    context_object_name = 'warehouses'
    queryset = Warehouse.objects.all().order_by('description')


class OrderList(ListView):
    model = Order
    template_name = 'warehouse/order_list.html'
    context_object_name = 'orders'
    queryset = Order.objects.exclude(status=Order.STATUS.CANC).order_by('code')


class MovementTypeList(ListView):
    model = MovementType
    template_name = 'warehouse/movement_type_list.html'
    context_object_name = 'movement_types'
    paginate_by = 10
    queryset = MovementType.objects.all().order_by('code')


class MovementList(ListView):
    model = Movement
    template_name = 'warehouse/movements.html'
    context_object_name = 'movements'
    queryset = Movement.objects.filter(status=Movement.STATUS.ACT)


class InboundList(ListView):
    model = Movement
    template_name = 'warehouse/entry_list.html'
    context_object_name = 'movements'
    queryset = Movement.objects.filter(status=Movement.STATUS.ACT, movement_type__increases=True)


class OutboundList(ListView):
    model = Movement
    template_name = 'warehouse/exit_list.html'
    context_object_name = 'movements'
    queryset = Movement.objects.filter(status=Movement.STATUS.ACT, movement_type__increases=False)


class MovementListByOrder(ListView):
    model = Movement
    template_name = 'warehouse/movements.html'
    context_object_name = 'movements'

    @method_decorator(requires('warehouse.ver_tabla_movimientos'))
    def dispatch(self, *args, **kwargs):
        return super(MovementListByOrder, self).dispatch(*args, **kwargs)

    def get_queryset(self):
        order = Order.objects.get(pk=self.kwargs['order'])
        queryset = order.movements.all()
        return queryset


class MovementUpdate(TemplateView):

    @method_decorator(requires('warehouse.change_movement'))
    def dispatch(self, *args, **kwargs):
        return super(MovementUpdate, self).dispatch(*args, **kwargs)

    def get(self, request, *args, **kwargs):
        pk = kwargs['pk']
        movement = Movement.objects.get(pk=pk)
        if movement.status == Movement.STATUS.CANC:
            return HttpResponseRedirect(reverse('security:permission_denied'))
        movement_type = movement.movement_type
        if movement_type.increases:
            return HttpResponseRedirect(reverse('warehouse:inbound_update', args=[movement.pk]))
        else:
            return HttpResponseRedirect(reverse('warehouse:outbound_update', args=[movement.pk]))


class InboundUpdate(UpdateView):
    template_name = 'warehouse/warehouse_entry.html'
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
            details = MovementDetail.objects.filter(movement=self.object).order_by('line_number')
            details_data = []
            for detail in details:
                if detail.purchase_order_detail is not None:
                    if detail.purchase_order_detail.quotation_detail is not None:
                        d = {'purchase_order': detail.purchase_order_detail.pk,
                             'code': detail.purchase_order_detail.quotation_detail.requirement_detail.product.code,
                             'name': detail.purchase_order_detail.quotation_detail.requirement_detail.product.description,
                             'unit': detail.purchase_order_detail.quotation_detail.requirement_detail.product.unit_of_measure.code,
                             'quantity': detail.quantity,
                             'price': detail.price,
                             'amount': detail.amount}
                    else:
                        d = {'purchase_order': detail.purchase_order_detail.pk,
                             'code': detail.purchase_order_detail.product.code,
                             'name': detail.purchase_order_detail.product.description,
                             'unit': detail.purchase_order_detail.product.unit_of_measure.code,
                             'quantity': detail.quantity,
                             'price': detail.price,
                             'amount': detail.amount}
                else:
                    d = {'purchase_order': '0',
                         'code': detail.product.code,
                         'name': detail.product.description,
                         'unit': detail.product.unit_of_measure.code,
                         'quantity': detail.quantity,
                         'price': detail.price,
                         'amount': detail.amount}
                details_data.append(d)
            inbound_detail_formset = InboundDetailFormSet(initial=details_data)
            return self.render_to_response(self.get_context_data(form=form,
                                                                 inbound_detail_formset=inbound_detail_formset))
        else:
            return HttpResponseRedirect(reverse('warehouse:inbound_list'))

    def get_initial(self):
        initial = super(InboundUpdate, self).get_initial()
        movement = self.object
        initial['movement_id'] = movement.movement_id
        initial['date'] = movement.operation_date.strftime('%d/%m/%Y')
        initial['time'] = movement.operation_date.strftime('%H : %M : %S')
        initial['warehouse'] = movement.warehouse
        initial['movement_type'] = movement.movement_type
        initial['reference_document'] = movement.reference
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
        inbound_detail_formset = InboundDetailFormSet(request.POST)
        if form.is_valid() and inbound_detail_formset.is_valid():
            return self.form_valid(form, inbound_detail_formset)
        else:
            return self.form_invalid(form, inbound_detail_formset)

    def form_valid(self, form, inbound_detail_formset):
        try:
            with transaction.atomic():
                if self.object.reference:
                    self.object.delete_reference()
                self.object.delete_kardex()
                self.object.delete_details()
                self.object = form.save()
                reference = self.object.reference
                details = []
                cont = 1
                for inbound_detail_form in inbound_detail_formset:
                    purchase_order = inbound_detail_form.cleaned_data.get('purchase_order')
                    code = inbound_detail_form.cleaned_data.get('code')
                    quantity = inbound_detail_form.cleaned_data.get('quantity')
                    price = inbound_detail_form.cleaned_data.get('price')
                    amount = inbound_detail_form.cleaned_data.get('amount')
                    if quantity and price and amount:
                        try:
                            purchase_order_detail = PurchaseOrderDetail.objects.get(pk=purchase_order)
                            movement_detail = MovementDetail(purchase_order_detail=purchase_order_detail,
                                                                   line_number=cont,
                                                                   movement=self.object,
                                                                   product=Product.objects.get(pk=code),
                                                                   quantity=quantity,
                                                                   price=price,
                                                                   amount=amount)
                        except ObjectDoesNotExist:
                            movement_detail = MovementDetail(line_number=cont,
                                                                   movement=self.object,
                                                                   product=Product.objects.get(pk=code),
                                                                   quantity=quantity,
                                                                   price=price,
                                                                   amount=amount)
                        details.append(movement_detail)
                        cont = cont + 1
                MovementDetail.objects.bulk_create(details, reference, None)
                return HttpResponseRedirect(reverse('warehouse:movement_detail_view', args=[self.object.pk]))
        except IntegrityError:
            messages.error(self.request, 'Error guardando la cotizacion.')

    def form_invalid(self, form, inbound_detail_formset):
        return self.render_to_response(self.get_context_data(form=form,
                                                             inbound_detail_formset=inbound_detail_formset))


class OutboundUpdate(UpdateView):
    template_name = 'warehouse/warehouse_exit.html'
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
        details = MovementDetail.objects.filter(movement=self.object)
        details_data = []
        for detail in details:
            try:
                d = {'order': detail.order_detail.pk,
                     'code': detail.product.pk,
                     'name': detail.product.description,
                     'unit': detail.product.unit_of_measure,
                     'quantity': detail.quantity,
                     'price': detail.price,
                     'amount': detail.amount}
            except (ObjectDoesNotExist, AttributeError):
                d = {'order': 0,
                     'code': detail.product.pk,
                     'name': detail.product.description,
                     'unit': detail.product.unit_of_measure,
                     'quantity': detail.quantity,
                     'price': detail.price,
                     'amount': detail.amount}
            details_data.append(d)
        outbound_detail_formset = OutboundDetailFormSet(initial=details_data)
        return self.render_to_response(self.get_context_data(form=form,
                                                             outbound_detail_formset=outbound_detail_formset))

    def get_initial(self):
        initial = super(OutboundUpdate, self).get_initial()
        movement = self.object
        self.details = MovementDetail.objects.filter(movement=movement)
        initial['movement_id'] = movement.movement_id
        initial['date'] = movement.operation_date.strftime('%d/%m/%Y')
        initial['time'] = movement.operation_date.strftime('%H : %M : %S')
        initial['warehouses'] = movement.warehouse
        initial['outbound_types'] = movement.movement_type
        initial['office'] = movement.office
        initial['reference'] = movement.reference
        initial['reference_document'] = movement.document_type
        initial['series'] = movement.series
        initial['number'] = movement.number
        initial['total'] = movement.total
        initial['notes'] = movement.notes
        initial['details_count'] = self.details.count()
        return initial

    def get_context_data(self, **kwargs):
        movement = self.object
        context = super(OutboundUpdate, self).get_context_data(**kwargs)
        context['movement'] = movement
        context['details'] = self.details
        return context

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        form_class = self.get_form_class()
        form = self.get_form(form_class)
        outbound_detail_formset = OutboundDetailFormSet(request.POST)
        if form.is_valid() and outbound_detail_formset.is_valid():
            return self.form_valid(form, outbound_detail_formset)
        else:
            return self.form_invalid(form, outbound_detail_formset)

    def form_valid(self, form, outbound_detail_formset):
        try:
            with transaction.atomic():
                if self.object.reference:
                    self.object.delete_reference()
                self.object.delete_details()
                self.object.delete_kardex()
                self.object = form.save()
                reference = self.object.reference
                details = []
                cont = 1
                for outbound_detail_form in outbound_detail_formset:
                    order_detail = outbound_detail_form.cleaned_data.get('order')
                    code = outbound_detail_form.cleaned_data.get('code')
                    quantity = outbound_detail_form.cleaned_data.get('quantity')
                    price = outbound_detail_form.cleaned_data.get('price')
                    amount = outbound_detail_form.cleaned_data.get('amount')
                    if quantity and price and amount:
                        try:
                            det_ped = OrderDetail.objects.get(pk=order_detail)
                        except ObjectDoesNotExist:
                            det_ped = None
                        movement_detail = MovementDetail(line_number=cont,
                                                               movement=self.object,
                                                               order_detail=det_ped,
                                                               product=Product.objects.get(pk=code),
                                                               quantity=quantity,
                                                               price=price,
                                                               amount=amount)
                        details.append(movement_detail)
                        cont = cont + 1
                MovementDetail.objects.bulk_create(details, reference, self.object.order)
                return HttpResponseRedirect(reverse('warehouse:movement_detail_view', args=[self.object.pk]))
        except IntegrityError:
            messages.error(self.request, 'Error guardando la cotizacion.')

    def form_invalid(self, form, outbound_detail_formset):
        return self.render_to_response(self.get_context_data(form=form,
                                                             outbound_detail_formset=outbound_detail_formset))


class WarehouseUpdate(UpdateView):
    model = Warehouse
    template_name = 'warehouse/warehouse_form.html'
    form_class = WarehouseForm
    success_url = reverse_lazy('warehouse:warehouse_list')


class OrderUpdate(UpdateView):
    template_name = 'warehouse/order_form.html'
    form_class = OrderForm
    model = Order
    context_object_name = 'order'

    @method_decorator(requires('warehouse.change_order'))
    def dispatch(self, *args, **kwargs):
        order = self.get_object()
        if order.status == Order.STATUS.PEND:
            return super(OrderUpdate, self).dispatch(*args, **kwargs)
        else:
            return HttpResponseRedirect(reverse('security:permission_denied'))

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
        details = OrderDetail.objects.filter(order=order).order_by('line_number')
        detail_count = details.count()
        context = super(OrderUpdate, self).get_context_data(**kwargs)
        context['order'] = order
        context['details'] = details
        context['detail_count'] = detail_count
        return context

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        if self.object.status == Order.STATUS.PEND:
            form_class = self.get_form_class()
            form = self.get_form(form_class)
            details = OrderDetail.objects.filter(order=self.object).order_by('line_number')
            details_data = []
            for detail in details:
                d = {'code': detail.product.code,
                     'name': detail.product.description,
                     'unit': detail.product.unit_of_measure.code,
                     'quantity': detail.quantity}
                details_data.append(d)
            order_detail_formset = OrderDetailFormSet(initial=details_data)
            return self.render_to_response(self.get_context_data(form=form,
                                                                 order_detail_formset=order_detail_formset))

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        form_class = self.get_form_class()
        form = self.get_form(form_class)
        order_detail_formset = OrderDetailFormSet(request.POST)
        if form.is_valid() and order_detail_formset.is_valid():
            return self.form_valid(form, order_detail_formset)
        else:
            return self.form_invalid(form, order_detail_formset)

    def form_valid(self, form, order_detail_formset):
        try:
            with transaction.atomic():
                self.object = form.save()
                OrderDetail.objects.filter(order=self.object).delete()
                details = []
                cont = 1
                for order_detail_form in order_detail_formset:
                    code = order_detail_form.cleaned_data.get('code')
                    quantity = order_detail_form.cleaned_data.get('quantity')
                    if code and quantity:
                        product = Product.objects.get(code=code)
                        details.append(OrderDetail(order=self.object,
                                                      line_number=cont,
                                                      product=product,
                                                      quantity=quantity))
                        cont = cont + 1
                OrderDetail.objects.bulk_create(details)
                return HttpResponseRedirect(reverse('warehouse:order_detail', args=[self.object.code]))
        except IntegrityError:
            messages.error(self.request, 'Error guardando la cotizacion.')

    def form_invalid(self, form, order_detail_formset):
        return self.render_to_response(self.get_context_data(form=form,
                                                             order_detail_formset=order_detail_formset))


class MovementListByProduct(FormView):
    template_name = 'warehouse/movements_by_product.html'
    form_class = ProductMovementForm

    def form_valid(self, form):
        data = form.cleaned_data
        start_date = data['start_date']
        end_date = data['end_date']
        warehouse = data['warehouse']
        product = Product.objects.get(code=data['product'])
        return self.get_movements(start_date, end_date, warehouse, product)

    def get_movements(self, start_date, end_date, warehouse, product):
        details = MovementDetail.objects.filter(movement__warehouse=warehouse,
                                                    product=product,
                                                    movement__operation_date__gte=start_date,
                                                    movement__operation_date__lte=end_date).order_by(
            'movement__operation_date')
        wb = Workbook()
        ws = wb.active
        ws['B1'] = u'Product: ' + product.description
        ws.merge_cells('B1:I1')
        ws['B2'] = u'Almacén: ' + warehouse.description
        ws.merge_cells('B2:D2')
        ws['E2'] = 'Periodo: Desde: ' + start_date.strftime('%d/%m/%Y') + ' Hasta: ' + end_date.strftime('%d/%m/%Y')
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
        for detail in details:
            ws.cell(row=cont, column=2).value = str(detail.movement)
            ws.cell(row=cont, column=3).value = str(detail.movement.movement_type)
            if detail.movement.reference is not None:
                ws.cell(row=cont, column=4).value = str(detail.movement.reference)
            else:
                ws.cell(row=cont, column=4).value = ""
            if detail.movement.order is not None:
                ws.cell(row=cont, column=5).value = str(detail.movement.order)
            else:
                ws.cell(row=cont, column=5).value = ""
            ws.cell(row=cont, column=6).value = detail.movement.operation_date.strftime('%d/%m/%Y %H : %M : %S')
            ws.cell(row=cont, column=7).value = detail.quantity
            ws.cell(row=cont, column=8).value = detail.price
            ws.cell(row=cont, column=9).value = detail.amount
            cont = cont + 1
        file_name = "MovementListByProduct.xlsx"
        response = HttpResponse(content_type="application/ms-excel")
        contenido = "attachment; filename={0}".format(file_name)
        response["Content-Disposition"] = contenido
        wb.save(response)
        return response


class InboundCreate(CreateView):
    template_name = 'warehouse/warehouse_entry.html'
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
        movement_type_code = 'I00'
        inbound_types = MovementType.objects.filter(increases=True).exclude(code=movement_type_code)
        if not inbound_types:
            return HttpResponseRedirect(reverse('warehouse:movement_type_create'))
        warehouses = Warehouse.objects.all()
        supply_count = Product.objects.count()
        if warehouses.count() > 0:
            if supply_count > 0:
                form_class = self.get_form_class()
                form = self.get_form(form_class)
                inbound_detail_formset = InboundDetailFormSet()
                return self.render_to_response(self.get_context_data(form=form,
                                                                     inbound_detail_formset=inbound_detail_formset))
        return HttpResponseRedirect(reverse('warehouse:dashboard'))

    def post(self, request, *args, **kwargs):
        self.object = None
        form_class = self.get_form_class()
        form = self.get_form(form_class)
        inbound_detail_formset = InboundDetailFormSet(request.POST)
        if form.is_valid() and inbound_detail_formset.is_valid():
            return self.form_valid(form, inbound_detail_formset)
        else:
            return self.form_invalid(form, inbound_detail_formset)

    def form_valid(self, form, inbound_detail_formset):
        try:
            with transaction.atomic():
                self.object = form.save()
                reference = self.object.reference
                details = []
                cont = 1
                for inbound_detail_form in inbound_detail_formset:
                    purchase_order = inbound_detail_form.cleaned_data.get('purchase_order')
                    code = inbound_detail_form.cleaned_data.get('code')
                    quantity = inbound_detail_form.cleaned_data.get('quantity')
                    price = inbound_detail_form.cleaned_data.get('price')
                    amount = inbound_detail_form.cleaned_data.get('amount')
                    if quantity and price and amount:
                        try:
                            purchase_order_detail = PurchaseOrderDetail.objects.get(pk=purchase_order)
                            movement_detail = MovementDetail(purchase_order_detail=purchase_order_detail,
                                                                   line_number=cont,
                                                                   movement=self.object,
                                                                   product=Product.objects.get(pk=code),
                                                                   quantity=quantity,
                                                                   price=price,
                                                                   amount=amount)
                        except ObjectDoesNotExist:
                            movement_detail = MovementDetail(line_number=cont,
                                                                   movement=self.object,
                                                                   product=Product.objects.get(pk=code),
                                                                   quantity=quantity,
                                                                   price=price,
                                                                   amount=amount)
                        details.append(movement_detail)
                        cont = cont + 1
                MovementDetail.objects.bulk_create(details, reference, None)
                return HttpResponseRedirect(reverse('warehouse:movement_detail_view', args=[self.object.pk]))
        except IntegrityError:
            messages.error(self.request, 'Error guardando la cotizacion.')

    def form_invalid(self, form, inbound_detail_formset):
        return self.render_to_response(self.get_context_data(form=form,
                                                             inbound_detail_formset=inbound_detail_formset))


class OutboundCreate(CreateView):
    form_class = MovementForm
    template_name = "warehouse/warehouse_exit.html"
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
        outbound_types = MovementType.objects.filter(increases=False)
        if not outbound_types:
            return HttpResponseRedirect(reverse('warehouse:movement_type_create'))
        warehouses = Warehouse.objects.filter()
        if not warehouses:
            return HttpResponseRedirect(reverse('warehouse:warehouse_create'))
        else:
            form_class = self.get_form_class()
            form = self.get_form(form_class)
            outbound_detail_formset = OutboundDetailFormSet()
            return self.render_to_response(self.get_context_data(form=form,
                                                                 outbound_detail_formset=outbound_detail_formset))

    def post(self, request, *args, **kwargs):
        self.object = None
        form_class = self.get_form_class()
        form = self.get_form(form_class)
        outbound_detail_formset = OutboundDetailFormSet(request.POST)
        if form.is_valid() and outbound_detail_formset.is_valid():
            return self.form_valid(form, outbound_detail_formset)
        else:
            return self.form_invalid(form, outbound_detail_formset)

    def form_valid(self, form, outbound_detail_formset):
        try:
            with transaction.atomic():
                self.object = form.save()
                reference = self.object.reference
                details = []
                cont = 1
                for outbound_detail_form in outbound_detail_formset:
                    code = outbound_detail_form.cleaned_data.get('code')
                    quantity = outbound_detail_form.cleaned_data.get('quantity')
                    price = outbound_detail_form.cleaned_data.get('price')
                    amount = outbound_detail_form.cleaned_data.get('amount')
                    if quantity and price and amount:
                        movement_detail = MovementDetail(line_number=cont,
                                                               movement=self.object,
                                                               product=Product.objects.get(pk=code),
                                                               quantity=quantity,
                                                               price=price,
                                                               amount=amount)
                        details.append(movement_detail)
                        cont = cont + 1
                MovementDetail.objects.bulk_create(details, reference, None)
                return HttpResponseRedirect(reverse('warehouse:movement_detail_view', args=[self.object.pk]))
        except IntegrityError:
            messages.error(self.request, 'Error guardando la cotizacion.')

    def form_invalid(self, form, outbound_detail_formset):
        return self.render_to_response(self.get_context_data(form=form,
                                                             outbound_detail_formset=outbound_detail_formset))


class WarehouseExcelReport(TemplateView):

    def get(self, request, *args, **kwargs):
        warehouses = Warehouse.objects.filter(is_active=True).order_by('code')
        wb = Workbook()
        ws = wb.active
        ws['B1'] = 'REPORTE DE ALMACENES'
        ws.merge_cells('B1:J1')
        ws['B3'] = 'CODIGO'
        ws['C3'] = 'DESCRIPCIÓN'
        cont = 4
        for warehouse in warehouses:
            ws.cell(row=cont, column=2).value = warehouse.code
            ws.cell(row=cont, column=3).value = warehouse.description
            cont = cont + 1
        file_name = "WarehouseList.xlsx"
        response = HttpResponse(content_type="application/ms-excel")
        contenido = "attachment; filename={0}".format(file_name)
        response["Content-Disposition"] = contenido
        wb.save(response)
        return response


class MovementTypeExcelReport(TemplateView):

    def get(self, request, *args, **kwargs):
        types = MovementType.objects.filter(is_active=True).order_by('code')
        wb = Workbook()
        ws = wb.active
        ws['B1'] = 'REPORTE DE TIPOS DE MOVIMIENTOS'
        ws.merge_cells('B1:J1')
        ws['B3'] = 'CODIGO'
        ws['C3'] = 'DESCRIPCIÓN'
        cont = 4
        for type in types:
            ws.cell(row=cont, column=2).value = type.code
            ws.cell(row=cont, column=3).value = type.description
            cont = cont + 1
        file_name = "MaestroTiposMovimientos.xlsx"
        response = HttpResponse(content_type="application/ms-excel")
        contenido = "attachment; filename={0}".format(file_name)
        response["Content-Disposition"] = contenido
        wb.save(response)
        return response


class ReportResponseMixin(object):
    """Armado de la respuesta HTTP de los reportes que se descargan como file."""

    def _pdf_response(self, contenido, file_name):
        response = HttpResponse(content_type='application/pdf')
        response['Content-Disposition'] = 'attachment; filename=' + file_name
        response.write(contenido)
        return response

    def _excel_response(self, excel, file_name):
        response = HttpResponse(content_type="application/ms-excel")
        response["Content-Disposition"] = "attachment; filename={0}".format(file_name)
        excel.save(response)
        return response


class KardexProductReport(ReportResponseMixin, FormView):
    template_name = 'warehouse/product_kardex_report.html'
    form_class = KardexProductForm

    REPORTES_EXCEL = {
        'S': ('get_sunat_physical_units_product', 'InventarioPermanenteUnidadesFisicas.xlsx'),
        'V': ('get_sunat_valued_product', 'InventarioPermanenteValorizado.xlsx'),
        None: ('get_normal_format_product', 'ReporteExcelKardexProducto.xlsx'),
    }

    REPORTES_PDF = {
        'S': ('render_sunat_physical_units_product_format', 'InventarioPermanenteUnidadesFisicas.pdf'),
        'V': ('render_sunat_valued_product_format', 'InventarioPermanenteValorizado.pdf'),
    }

    def _sunat_format(self, sunat_format):
        return sunat_format if sunat_format in ('S', 'V') else None

    def form_valid(self, form):
        data = form.cleaned_data
        product_code = data.get('product_code')
        product = Product.objects.get(code=product_code)
        start_date = data.get('start_date')
        end_date = data.get('end_date')
        warehouse = data.get('warehouses')
        sunat_format = data.get('sunat_format')
        formats = data.get('formats')

        if formats == 'XLS':
            metodo, file_name = self.REPORTES_EXCEL[self._sunat_format(sunat_format)]
            excel = getattr(KardexExcelReport(), metodo)(product, start_date, end_date, warehouse)
            return self._excel_response(excel, file_name)
        if formats == 'PDF':
            key = self._sunat_format(sunat_format)
            if key not in self.REPORTES_PDF:
                return HttpResponse('Este reporte no esta disponible en PDF para la combinacion elegida.',
                                    status=404)
            metodo, file_name = self.REPORTES_PDF[key]
            report = KardexPdfReport('A4', start_date, end_date, warehouse, False)
            return self._pdf_response(getattr(report, metodo)(product), file_name)
        return HttpResponse('Formato no soportado.', status=400)


class KardexReport(ReportResponseMixin, FormView):
    template_name = 'warehouse/kardex_report.html'
    form_class = KardexProductForm

    def form_valid(self, form):
        data = form.cleaned_data
        start_date = data.get('start_date')
        end_date = data['end_date']
        warehouse = data.get('warehouses')
        sunat_format = data.get('sunat_format')
        formats = data.get('formats')
        consolidated = data['consolidated']

        key = self._report_key(consolidated, sunat_format)
        if formats == 'XLS':
            return self._excel_report(key, start_date, end_date, warehouse)
        if formats == 'PDF':
            return self._pdf_report(key, start_date, end_date, warehouse)
        return HttpResponse('Formato no soportado.', status=400)

    REPORTES_PDF = {
        ('P', None): ('render_consolidated_products_format', False, 'ResumenMensualDeAlmacen.pdf'),
        ('G', None): ('render_consolidated_groups_format', True, 'ResumenMensualDeAlmacenPorGruposYCuentas.pdf'),
        (None, 'S'): ('render_sunat_physical_units_all_format', False,
                      'InventarioPermanenteUnidadesFisicas.pdf'),
        (None, 'V'): ('render_sunat_valued_all_format', False, 'InventarioPermanenteValorizado.pdf'),
    }

    REPORTES_EXCEL = {
        ('P', None): ('get_consolidated_products', 'ReporteConsolidadoKardexExcel.xlsx'),
        ('G', None): ('get_consolidated_groups', 'ReporteConsolidadoCuentasContablesAlmacen.xlsx'),
        (None, 'S'): ('get_sunat_physical_units_all', 'InventarioPermanenteUnidadesFisicas.xlsx'),
        (None, 'V'): ('get_sunat_valued_all', 'InventarioPermanenteValorizado.xlsx'),
        (None, None): ('get_normal_format_all', 'ReporteFormatoNormalKardexTodosLosProductos.xlsx'),
    }

    def _report_key(self, consolidated, sunat_format):
        if consolidated in ('P', 'G'):
            return (consolidated, None)
        return (None, sunat_format if sunat_format in ('S', 'V') else None)

    def _pdf_report(self, key, start_date, end_date, warehouse):
        if key not in self.REPORTES_PDF:
            return HttpResponse('Este reporte no esta disponible en PDF para la combinacion elegida.', status=404)
        metodo, agrupado, file_name = self.REPORTES_PDF[key]
        report = KardexPdfReport('A4', start_date, end_date, warehouse, agrupado)
        return self._pdf_response(getattr(report, metodo)(), file_name)

    def _excel_report(self, key, start_date, end_date, warehouse):
        metodo, file_name = self.REPORTES_EXCEL[key]
        report = KardexExcelReport()
        return self._excel_response(getattr(report, metodo)(start_date, end_date, warehouse), file_name)


class PriceReprocess(FormView):
    template_name = 'warehouse/price_reprocess.html'
    form_class = PriceReprocessForm

    def reprocess_product_price(self, product, warehouse, start_date):
        details = Kardex.objects.filter(product=product,
                                         warehouse=warehouse,
                                         operation_date__gte=start_date).order_by('operation_date')
        index = 0
        for detail in details:
            try:
                previous = details[index - 1]
                previous_quantity = previous.total_quantity
                previous_amount = previous.total_amount
                previous_price = Decimal(round(previous_amount / previous_quantity, 8))
            except (IndexError, ZeroDivisionError, TypeError):
                previous_quantity = 0
                previous_price = 0
                previous_amount = 0
            movement_type = detail.movement.movement_type
            if movement_type.increases:
                detail.total_quantity = previous_quantity + detail.in_quantity
                detail.total_price = detail.in_price
                detail.total_amount = previous_amount + detail.in_amount
            else:
                detail.out_price = previous_price
                detail.out_amount = detail.out_quantity * detail.out_price
                detail.total_quantity = previous_quantity - detail.out_quantity
                detail.total_amount = previous_amount - detail.out_amount
                try:
                    detail.total_price = detail.total_amount / detail.total_quantity
                except ZeroDivisionError:
                    detail.total_price = 0
            detail.save()
            index = index + 1

    def form_valid(self, form):
        data = form.cleaned_data
        start_date = data['start_date']
        warehouse = data['warehouse']
        selection = data['selection']
        if selection == 'P':
            product_code = data['product']
            product = Product.objects.get(code=product_code)
            self.reprocess_product_price(product, warehouse, start_date)
        else:
            listado_kardex = Kardex.objects.filter(warehouse=warehouse).order_by('product').distinct('product__code')
            for kardex in listado_kardex:
                self.reprocess_product_price(kardex.product, warehouse, start_date)
        return HttpResponseRedirect(reverse('warehouse:dashboard'))


class ProductStock(FormView):
    form_class = StockQueryForm
    template_name = 'warehouse/product_stock.html'

    def get_initial(self):
        initial = super(ProductStock, self).get_initial()
        initial['start_date'] = date.today().strftime('%d/%m/%Y')
        return initial

    def form_valid(self, form):
        data = form.cleaned_data
        warehouse = data['warehouse']
        description = data['description']
        products = list(Product.objects.filter(description__icontains=description)
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
        last_records = Kardex.last_by_product(products, warehouse=warehouse)
        for product in products:
            kardex = last_records.get(product.pk)
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

            temp_price = format(price, '.3f')
            if temp_price == '-0.000':
                price = format(abs(price), '.3f')
            else:
                price = format(price, '.3f')
            ws.cell(row=cont, column=6).value = price
            ws.cell(row=cont, column=6).number_format = '#.000'
            temp_amount = format(amount, '.3f')
            if temp_amount == '-0.000':
                amount = format(abs(amount), '.3f')
            else:
                amount = format(amount, '.3f')
            ws.cell(row=cont, column=7).value = amount
            ws.cell(row=cont, column=7).number_format = '#.000'
            cont = cont + 1
        file_name = "ReporteStock.xlsx"
        response = HttpResponse(content_type="application/ms-excel")
        contenido = "attachment; filename={0}".format(file_name)
        response["Content-Disposition"] = contenido
        wb.save(response)
        return response


class ProductStockList(AjaxOnlyMixin, TemplateView):

    required_params = ('description', 'warehouse')

    def get(self, request, *args, **kwargs):
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            description = request.GET['description']
            warehouse = request.GET['warehouse']
            product_list = []
            products = list(Product.objects.filter(description__icontains=description)
                             .select_related('unit_of_measure').order_by('description'))
            last_records = Kardex.last_by_product(products, warehouse__pk=warehouse)
            for product in products:
                kardex = last_records.get(product.pk)
                kardex_json = {}
                kardex_json['code'] = product.code
                kardex_json['label'] = product.description
                kardex_json['unit'] = product.unit_of_measure.code
                kardex_json['stock'] = kardex.total_quantity if kardex else 0
                product_list.append(kardex_json)
            data = simplejson.dumps(product_list)
            return HttpResponse(data, 'application/json')


class MovementExcelReport(FormView):
    form_class = MovementReportForm
    template_name = "warehouse/movement_report.html"

    def form_valid(self, form):
        data = form.cleaned_data
        search_type = data['search_type']
        previous_warehouse = data['warehouses']
        previous_movement_type = data['movement_types']
        warehouse = Warehouse.objects.get(code=previous_warehouse)
        movement_type = MovementType.objects.get(code=previous_movement_type)
        wb = Workbook()
        ws = wb.active
        if search_type == 'F':
            start_date = data['start_date']
            end_date = data['end_date']
            ws['B1'] = 'REPORTE DE MOVIMIENTOS POR FECHA'
            ws.merge_cells('B1:H1')
            ws['B2'] = 'ALMACEN: ' + warehouse.description
            ws.merge_cells('B2:D2')
            ws['E2'] = 'TIPO DE MOVIMIENTO: ' + movement_type.description
            ws.merge_cells('E2:H2')
            ws['B3'] = 'DESDE'
            ws['C3'] = timezone.localtime(start_date).replace(tzinfo=None)
            ws['C3'].number_format = 'dd/mm/yyyy'
            ws['D3'] = 'HASTA'
            ws['E3'] = timezone.localtime(end_date).replace(tzinfo=None)
            ws['F3'].number_format = 'dd/mm/yyyy'
            movements = Movement.objects.filter(operation_date__range=[start_date, end_date],
                                                    movement_type=movement_type, warehouse=warehouse)
        elif search_type == 'M':
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
            movements = Movement.objects.filter(operation_date__month=month,
                                                    operation_date__year=year,
                                                    movement_type=movement_type,
                                                    warehouse=warehouse)
        elif search_type == 'A':
            year = data['year'].strip()
            ws['B1'] = 'REPORTE DE MOVIMIENTOS POR AÑO'
            ws.merge_cells('B1:H1')
            ws['B2'] = 'ALMACEN: ' + warehouse.description
            ws.merge_cells('B2:D2')
            ws['E2'] = 'TIPO DE MOVIMIENTO: ' + movement_type.description
            ws.merge_cells('E2:H2')
            ws['B3'] = 'AÑO'
            ws['C3'] = year
            movements = Movement.objects.filter(operation_date__year=year,
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
        movements = movements.order_by('operation_date')
        for movement in movements:
            ws.cell(row=cont, column=2).value = movement.movement_id
            try:
                ws.cell(row=cont, column=3).value = movement.document_type.description
            except ObjectDoesNotExist:
                ws.cell(row=cont, column=3).value = '--'
            ws.cell(row=cont, column=4).value = movement.series
            ws.cell(row=cont, column=5).value = movement.number
            ws.cell(row=cont, column=6).value = timezone.localtime(movement.operation_date).replace(tzinfo=None)
            ws.cell(row=cont, column=6).number_format = 'dd/mm/yyyy hh:mm:ss'
            ws.cell(row=cont, column=7).value = movement.notes
            ws.cell(row=cont, column=8).value = timezone.localtime(movement.created).replace(tzinfo=None)
            ws.cell(row=cont, column=8).number_format = 'dd/mm/yyyy hh:mm:ss'
            ws.cell(row=cont, column=9).value = movement.status
            cont = cont + 1
        file_name = "ReporteMovimientosPorFecha.xlsx"
        response = HttpResponse(content_type="application/ms-excel")
        contenido = "attachment; filename={0}".format(file_name)
        response["Content-Disposition"] = contenido
        wb.save(response)
        return response


class MovementExcelReportByDate(View):

    def get(self, request, *args, **kwargs):
        p_start_date = kwargs['start_date']
        previous_end_date = kwargs['end_date']
        previous_warehouse = kwargs['warehouse']
        previous_movement_type = kwargs['movement_type']
        year = int(p_start_date[6:])
        month = int(p_start_date[3:5])
        dia = int(p_start_date[0:2])
        start_date = timezone.make_aware(datetime.datetime(year, month, dia, 23, 59, 59))
        year = int(previous_end_date[6:])
        month = int(previous_end_date[3:5])
        dia = int(previous_end_date[0:2])
        end_date = timezone.make_aware(datetime.datetime(year, month, dia, 23, 59, 59))
        warehouse = Warehouse.objects.get(code=previous_warehouse)
        movement_type = MovementType.objects.get(code=previous_movement_type)
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
        ws['E3'] = previous_end_date
        ws['F3'].number_format = 'dd/mm/yyyy'
        movements = Movement.objects.filter(operation_date__range=[start_date, end_date],
                                                movement_type=movement_type, warehouse=warehouse)
        ws['B5'] = 'ID_MOVIMIENTO'
        ws['C5'] = 'TIPO_DOCUMENTO'
        ws['D5'] = 'SERIE'
        ws['E5'] = 'NUMERO'
        ws['F5'] = 'FECHA_OPERACION'
        ws['G5'] = 'OBSERVACION'
        ws['H5'] = 'FECHA_CREACION'
        cont = 6
        for movement in movements:
            ws.cell(row=cont, column=2).value = movement.movement_id
            ws.cell(row=cont, column=3).value = movement.document_type.description if movement.document_type else '--'
            ws.cell(row=cont, column=4).value = movement.series
            ws.cell(row=cont, column=5).value = movement.number
            ws.cell(row=cont, column=6).value = timezone.localtime(movement.operation_date).replace(tzinfo=None)
            ws.cell(row=cont, column=6).number_format = 'dd/mm/yyyy hh:mm:ss'
            ws.cell(row=cont, column=7).value = movement.observation
            ws.cell(row=cont, column=8).value = timezone.localtime(movement.created).replace(tzinfo=None)
            ws.cell(row=cont, column=8).number_format = 'dd/mm/yyyy hh:mm:ss'
            cont = cont + 1
        file_name = "ReporteMovimientosPorFecha.xlsx"
        response = HttpResponse(content_type="application/ms-excel")
        contenido = "attachment; filename={0}".format(file_name)
        response["Content-Disposition"] = contenido
        wb.save(response)
        return response


class MovementPdfReport(View):

    def get(self, request, *args, **kwargs):
        movement_id = kwargs['movement_id']
        movement = Movement.objects.get(pk=movement_id)
        response = HttpResponse(content_type='application/pdf')
        report = MovementReport('A4', movement)
        pdf = report.render()
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
        allclientes = [(p.code, p.description, p.market_price, p.supply_group) for p in Product.objects.all()]

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


class VerifyReferenceRequired(AjaxOnlyMixin, TemplateView):

    required_params = ('type',)

    def get(self, request, *args, **kwargs):
        type = request.GET['type']
        movement_type = MovementType.objects.get(pk=type)
        json_object = {'requires_reference': movement_type.requires_reference}
        return JsonResponse(json_object)


class VerifyStockForOrder(AjaxOnlyMixin, TemplateView):

    required_params = ('warehouse', 'order')

    def get(self, request, *args, **kwargs):
        warehouse = request.GET['warehouse']
        order = request.GET['order']
        details = list(OrderDetail.objects.filter(order__code=order,
                                                     status=OrderDetail.STATUS.PEND)
                        .select_related('product__unit_of_measure').order_by('line_number'))
        last_records = Kardex.last_by_product([detail.product for detail in details],
                                              warehouse__code=warehouse)
        detail_list = []
        for detail in details:
            product_control = last_records.get(detail.product_id)
            try:
                stock = product_control.total_quantity
                price = product_control.total_amount / stock
            except (AttributeError, ZeroDivisionError):
                stock = 0
                price = 0
            if stock != 0:
                det = {}
                det['order'] = detail.id
                det['code'] = detail.product.code
                det['name'] = detail.product.description
                det['unit'] = detail.product.unit_of_measure.description
                quantity = detail.quantity - detail.served_quantity
                if quantity > stock:
                    quantity = stock
                amount = round(quantity * price, 5)
                det['quantity'] = quantity
                det['price'] = round(price, 5)
                det['amount'] = amount
                detail_list.append(det)
        formset = OutboundDetailFormSet(initial=detail_list)
        json_list = []
        for form in formset:
            detail_json = {}
            detail_json['order'] = str(form['order'])
            detail_json['code'] = str(form['code'])
            detail_json['name'] = str(form['name'])
            detail_json['quantity'] = str(form['quantity'])
            detail_json['price'] = str(form['price'])
            detail_json['unit'] = str(form['unit'])
            detail_json['amount'] = str(form['amount'])
            json_list.append(detail_json)
        data = json.dumps(json_list)
        return HttpResponse(data, 'application/json')


class Inventory(ReportResponseMixin, FormView):
    form_class = InventoryQueryForm
    template_name = 'warehouse/inventory.html'

    def get_initial(self):
        initial = super(Inventory, self).get_initial()
        initial['start_date'] = date.today().strftime('%d/%m/%Y')
        return initial

    def form_valid(self, form):
        return self._excel_response(inventory_report(form.cleaned_data['start_date']),
                                     'ReporteInventario.xlsx')
