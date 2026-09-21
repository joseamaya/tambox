# -*- coding: utf-8 -*- 
from django.utils import timezone
from django.views.generic.base import View, TemplateView
from django.views.generic.list import ListView

from compras.models import Supplier, PurchaseOrder, PaymentMethod, PurchaseOrderDetail, RequirementDetail, ServiceOrder, \
    ServiceOrderDetail, ServiceConformity, \
    ServiceConformityDetail, QuotationDetail, Quotation
from django.views.generic.edit import FormView, UpdateView, CreateView
from compras.forms import ProveedorForm, CotizacionForm, OrdenCompraForm, \
    OrdenServiciosForm, ConformidadServicioForm, DetalleOrdenCompraFormSet, \
    DetalleOrdenServiciosFormSet, DetalleConformidadServicioFormSet, DetalleCotizacionFormSet, \
    FormularioReporteOrdenesFecha
from django.urls import reverse_lazy, reverse
from django.http.response import HttpResponseRedirect
import json
from django.http import HttpResponse
import datetime
import simplejson
from openpyxl import Workbook
from django.views.generic.detail import DetailView
# from reportlab.lib.pagesizes import cm
import locale
from seguridad.permisos import requiere
from django.utils.decorators import method_decorator
from django.db import transaction, IntegrityError
from django.core.exceptions import ObjectDoesNotExist
from contabilidad.forms import UploadForm
from django.db.models import Q
from django.contrib import messages
from almacen.forms import DetalleIngresoFormSet
from django.shortcuts import render, get_object_or_404

from contabilidad.models import ExchangeRate
from productos.models import Product, UnitOfMeasure, ProductGroup
from datetime import date
from compras.reports import reporte_xls_orden_compra, PDFOrdenCompra, \
    PDFOrdenServicios, PDFMemorandoConformidadServicio, PDFSolicitudCotizacion
from tambox.configuracion import configuracion, purchase_tax
from tambox.vistas import CargarCsvMixin, SoloAjaxMixin
from decimal import Decimal

locale.setlocale(locale.LC_ALL, "")


class Tablero(View):

    def get(self, request, *args, **kwargs):
        lista_notificaciones = []
        cant_proveedores = Supplier.objects.count()
        cant_productos = Product.objects.filter(is_service=False).count()
        cant_tipos_unidad_medida = UnitOfMeasure.objects.count()
        cant_grupos_suministros = ProductGroup.objects.count()
        cant_servicios = Product.objects.filter(is_service=True).count()
        unit_of_measure, creado = UnitOfMeasure.objects.get_or_create(code='SERV',
                                                                   defaults={'description': 'SERVICIO'})
        if cant_proveedores == 0:
            lista_notificaciones.append("No se ha creado ningún proveedor")
        if creado:
            lista_notificaciones.append("Se ha creado la unidad de medida SERVICIO")
        if cant_productos == 0:
            lista_notificaciones.append("No se ha creado ningún producto")
        if cant_tipos_unidad_medida == 0:
            lista_notificaciones.append("No se ha creado ningún tipo de unidad de medida")
        if cant_grupos_suministros == 0:
            lista_notificaciones.append("No se ha creado ningún grupo de productos")
        if cant_servicios == 0:
            lista_notificaciones.append("No se ha creado ningún servicio")
        context = {'notificaciones': lista_notificaciones}
        return render(request, 'compras/tablero_compras.html', context)


class BusquedaCotizacion(SoloAjaxMixin, TemplateView):

    parametros_requeridos = ('code',)

    def get(self, request, *args, **kwargs):
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            code = request.GET['code']
            quotation = Quotation.objects.get(code=code)
            cotizacion_json = {}
            cotizacion_json['tax_id'] = quotation.supplier.tax_id
            cotizacion_json['business_name'] = quotation.supplier.business_name
            cotizacion_json['address'] = quotation.supplier.address
            data = simplejson.dumps(cotizacion_json)
            return HttpResponse(data, 'application/json')


class BusquedaProveedoresRazonSocial(SoloAjaxMixin, TemplateView):

    parametros_requeridos = ('business_name',)

    def get(self, request, *args, **kwargs):
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            business_name = request.GET['business_name']
            proveedores = Supplier.objects.filter(business_name__icontains=business_name)[:20]
            lista_proveedores = []
            for supplier in proveedores:
                proveedor_json = {}
                proveedor_json['label'] = supplier.business_name
                proveedor_json['tax_id'] = supplier.tax_id
                proveedor_json['address'] = supplier.address
                proveedor_json['order'] = str(ServiceOrder.objects.ultimo())
                lista_proveedores.append(proveedor_json)
            data = json.dumps(lista_proveedores)
            return HttpResponse(data, 'application/json')


class BusquedaProveedoresRUC(SoloAjaxMixin, TemplateView):

    parametros_requeridos = ('tax_id',)

    def get(self, request, *args, **kwargs):
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            tax_id = request.GET['tax_id']
            supplier = Supplier.objects.get(tax_id=tax_id)
            proveedor_json = {}
            proveedor_json['business_name'] = supplier.business_name
            proveedor_json['address'] = supplier.address
            proveedor_json['estado'] = supplier.sunat_status
            proveedor_json['es_locador'] = supplier.es_locador
            proveedor_json['order'] = str(ServiceOrder.objects.ultimo())
            data = simplejson.dumps(proveedor_json)
            return HttpResponse(data, 'application/json')


class CargarProveedores(CargarCsvMixin, FormView):
    template_name = 'compras/cargar_proveedores.html'
    form_class = UploadForm
    success_url = reverse_lazy('compras:proveedores')

    def procesar_fila(self, fila):
        Supplier.objects.get_or_create(tax_id=fila[0],
                                        defaults={'business_name': fila[1],
                                                  'address': fila[2],
                                                  'registration_date': datetime.datetime.now(),
                                                  'sunat_status': 'ACTIVO',
                                                  'sunat_condition': 'HABIDO',
                                                  'ciiu': 'CUALQUIERA'})


class CrearProveedor(CreateView):
    model = Supplier
    context_object_name = 'supplier'
    template_name = 'compras/proveedor.html'
    form_class = ProveedorForm

    @method_decorator(requiere('compras.add_supplier'))
    def dispatch(self, *args, **kwargs):
        return super(CrearProveedor, self).dispatch(*args, **kwargs)

    def get_success_url(self):
        return reverse('compras:detalle_proveedor', args=[self.object.pk])

    def form_invalid(self, form):
        return self.render_to_response(self.get_context_data(form=form))


class CrearDetalleOrdenCompra(SoloAjaxMixin, TemplateView):

    def get(self, request, *args, **kwargs):
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            lista_detalles = []
            det = {}
            det['quotation'] = '0'
            det['code'] = ''
            det['name'] = ''
            det['unidad'] = ''
            det['quantity'] = '0'
            det['price'] = '0'
            det['impuesto'] = '0'
            det['amount'] = '0'
            lista_detalles.append(det)
            formset = DetalleOrdenCompraFormSet(initial=lista_detalles)
            lista_json = []
            for form in formset:
                detalle_json = {}
                detalle_json['quotation'] = str(form['quotation'])
                detalle_json['code'] = str(form['code'])
                detalle_json['name'] = str(form['name'])
                detalle_json['unidad'] = str(form['unidad'])
                detalle_json['quantity'] = str(form['quantity'])
                detalle_json['price'] = str(form['price'])
                detalle_json['impuesto'] = str(form['impuesto'])
                detalle_json['amount'] = str(form['amount'])
                lista_json.append(detalle_json)
            data = json.dumps(lista_json)
            return HttpResponse(data, 'application/json')


class CrearDetalleOrdenServicios(SoloAjaxMixin, TemplateView):

    def get(self, request, *args, **kwargs):
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            lista_detalles = []
            det = {}
            det['quotation'] = '0'
            det['code'] = ''
            det['name'] = ''
            det['unidad'] = ''
            det['quantity'] = '0'
            det['price'] = '0'
            det['amount'] = '0'
            lista_detalles.append(det)
            formset = DetalleOrdenServiciosFormSet(initial=lista_detalles)
            lista_json = []
            for form in formset:
                detalle_json = {}
                detalle_json['quotation'] = str(form['quotation'])
                detalle_json['code'] = str(form['code'])
                detalle_json['name'] = str(form['name'])
                detalle_json['unidad'] = str(form['unidad'])
                detalle_json['quantity'] = str(form['quantity'])
                detalle_json['price'] = str(form['price'])
                detalle_json['amount'] = str(form['amount'])
                lista_json.append(detalle_json)
            data = json.dumps(lista_json)
            return HttpResponse(data, 'application/json')


class CrearCotizacion(CreateView):
    form_class = CotizacionForm
    template_name = "compras/cotizacion.html"
    model = Quotation
    context_object_name = 'quotation'

    @method_decorator(requiere('compras.add_quotation'))
    def dispatch(self, *args, **kwargs):
        return super(CrearCotizacion, self).dispatch(*args, **kwargs)

    def get_initial(self):
        initial = super(CrearCotizacion, self).get_initial()
        initial['date'] = date.today().strftime('%d/%m/%Y')
        return initial

    def get(self, request, *args, **kwargs):
        self.object = None
        proveedores = Supplier.objects.all()
        if not proveedores:
            return HttpResponseRedirect(reverse('compras:crear_proveedor'))
        else:
            form_class = self.get_form_class()
            form = self.get_form(form_class)
            detalle_cotizacion_formset = DetalleCotizacionFormSet()
            return self.render_to_response(self.get_context_data(form=form,
                                                                 detalle_cotizacion_formset=detalle_cotizacion_formset))

    def post(self, request, *args, **kwargs):
        self.object = None
        form_class = self.get_form_class()
        form = self.get_form(form_class)
        detalle_cotizacion_formset = DetalleCotizacionFormSet(request.POST)
        if form.is_valid() and detalle_cotizacion_formset.is_valid():
            return self.form_valid(form, detalle_cotizacion_formset)
        else:
            return self.form_invalid(form, detalle_cotizacion_formset)

    def form_valid(self, form, detalle_cotizacion_formset):
        # try:
        with transaction.atomic():
            self.object = form.save()
            reference = self.object.requirement
            detalles = []
            cont = 1
            for detalle_cotizacion_form in detalle_cotizacion_formset:
                requirement = detalle_cotizacion_form.cleaned_data.get('requirement')
                quantity = detalle_cotizacion_form.cleaned_data.get('quantity')
                requirement_detail = RequirementDetail.objects.get(pk=requirement)
                if quantity:
                    quotation_detail = QuotationDetail(requirement_detail=requirement_detail,
                                                           line_number=cont,
                                                           quotation=self.object,
                                                           quantity=quantity)
                    detalles.append(quotation_detail)

                    cont = cont + 1
            QuotationDetail.objects.bulk_create(detalles, reference, None)
            return HttpResponseRedirect(reverse('compras:quotation_detail', args=[self.object.code]))
        # except IntegrityError:
        # messages.error(self.request, 'Error guardando la cotizacion.')

    def form_invalid(self, form, detalle_cotizacion_formset):
        return self.render_to_response(self.get_context_data(form=form,
                                                             detalle_cotizacion_formset=detalle_cotizacion_formset))


class CrearOrdenCompra(CreateView):
    form_class = OrdenCompraForm
    template_name = "compras/orden_compra.html"
    model = PurchaseOrder

    @method_decorator(requiere('compras.add_purchaseorder'))
    def dispatch(self, *args, **kwargs):
        return super(CrearOrdenCompra, self).dispatch(*args, **kwargs)

    def get_initial(self):
        initial = super(CrearOrdenCompra, self).get_initial()
        try:
            monto_impuesto = purchase_tax().amount
        except AttributeError:
            return HttpResponseRedirect(reverse('contabilidad:configuracion'))
        initial['date'] = date.today().strftime('%d/%m/%Y')
        initial['code'] = PurchaseOrder.objects.ultimo()
        initial['impuesto_actual'] = monto_impuesto
        initial['total'] = 0
        initial['subtotal'] = 0
        initial['impuesto'] = 0
        initial['total_in_words'] = ''
        return initial

    def get(self, request, *args, **kwargs):
        self.object = None
        formas_pago = PaymentMethod.objects.all().order_by('description')
        if not formas_pago:
            return HttpResponseRedirect(reverse('contabilidad:crear_forma_pago'))
        else:
            try:
                configuracion()
                form_class = self.get_form_class()
                form = self.get_form(form_class)
                detalle_orden_compra_formset = DetalleOrdenCompraFormSet()
                return self.render_to_response(self.get_context_data(form=form,
                                                                     detalle_orden_compra_formset=detalle_orden_compra_formset))
            except Exception:
                return HttpResponseRedirect(reverse('contabilidad:configuracion'))

    def post(self, request, *args, **kwargs):
        self.object = None
        form_class = self.get_form_class()
        form = self.get_form(form_class)
        detalle_orden_compra_formset = DetalleOrdenCompraFormSet(request.POST)
        if form.is_valid() and detalle_orden_compra_formset.is_valid():
            return self.form_valid(form, detalle_orden_compra_formset)
        else:
            return self.form_invalid(form, detalle_orden_compra_formset)

    def form_valid(self, form, detalle_orden_compra_formset):
        try:
            with transaction.atomic():
                self.object = form.save()
                reference = self.object.quotation
                detalles = []
                cont = 1
                for detalle_orden_compra_form in detalle_orden_compra_formset:
                    quotation = detalle_orden_compra_form.cleaned_data.get('quotation')
                    code = detalle_orden_compra_form.cleaned_data.get('code')
                    quantity = detalle_orden_compra_form.cleaned_data.get('quantity')
                    price = detalle_orden_compra_form.cleaned_data.get('price')
                    amount = detalle_orden_compra_form.cleaned_data.get('amount')
                    impuesto = detalle_orden_compra_form.cleaned_data.get('impuesto')
                    if quantity and price and amount and impuesto:
                        try:
                            quotation_detail = QuotationDetail.objects.get(pk=quotation)
                            purchase_order_detail = PurchaseOrderDetail(quotation_detail=quotation_detail,
                                                                      line_number=cont,
                                                                      order=self.object,
                                                                      quantity=quantity,
                                                                      price=price)
                        except QuotationDetail.DoesNotExist:
                            product = Product.objects.get(pk=code)
                            purchase_order_detail = PurchaseOrderDetail(product=product,
                                                                      line_number=cont,
                                                                      order=self.object,
                                                                      quantity=quantity,
                                                                      price=price)
                        detalles.append(purchase_order_detail)
                        cont = cont + 1
                if cont > 1:
                    PurchaseOrderDetail.objects.bulk_create(detalles, reference)
                return HttpResponseRedirect(reverse('compras:purchase_order_detail', args=[self.object.pk]))
        except IntegrityError:
            messages.error(self.request, 'Error guardando la orden de compra.')

    def form_invalid(self, form, detalle_orden_compra_formset):
        return self.render_to_response(self.get_context_data(form=form,
                                                             detalle_orden_compra_formset=detalle_orden_compra_formset))


class CrearOrdenServicios(CreateView):
    form_class = OrdenServiciosForm
    template_name = "compras/orden_servicio.html"
    model = ServiceOrder

    @method_decorator(requiere('compras.add_serviceorder'))
    def dispatch(self, *args, **kwargs):
        return super(CrearOrdenServicios, self).dispatch(*args, **kwargs)

    def get_initial(self):
        initial = super(CrearOrdenServicios, self).get_initial()
        initial['code'] = ServiceOrder.objects.ultimo()
        initial['total'] = 0
        initial['subtotal'] = 0
        initial['impuesto'] = 0
        initial['total_in_words'] = ''
        return initial

    def get(self, request, *args, **kwargs):
        self.object = None
        formas_pago = PaymentMethod.objects.all().order_by('description')
        if not formas_pago:
            return HttpResponseRedirect(reverse('contabilidad:crear_forma_pago'))
        else:
            form_class = self.get_form_class()
            form = self.get_form(form_class)
            detalle_orden_servicios_formset = DetalleOrdenServiciosFormSet()
            return self.render_to_response(self.get_context_data(form=form,
                                                                 detalle_orden_servicios_formset=detalle_orden_servicios_formset))

    def post(self, request, *args, **kwargs):
        self.object = None
        form_class = self.get_form_class()
        form = self.get_form(form_class)
        detalle_orden_servicios_formset = DetalleOrdenServiciosFormSet(request.POST)
        if form.is_valid() and detalle_orden_servicios_formset.is_valid():
            return self.form_valid(form, detalle_orden_servicios_formset)
        else:
            return self.form_invalid(form, detalle_orden_servicios_formset)

    def form_valid(self, form, detalle_orden_servicios_formset):
        try:
            with transaction.atomic():
                self.object = form.save()
                reference = self.object.quotation
                detalles = []
                cont = 1
                for detalle_orden_servicios_form in detalle_orden_servicios_formset:
                    quotation = detalle_orden_servicios_form.cleaned_data.get('quotation')
                    code = detalle_orden_servicios_form.cleaned_data.get('code')
                    quantity = detalle_orden_servicios_form.cleaned_data.get('quantity')
                    price = detalle_orden_servicios_form.cleaned_data.get('price')
                    amount = detalle_orden_servicios_form.cleaned_data.get('amount')
                    if quantity and price and amount:
                        try:
                            quotation_detail = QuotationDetail.objects.get(pk=quotation)
                            service_order_detail = ServiceOrderDetail(quotation_detail=quotation_detail,
                                                                            line_number=cont,
                                                                            order=self.object,
                                                                            quantity=quantity,
                                                                            price=price,
                                                                            amount=amount)
                        except QuotationDetail.DoesNotExist:
                            product = Product.objects.get(pk=code)
                            service_order_detail = ServiceOrderDetail(product=product,
                                                                            line_number=cont,
                                                                            order=self.object,
                                                                            quantity=quantity,
                                                                            price=price,
                                                                            amount=amount)

                        detalles.append(service_order_detail)
                        cont = cont + 1
                ServiceOrderDetail.objects.bulk_create(detalles, reference)
                return HttpResponseRedirect(reverse('compras:service_order_detail', args=[self.object.code]))
        except IntegrityError:
            messages.error(self.request, 'Error guardando la cotizacion.')

    def form_invalid(self, form, detalle_orden_servicios_formset):
        return self.render_to_response(self.get_context_data(form=form,
                                                             detalle_orden_servicios_formset=detalle_orden_servicios_formset))


class CrearConformidadServicio(CreateView):
    form_class = ConformidadServicioForm
    template_name = "compras/conformidad_servicio.html"
    model = ServiceConformity

    @method_decorator(requiere('compras.add_serviceconformity'))
    def dispatch(self, *args, **kwargs):
        return super(CrearConformidadServicio, self).dispatch(*args, **kwargs)

    def get_initial(self):
        initial = super(CrearConformidadServicio, self).get_initial()
        initial['total'] = 0
        initial['subtotal'] = 0
        initial['total_in_words'] = ''
        return initial

    def get(self, request, *args, **kwargs):
        self.object = None
        formas_pago = PaymentMethod.objects.all().order_by('description')
        if not formas_pago:
            return HttpResponseRedirect(reverse('contabilidad:crear_forma_pago'))
        else:
            form_class = self.get_form_class()
            form = self.get_form(form_class)
            detalle_conformidad_servicio_formset = DetalleConformidadServicioFormSet()
            return self.render_to_response(self.get_context_data(form=form,
                                                                 detalle_conformidad_servicio_formset=detalle_conformidad_servicio_formset))

    def post(self, request, *args, **kwargs):
        self.object = None
        form_class = self.get_form_class()
        form = self.get_form(form_class)
        detalle_conformidad_servicio_formset = DetalleConformidadServicioFormSet(request.POST)
        if form.is_valid() and detalle_conformidad_servicio_formset.is_valid():
            return self.form_valid(form, detalle_conformidad_servicio_formset)
        else:
            return self.form_invalid(form, detalle_conformidad_servicio_formset)

    def form_valid(self, form, detalle_conformidad_servicio_formset):
        try:
            with transaction.atomic():
                self.object = form.save()
                reference = self.object.service_order
                detalles = []
                cont = 1
                for detalle_orden_servicios_form in detalle_conformidad_servicio_formset:
                    service_order = detalle_orden_servicios_form.cleaned_data.get('service_order')
                    quantity = detalle_orden_servicios_form.cleaned_data.get('quantity')
                    price = detalle_orden_servicios_form.cleaned_data.get('price')
                    amount = detalle_orden_servicios_form.cleaned_data.get('amount')
                    service_order_detail = ServiceOrderDetail.objects.get(pk=service_order)
                    if quantity and price and amount:
                        detalle_conformidad_servicio = ServiceConformityDetail(
                            service_order_detail=service_order_detail,
                            line_number=cont,
                            conformity=self.object,
                            quantity=quantity)
                        detalles.append(detalle_conformidad_servicio)
                        cont = cont + 1
                ServiceConformityDetail.objects.bulk_create(detalles, reference)
                return HttpResponseRedirect(reverse('compras:detalle_conformidad_servicios', args=[self.object.code]))
        except IntegrityError:
            messages.error(self.request, 'Error guardando la cotizacion.')

    def form_invalid(self, form, detalle_conformidad_servicio_formset):
        return self.render_to_response(self.get_context_data(form=form,
                                                             detalle_conformidad_servicio_form=detalle_conformidad_servicio_formset))


class DetalleProveedor(DetailView):
    model = Supplier
    template_name = 'compras/detalle_proveedor.html'


class DetalleOperacionCotizacion(DetailView):
    model = Quotation
    context_object_name = 'quotation'
    template_name = 'compras/detalle_cotizacion.html'


class DetalleOperacionOrdenCompra(DetailView):
    model = PurchaseOrder
    template_name = 'compras/detalle_orden_compra.html'


class DetalleOperacionOrdenServicios(DetailView):
    model = ServiceOrder
    template_name = 'compras/detalle_orden_servicios.html'


class DetalleOperacionConformidadServicios(DetailView):
    model = ServiceConformity
    template_name = 'compras/detalle_conformidad_servicios.html'


class EliminarCotizacion(TemplateView):
    http_method_names = ['post']

    @method_decorator(requiere('compras.delete_quotation'))
    def dispatch(self, *args, **kwargs):
        return super(EliminarCotizacion, self).dispatch(*args, **kwargs)

    def post(self, request, *args, **kwargs):
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            code = request.POST['code']
            quotation = Quotation.objects.get(code=code)
            cotizacion_json = {}
            cotizacion_json['code'] = code
            ordenes_servicios = quotation.service_orders.all()
            if len(ordenes_servicios) > 0:
                cotizacion_json['ordenes'] = 'SI'
            else:
                cotizacion_json['ordenes'] = 'NO'
                ordenes_compras = quotation.purchase_orders.all()
                if len(ordenes_compras) > 0:
                    cotizacion_json['ordenes'] = 'SI'
                else:
                    cotizacion_json['ordenes'] = 'NO'

                with transaction.atomic():
                    quotation.eliminar_referencia()
                    quotation.eliminar_cotizacion()
                    QuotationDetail.objects.filter(quotation=quotation).delete()
            data = simplejson.dumps(cotizacion_json)
            return HttpResponse(data, 'application/json')


class EliminarOrdenCompra(TemplateView):
    http_method_names = ['post']

    @method_decorator(requiere('compras.delete_purchaseorder'))
    def dispatch(self, *args, **kwargs):
        return super(EliminarOrdenCompra, self).dispatch(*args, **kwargs)

    def post(self, request, *args, **kwargs):
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            code = request.POST['code']
            order = PurchaseOrder.objects.get(code=code)
            movimiento_json = {}
            movimiento_json['code'] = code
            if len(order.movements.all()) > 0:
                movimiento_json['movimientos'] = 'SI'
            else:
                movimiento_json['movimientos'] = 'NO'
                with transaction.atomic():
                    if order.quotation is not None:
                        order.eliminar_referencia()
                    PurchaseOrder.objects.filter(code=code).update(status=PurchaseOrder.STATUS.CANC, quotation=None)
                    PurchaseOrderDetail.objects.filter(order=order).delete()
            data = simplejson.dumps(movimiento_json)
            return HttpResponse(data, 'application/json')


class EliminarOrdenServicios(TemplateView):
    http_method_names = ['post']

    @method_decorator(requiere('compras.delete_serviceorder'))
    def dispatch(self, *args, **kwargs):
        return super(EliminarOrdenServicios, self).dispatch(*args, **kwargs)

    def post(self, request, *args, **kwargs):
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            code = request.POST['code']
            order = ServiceOrder.objects.get(code=code)
            orden_json = {}
            orden_json['code'] = code
            if len(order.conformities.all()) > 0:
                orden_json['conformidades'] = 'SI'
            else:
                orden_json['conformidades'] = 'NO'
                with transaction.atomic():
                    if order.quotation is not None:
                        order.eliminar_referencia()
                    ServiceOrder.objects.filter(code=code).update(status=ServiceOrder.STATUS.CANC,
                                                                        quotation=None)
                    ServiceOrderDetail.objects.filter(order=order).delete()
            data = simplejson.dumps(orden_json)
            return HttpResponse(data, 'application/json')


class EliminarConformidadServicio(TemplateView):
    http_method_names = ['post']

    @method_decorator(requiere('compras.delete_serviceconformity'))
    def dispatch(self, *args, **kwargs):
        return super(EliminarConformidadServicio, self).dispatch(*args, **kwargs)

    def post(self, request, *args, **kwargs):
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            code = request.POST['code']
            conformity = ServiceConformity.objects.get(code=code)
            conformidad_json = {}
            conformidad_json['code'] = code
            with transaction.atomic():
                if conformity.service_order is not None:
                    conformity.eliminar_referencia()
                ServiceConformity.objects.filter(code=code).update(is_active=False)
                ServiceConformityDetail.objects.filter(conformity=conformity).delete()
            data = simplejson.dumps(conformidad_json)
            return HttpResponse(data, 'application/json')


class EliminarProveedor(TemplateView):
    http_method_names = ['post']

    @method_decorator(requiere('compras.delete_supplier'))
    def dispatch(self, *args, **kwargs):
        return super(EliminarProveedor, self).dispatch(*args, **kwargs)

    def post(self, request, *args, **kwargs):
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            tax_id = request.POST['tax_id']
            proveedor_json = {}
            proveedor_json['tax_id'] = tax_id
            Supplier.objects.filter(pk=tax_id).update(is_active=False)
            data = simplejson.dumps(proveedor_json)
            return HttpResponse(data, 'application/json')


class ListadoProveedores(ListView):
    model = Supplier
    template_name = 'compras/proveedores.html'
    context_object_name = 'proveedores'
    queryset = Supplier.objects.filter(is_active=True).order_by('business_name')

    @method_decorator(requiere('compras.ver_tabla_proveedores'))
    def dispatch(self, *args, **kwargs):
        return super(ListadoProveedores, self).dispatch(*args, **kwargs)


class ListadoCotizaciones(ListView):
    model = Quotation
    template_name = 'compras/cotizaciones.html'
    context_object_name = 'cotizaciones'
    queryset = Quotation.objects.exclude(status=Quotation.STATUS.CANC).order_by('code')

    @method_decorator(requiere('compras.ver_tabla_cotizaciones'))
    def dispatch(self, *args, **kwargs):
        return super(ListadoCotizaciones, self).dispatch(*args, **kwargs)


class ListadoOrdenesCompra(ListView):
    model = PurchaseOrder
    template_name = 'compras/ordenes_compra.html'
    context_object_name = 'ordenes_compra'
    queryset = PurchaseOrder.objects.exclude(status=PurchaseOrder.STATUS.CANC).order_by('code')

    @method_decorator(
        requiere('compras.ver_tabla_ordenes_compra'))
    def dispatch(self, *args, **kwargs):
        return super(ListadoOrdenesCompra, self).dispatch(*args, **kwargs)


class ListadoOrdenesServicios(ListView):
    model = ServiceOrder
    template_name = 'compras/ordenes_servicios.html'
    context_object_name = 'ordenes_servicios'
    queryset = ServiceOrder.objects.filter().order_by('code')

    @method_decorator(
        requiere('compras.ver_tabla_ordenes_servicios'))
    def dispatch(self, *args, **kwargs):
        return super(ListadoOrdenesServicios, self).dispatch(*args, **kwargs)


class ListadoOrdenesCompraPorCotizacion(ListView):
    model = PurchaseOrder
    template_name = 'compras/ordenes_compra.html'
    context_object_name = 'ordenes_compra'

    @method_decorator(
        requiere('compras.ver_tabla_ordenes_compra'))
    def dispatch(self, *args, **kwargs):
        return super(ListadoOrdenesCompraPorCotizacion, self).dispatch(*args, **kwargs)

    def get_queryset(self):
        quotation = Quotation.objects.get(pk=self.kwargs['quotation'])
        queryset = quotation.purchase_orders.all()
        return queryset


class ListadoOrdenesServiciosPorCotizacion(ListView):
    model = PurchaseOrder
    template_name = 'compras/ordenes_servicios.html'
    context_object_name = 'ordenes_servicios'

    @method_decorator(
        requiere('compras.ver_tabla_ordenes_servicios'))
    def dispatch(self, *args, **kwargs):
        return super(ListadoOrdenesServiciosPorCotizacion, self).dispatch(*args, **kwargs)

    def get_queryset(self):
        quotation = Quotation.objects.get(pk=self.kwargs['quotation'])
        queryset = quotation.service_orders.all()
        return queryset


class ListadoConformidadesServicio(ListView):
    model = ServiceConformity
    template_name = 'compras/conformidades_servicio.html'
    context_object_name = 'conformidades'
    queryset = ServiceConformity.objects.filter(is_active=True).order_by('code')

    @method_decorator(
        requiere('compras.ver_tabla_conformidades_servicio'))
    def dispatch(self, *args, **kwargs):
        return super(ListadoConformidadesServicio, self).dispatch(*args, **kwargs)


class ListadoMovimientosPorOrdenCompra(ListView):
    template_name = 'almacen/movimientos.html'
    context_object_name = 'movimientos'

    @method_decorator(requiere('almacen.ver_tabla_movimientos'))
    def dispatch(self, *args, **kwargs):
        return super(ListadoMovimientosPorOrdenCompra, self).dispatch(*args, **kwargs)

    def get_queryset(self):
        orden_compra = PurchaseOrder.objects.get(pk=self.kwargs['order'])
        queryset = orden_compra.movements.all()
        return queryset


class ListadoConformidadesPorOrdenServicios(ListView):
    template_name = 'compras/conformidades_servicio.html'
    context_object_name = 'conformidades'

    @method_decorator(
        requiere('compras.ver_tabla_conformidades_servicio'))
    def dispatch(self, *args, **kwargs):
        return super(ListadoConformidadesPorOrdenServicios, self).dispatch(*args, **kwargs)

    def get_queryset(self):
        service_order = ServiceOrder.objects.get(pk=self.kwargs['order'])
        queryset = service_order.conformities.all()
        return queryset


class ModificarProveedor(UpdateView):
    model = Supplier
    context_object_name = 'supplier'
    template_name = 'compras/proveedor.html'
    form_class = ProveedorForm

    @method_decorator(requiere('compras.change_supplier'))
    def dispatch(self, *args, **kwargs):
        return super(ModificarProveedor, self).dispatch(*args, **kwargs)

    def get_success_url(self):
        return reverse('compras:detalle_proveedor', args=[self.object.pk])

    def get_initial(self):
        initial = super(ModificarProveedor, self).get_initial()
        initial['registration_date'] = self.object.registration_date.strftime('%d/%m/%Y')
        return initial


class ModificarCotizacion(UpdateView):
    form_class = CotizacionForm
    template_name = "compras/cotizacion.html"
    model = Quotation
    context_object_name = 'quotation'

    @method_decorator(requiere('compras.change_quotation'))
    def dispatch(self, *args, **kwargs):
        quotation = self.get_object()
        if quotation.status == Quotation.STATUS.PEND:
            return super(ModificarCotizacion, self).dispatch(*args, **kwargs)
        else:
            return HttpResponseRedirect(reverse('seguridad:permiso_denegado'))

    def get_initial(self):
        initial = super(ModificarCotizacion, self).get_initial()
        quotation = self.object
        initial['code'] = quotation.code
        initial['tax_id'] = quotation.supplier.tax_id
        initial['business_name'] = quotation.supplier.business_name
        initial['address'] = quotation.supplier.address
        initial['date'] = quotation.date.strftime('%d/%m/%Y')
        initial['reference'] = quotation.requirement
        initial['notes'] = quotation.notes
        return initial

    def get_context_data(self, **kwargs):
        quotation = self.object
        detalles = QuotationDetail.objects.filter(quotation=quotation).order_by('line_number')
        cant_detalles = detalles.count()
        context = super(ModificarCotizacion, self).get_context_data(**kwargs)
        context['quotation'] = quotation
        context['detalles'] = detalles
        context['cant_detalles'] = cant_detalles
        return context

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        form_class = self.get_form_class()
        form = self.get_form(form_class)
        detalles = QuotationDetail.objects.filter(quotation=self.object).order_by('line_number')
        detalles_data = []
        for detalle in detalles:
            d = {'requirement': detalle.requirement_detail.pk,
                 'code': detalle.requirement_detail.product.code,
                 'name': detalle.requirement_detail.product.description,
                 'unidad': detalle.requirement_detail.product.unit_of_measure.code,
                 'quantity': detalle.quantity}
            detalles_data.append(d)
        detalle_cotizacion_formset = DetalleCotizacionFormSet(initial=detalles_data)
        return self.render_to_response(self.get_context_data(form=form,
                                                             detalle_cotizacion_formset=detalle_cotizacion_formset))

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        form_class = self.get_form_class()
        form = self.get_form(form_class)
        detalle_cotizacion_formset = DetalleCotizacionFormSet(request.POST)
        if form.is_valid() and detalle_cotizacion_formset.is_valid():
            return self.form_valid(form, detalle_cotizacion_formset)
        else:
            return self.form_invalid(form, detalle_cotizacion_formset)

    def form_valid(self, form, detalle_cotizacion_formset):
        try:
            with transaction.atomic():
                self.object.eliminar_referencia()
                form.save()
                detalles = []
                cont = 1
                for detalle_cotizacion_form in detalle_cotizacion_formset:
                    requirement_detail = detalle_cotizacion_form.cleaned_data.get('requirement')
                    quantity = detalle_cotizacion_form.cleaned_data.get('quantity')
                    requirement_detail = RequirementDetail.objects.get(pk=requirement_detail)
                    if quantity:
                        quotation_detail = QuotationDetail(requirement_detail=requirement_detail,
                                                               line_number=cont,
                                                               quotation=self.object,
                                                               quantity=quantity)
                        detalles.append(quotation_detail)
                        cont = cont + 1
                QuotationDetail.objects.bulk_create(detalles, self.object.requirement)
                return HttpResponseRedirect(reverse('compras:quotation_detail', args=[self.object.code]))
        except IntegrityError:
            messages.error(self.request, 'Error guardando el requerimiento.')

    def form_invalid(self, form, detalle_cotizacion_formset):
        return self.render_to_response(self.get_context_data(form=form))


class ModificarConformidadServicio(UpdateView):
    template_name = 'compras/conformidad_servicio.html'
    form_class = ConformidadServicioForm
    model = ServiceConformity

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        form_class = self.get_form_class()
        form = self.get_form(form_class)
        return self.render_to_response(self.get_context_data(form=form))

    def get_initial(self):
        initial = super(ModificarConformidadServicio, self).get_initial()
        conformity = self.object
        initial['cod_conformidad_servicio'] = conformity.code
        initial['service_order'] = conformity.service_order
        initial['supporting_document'] = conformity.supporting_document
        initial['date'] = conformity.date.strftime('%d/%m/%Y')
        return initial

    def get_context_data(self, **kwargs):
        conformity = self.object
        detalles = ServiceConformityDetail.objects.filter(conformity=conformity)
        cant_detalles = detalles.count()
        context = super(ModificarConformidadServicio, self).get_context_data(**kwargs)
        context['conformity'] = conformity
        context['detalles'] = detalles
        context['cant_detalles'] = cant_detalles
        return context

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        form_class = self.get_form_class()
        form = self.get_form(form_class)
        if form.is_valid():
            return self.form_valid(form)
        else:
            return self.form_invalid(form)

    def form_valid(self, form):
        try:
            with transaction.atomic():
                self.eliminar_referencia()
                form.save()
                return HttpResponseRedirect(reverse('compras:quotation_detail', args=[self.object.code]))
        except IntegrityError:
            messages.error(self.request, 'Error guardando el requerimiento.')


class ModificarOrdenCompra(UpdateView):
    template_name = 'compras/orden_compra.html'
    form_class = OrdenCompraForm
    model = PurchaseOrder

    @method_decorator(requiere('compras.change_purchaseorder'))
    def dispatch(self, *args, **kwargs):
        orden_compra = self.get_object()
        if orden_compra.status == PurchaseOrder.STATUS.PEND:
            return super(ModificarOrdenCompra, self).dispatch(*args, **kwargs)
        else:
            return HttpResponseRedirect(reverse('seguridad:permiso_denegado'))

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        if self.object.status == PurchaseOrder.STATUS.PEND:
            form_class = self.get_form_class()
            form = self.get_form(form_class)
            detalles = (PurchaseOrderDetail.objects.filter(order=self.object)
                        .select_related('order', 'product__unit_of_measure',
                                        'quotation_detail__requirement_detail__product__unit_of_measure')
                        .order_by('line_number'))
            detalles_data = []
            for detalle in detalles:
                try:
                    d = {'quotation': detalle.quotation_detail.pk,
                         'code': detalle.quotation_detail.requirement_detail.product.code,
                         'name': detalle.quotation_detail.requirement_detail.product.description,
                         'unidad': detalle.quotation_detail.requirement_detail.product.unit_of_measure.code,
                         'quantity': detalle.quantity,
                         'price': detalle.price,
                         'impuesto': detalle.impuesto,
                         'amount': detalle.amount}
                except (ObjectDoesNotExist, AttributeError):
                    d = {'quotation': '0',
                         'code': detalle.product.code,
                         'name': detalle.product.description,
                         'unidad': detalle.product.unit_of_measure.code,
                         'quantity': detalle.quantity,
                         'price': detalle.price,
                         'impuesto': detalle.impuesto,
                         'amount': detalle.valor_sin_igv}
                detalles_data.append(d)
            detalle_orden_compra_formset = DetalleOrdenCompraFormSet(initial=detalles_data)
            return self.render_to_response(self.get_context_data(form=form,
                                                                 detalle_orden_compra_formset=detalle_orden_compra_formset))
        else:
            return HttpResponseRedirect(reverse('compras:ordenes_compra'))

    def get_initial(self):
        initial = super(ModificarOrdenCompra, self).get_initial()
        order = self.object
        quotation = order.quotation
        if quotation is None:
            supplier = order.supplier
        else:
            supplier = order.quotation.supplier
        initial['code'] = order.code
        initial['tax_id'] = supplier.tax_id
        initial['business_name'] = supplier.business_name
        initial['address'] = supplier.address
        initial['date'] = order.date.strftime('%d/%m/%Y')
        initial['formas_pago'] = order.payment_method
        initial['reference'] = order.quotation
        try:
            monto_impuesto = purchase_tax().amount
        except AttributeError:
            return HttpResponseRedirect(reverse('contabilidad:configuracion'))
        initial['impuesto_actual'] = monto_impuesto
        initial['total'] = order.total
        initial['subtotal'] = order.subtotal
        initial['impuesto'] = order.impuesto
        initial['total_in_words'] = order.total_in_words
        initial['notes'] = order.notes
        return initial

    def get_context_data(self, **kwargs):
        order = self.object
        context = super(ModificarOrdenCompra, self).get_context_data(**kwargs)
        context['order'] = order
        return context

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        form_class = self.get_form_class()
        form = self.get_form(form_class)
        detalle_orden_compra_formset = DetalleOrdenCompraFormSet(request.POST)
        if form.is_valid() and detalle_orden_compra_formset.is_valid():
            return self.form_valid(form, detalle_orden_compra_formset)
        else:
            return self.form_invalid(form, detalle_orden_compra_formset)

    def form_valid(self, form, detalle_orden_compra_formset):
        try:
            with transaction.atomic():
                if self.object.quotation is not None:
                    self.object.eliminar_referencia()
                PurchaseOrderDetail.objects.filter(order=self.object).delete()
                self.object = form.save()
                reference = self.object.quotation
                detalles = []
                cont = 1
                for detalle_orden_compra_form in detalle_orden_compra_formset:
                    quotation = detalle_orden_compra_form.cleaned_data.get('quotation')
                    code = detalle_orden_compra_form.cleaned_data.get('code')
                    quantity = detalle_orden_compra_form.cleaned_data.get('quantity')
                    price = detalle_orden_compra_form.cleaned_data.get('price')
                    amount = detalle_orden_compra_form.cleaned_data.get('amount')
                    impuesto = detalle_orden_compra_form.cleaned_data.get('impuesto')
                    if quantity and price and amount and impuesto:
                        try:
                            quotation_detail = QuotationDetail.objects.get(pk=quotation)
                            purchase_order_detail = PurchaseOrderDetail(quotation_detail=quotation_detail,
                                                                      line_number=cont,
                                                                      order=self.object,
                                                                      quantity=quantity,
                                                                      price=price)
                        except QuotationDetail.DoesNotExist:
                            product = Product.objects.get(pk=code)
                            purchase_order_detail = PurchaseOrderDetail(product=product,
                                                                      line_number=cont,
                                                                      order=self.object,
                                                                      quantity=quantity,
                                                                      price=price)
                        detalles.append(purchase_order_detail)
                        cont = cont + 1
                        if cont > 1:
                            PurchaseOrderDetail.objects.bulk_create(detalles, reference)
                return HttpResponseRedirect(reverse('compras:purchase_order_detail', args=[self.object.pk]))
        except IntegrityError:
            messages.error(self.request, 'Error guardando la cotizacion.')

    def form_invalid(self, form, detalle_orden_compra_formset):
        return self.render_to_response(self.get_context_data(form=form,
                                                             detalle_orden_compra_formset=detalle_orden_compra_formset))


class ModificarOrdenServicios(UpdateView):
    template_name = 'compras/orden_servicio.html'
    form_class = OrdenServiciosForm
    model = ServiceOrder

    @method_decorator(requiere('compras.change_serviceorder'))
    def dispatch(self, *args, **kwargs):
        service_order = self.get_object()
        if service_order.status == ServiceOrder.STATUS.PEND:
            return super(ModificarOrdenServicios, self).dispatch(*args, **kwargs)
        else:
            return HttpResponseRedirect(reverse('seguridad:permiso_denegado'))

    def get_initial(self):
        initial = super(ModificarOrdenServicios, self).get_initial()
        order = self.object
        quotation = order.quotation
        if quotation is None:
            supplier = order.supplier
        else:
            supplier = order.quotation.supplier
        initial['code'] = order.code
        initial['tax_id'] = supplier.tax_id
        initial['business_name'] = supplier.business_name
        initial['address'] = supplier.address
        initial['date'] = order.date.strftime('%d/%m/%Y')
        initial['formas_pago'] = order.payment_method
        initial['reference'] = order.quotation
        initial['process'] = order.process
        initial['total'] = order.total
        initial['subtotal'] = order.subtotal
        initial['impuesto'] = order.impuesto
        initial['total_in_words'] = order.total_in_words
        initial['notes'] = order.notes
        return initial

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        if self.object.status == PurchaseOrder.STATUS.PEND:
            form_class = self.get_form_class()
            form = self.get_form(form_class)
            detalles = ServiceOrderDetail.objects.filter(order=self.object).order_by('line_number')
            detalles_data = []
            for detalle in detalles:
                try:
                    d = {'quotation': detalle.quotation_detail.pk,
                         'code': detalle.quotation_detail.requirement_detail.product.code,
                         'name': detalle.quotation_detail.requirement_detail.product.description,
                         'unidad': detalle.quotation_detail.requirement_detail.product.unit_of_measure.code,
                         'quantity': detalle.quantity,
                         'price': detalle.price,
                         'amount': detalle.amount}
                except (ObjectDoesNotExist, AttributeError):
                    d = {'quotation': '0',
                         'code': detalle.product.code,
                         'name': detalle.product.description,
                         'unidad': detalle.product.unit_of_measure.code,
                         'quantity': detalle.quantity,
                         'price': detalle.price,
                         'amount': detalle.amount}
                detalles_data.append(d)
            detalle_orden_servicios_formset = DetalleOrdenServiciosFormSet(initial=detalles_data)
            return self.render_to_response(self.get_context_data(form=form,
                                                                 detalle_orden_servicios_formset=detalle_orden_servicios_formset))
        else:
            return HttpResponseRedirect(reverse('compras:ordenes_compra'))

    def get_context_data(self, **kwargs):
        order = self.object
        context = super(ModificarOrdenServicios, self).get_context_data(**kwargs)
        context['order'] = order
        return context

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        form_class = self.get_form_class()
        form = self.get_form(form_class)
        detalle_orden_servicios_formset = DetalleOrdenServiciosFormSet(request.POST)
        if form.is_valid() and detalle_orden_servicios_formset.is_valid():
            return self.form_valid(form, detalle_orden_servicios_formset)
        else:
            return self.form_invalid(form, detalle_orden_servicios_formset)

    def form_valid(self, form, detalle_orden_servicios_formset):
        # try:
        with transaction.atomic():
            if self.object.quotation is not None:
                self.object.eliminar_referencia()
            ServiceOrderDetail.objects.filter(order=self.object).delete()
            self.object = form.save()
            reference = self.object.quotation
            detalles = []
            cont = 1
            for detalle_orden_servicios_form in detalle_orden_servicios_formset:
                quotation = detalle_orden_servicios_form.cleaned_data.get('quotation')
                code = detalle_orden_servicios_form.cleaned_data.get('code')
                quantity = detalle_orden_servicios_form.cleaned_data.get('quantity')
                price = detalle_orden_servicios_form.cleaned_data.get('price')
                amount = detalle_orden_servicios_form.cleaned_data.get('amount')
                if quantity and price and amount:
                    try:
                        quotation_detail = QuotationDetail.objects.get(pk=quotation)
                        service_order_detail = ServiceOrderDetail(quotation_detail=quotation_detail,
                                                                        line_number=cont,
                                                                        order=self.object,
                                                                        quantity=quantity,
                                                                        price=price,
                                                                        amount=amount)
                    except ObjectDoesNotExist:
                        product = Product.objects.get(pk=code)
                        service_order_detail = ServiceOrderDetail(product=product,
                                                                        line_number=cont,
                                                                        order=self.object,
                                                                        quantity=quantity,
                                                                        price=price,
                                                                        amount=amount)
                    detalles.append(service_order_detail)
                    cont = cont + 1
            ServiceOrderDetail.objects.bulk_create(detalles, reference)
            return HttpResponseRedirect(reverse('compras:service_order_detail', args=[self.object.code]))
            # except IntegrityError:
            # messages.error(self.request, 'Error guardando la Orden de Servicios.')

    def form_invalid(self, form, detalle_orden_servicios_formset):
        return self.render_to_response(self.get_context_data(form=form,
                                                             detalle_orden_servicios_formset=detalle_orden_servicios_formset))


class ObtenerDetalleCotizacion(SoloAjaxMixin, TemplateView):

    parametros_requeridos = ('quotation', 'tipo_busqueda')

    def get(self, request, *args, **kwargs):
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            quotation = request.GET['quotation']
            tipo_busqueda = request.GET['tipo_busqueda']
            if tipo_busqueda == 'PRODUCTOS':
                detalles = QuotationDetail.objects.filter(
                    Q(status=QuotationDetail.STATUS.PEND) | Q(status=QuotationDetail.STATUS.ELEG_PARC),
                    quotation__code=quotation,
                    requirement_detail__product__is_service=False).order_by('line_number')
                try:
                    monto_impuesto = purchase_tax().amount
                except AttributeError:
                    monto_impuesto = 0
            elif tipo_busqueda == 'SERVICIOS':
                monto_impuesto = 1
                detalles = QuotationDetail.objects.filter(quotation__code=quotation,
                                                            requirement_detail__product__is_service=True).order_by(
                    'line_number')

            lista_detalles = []
            for detalle in detalles:
                det = {}
                det['quotation'] = detalle.id
                try:
                    det['code'] = detalle.requirement_detail.product.code
                    det['name'] = detalle.requirement_detail.product.description
                    det['price'] = str(detalle.requirement_detail.product.price)
                    quantity = detalle.quantity - detalle.requirement_detail.purchased_quantity
                    det['quantity'] = str(quantity)
                    amount = detalle.requirement_detail.product.price * quantity
                    if tipo_busqueda == 'PRODUCTOS':
                        det['unidad'] = detalle.requirement_detail.product.unit_of_measure.code
                        base = amount / (monto_impuesto + 1)
                        det['impuesto'] = str(round(amount - base, 5))
                        det['amount'] = str(round(amount, 5))
                    elif tipo_busqueda == 'SERVICIOS':
                        det['unidad'] = detalle.requirement_detail.product.unit_of_measure.code
                        det['amount'] = str(round(amount))
                    lista_detalles.append(det)
                except (ObjectDoesNotExist, AttributeError):
                    pass
            if tipo_busqueda == 'PRODUCTOS':
                formset = DetalleOrdenCompraFormSet(initial=lista_detalles)
            elif tipo_busqueda == 'SERVICIOS':
                formset = DetalleOrdenServiciosFormSet(initial=lista_detalles)
            lista_json = []
            if tipo_busqueda == 'PRODUCTOS':
                for form in formset:
                    detalle_json = {}
                    detalle_json['quotation'] = str(form['quotation'])
                    detalle_json['code'] = str(form['code'])
                    detalle_json['name'] = str(form['name'])
                    detalle_json['price'] = str(form['price'])
                    detalle_json['unidad'] = str(form['unidad'])
                    detalle_json['quantity'] = str(form['quantity'])
                    detalle_json['impuesto'] = str(form['impuesto'])
                    detalle_json['amount'] = str(form['amount'])
                    lista_json.append(detalle_json)
            elif tipo_busqueda == 'SERVICIOS':
                for form in formset:
                    detalle_json = {}
                    detalle_json['quotation'] = str(form['quotation'])
                    detalle_json['code'] = str(form['code'])
                    detalle_json['name'] = str(form['name'])
                    detalle_json['price'] = str(form['price'])
                    detalle_json['unidad'] = str(form['unidad'])
                    detalle_json['quantity'] = str(form['quantity'])
                    detalle_json['amount'] = str(form['amount'])
                    lista_json.append(detalle_json)
            data = json.dumps(lista_json)
            return HttpResponse(data, 'application/json')


class ObtenerDetalleOrdenCompra(SoloAjaxMixin, TemplateView):

    parametros_requeridos = ('orden_compra', 'date')

    def obtener_date(self, r_date):
        anio = int(r_date[6:])
        month = int(r_date[3:5])
        dia = int(r_date[0:2])
        date = datetime.date(anio, month, dia)
        return date

    def get(self, request, *args, **kwargs):
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            orden_compra = PurchaseOrder.objects.get(code=request.GET['orden_compra'])
            date = self.obtener_date(request.GET['date'])
            tipo_cambio = 1
            if orden_compra.in_dollars:
                try:
                    tipo_cambio = ExchangeRate.objects.get(date=date).amount
                except ExchangeRate.DoesNotExist:
                    tipo_cambio = 0
            lista_detalles = []
            lista_json = []
            if tipo_cambio > 0:
                detalles = PurchaseOrderDetail.objects.filter(order=orden_compra,
                                                             status=PurchaseOrderDetail.STATUS.PEND).order_by(
                    'line_number')
                for detalle in detalles:
                    det = {}
                    det['orden_compra'] = detalle.id
                    try:
                        det['code'] = detalle.quotation_detail.requirement_detail.product.code
                        det['name'] = detalle.quotation_detail.requirement_detail.product.description
                        det['quantity'] = str(detalle.quantity - detalle.received_quantity)
                        det['price'] = str(round(Decimal(detalle.precio_sin_igv) * tipo_cambio, 5))
                        det['unidad'] = detalle.quotation_detail.requirement_detail.product.unit_of_measure.code
                        det['amount'] = str(round(Decimal(detalle.valor_sin_igv) * tipo_cambio, 5))
                    except (ObjectDoesNotExist, AttributeError):
                        det['code'] = detalle.product.code
                        det['name'] = detalle.product.description
                        det['quantity'] = str(detalle.quantity - detalle.received_quantity)
                        det['price'] = str(round(Decimal(detalle.precio_sin_igv) * tipo_cambio, 5))
                        det['unidad'] = detalle.product.unit_of_measure.code
                        det['amount'] = str(round(Decimal(detalle.valor_sin_igv) * tipo_cambio, 5))
                    lista_detalles.append(det)
                formset = DetalleIngresoFormSet(initial=lista_detalles)
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


class ObtenerDetalleOrdenServicios(SoloAjaxMixin, TemplateView):

    parametros_requeridos = ('service_order',)

    def get(self, request, *args, **kwargs):
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            service_order = request.GET['service_order']
            detalles = ServiceOrderDetail.objects.filter(order__code=service_order,
                                                            status=ServiceOrderDetail.STATUS.PEND).order_by(
                'line_number')
            lista_detalles = []
            for detalle in detalles:
                try:
                    det = {}
                    det['service_order'] = detalle.id
                    det['code'] = detalle.quotation_detail.requirement_detail.product.code
                    det['servicio'] = detalle.quotation_detail.requirement_detail.product.description
                    det['use'] = detalle.quotation_detail.requirement_detail.use
                    det['price'] = str(detalle.price)
                    det['quantity'] = str(detalle.quantity)
                    det['amount'] = str(detalle.amount)
                except (ObjectDoesNotExist, AttributeError):
                    det = {}
                    det['service_order'] = detalle.id
                    det['code'] = detalle.product.code
                    det['servicio'] = detalle.product.description
                    det['use'] = detalle.product.unit_of_measure.description
                    det['price'] = str(detalle.price)
                    det['quantity'] = str(detalle.quantity)
                    det['amount'] = str(detalle.amount)
                lista_detalles.append(det)
            formset = DetalleConformidadServicioFormSet(initial=lista_detalles)
            lista_json = []
            for form in formset:
                detalle_json = {}
                detalle_json['service_order'] = str(form['service_order'])
                detalle_json['servicio'] = str(form['servicio'])
                detalle_json['use'] = str(form['use'])
                detalle_json['price'] = str(form['price'])
                detalle_json['quantity'] = str(form['quantity'])
                detalle_json['amount'] = str(form['amount'])
                lista_json.append(detalle_json)
            data = json.dumps(lista_json)
            return HttpResponse(data, 'application/json')


"""class ReportePDFOrdenCompra(View):
    
    def get(self, request, *args, **kwargs): 
        code = kwargs['pk']
        order = PurchaseOrder.objects.get(code=code)        
        response = HttpResponse(content_type='application/pdf')                
        reporte = ReporteOrdenCompra('A4',order)
        pdf = reporte.imprimir()        
        response.write(pdf)
        return response"""


class ReportePDFOrdenCompra(View):

    def get(self, request, *args, **kwargs):
        order = PurchaseOrder.objects.get(pk=kwargs['pk'])
        response = HttpResponse(content_type='application/pdf')
        response.write(PDFOrdenCompra().imprimir(order))
        return response


class ReporteXLSOrdenCompra(TemplateView):

    def get(self, request, *args, **kwargs):
        order = get_object_or_404(PurchaseOrder, pk=kwargs['pk'])
        wb = reporte_xls_orden_compra(order)
        response = HttpResponse(content_type="application/ms-excel")
        nombre_archivo = "ORDEN_DE_COMPRA_N°.xlsx"
        response["Content-Disposition"] = "attachment; filename={0}".format(nombre_archivo)
        wb.save(response)
        return response


class ReportePDFOrdenServicios(View):

    def get(self, request, *args, **kwargs):
        order = ServiceOrder.objects.get(code=kwargs['code'])
        response = HttpResponse(content_type='application/pdf')
        response.write(PDFOrdenServicios().imprimir(order))
        return response


class ReportePDFMemorandoConformidadServicio(View):

    def get(self, request, *args, **kwargs):
        conformity = ServiceConformity.objects.get(code=kwargs['code'])
        response = HttpResponse(content_type='application/pdf')
        response.write(PDFMemorandoConformidadServicio().imprimir(conformity))
        return response


class ReportePDFSolicitudCotizacion(View):

    def get(self, request, *args, **kwargs):
        quotation = Quotation.objects.get(code=kwargs['code'])
        response = HttpResponse(content_type='application/pdf')
        response.write(PDFSolicitudCotizacion().imprimir(quotation))
        return response


class ReporteExcelProveedores(TemplateView):

    def get(self, request, *args, **kwargs):
        proveedores = Supplier.objects.all().order_by('tax_id')
        wb = Workbook()
        ws = wb.active
        ws['B1'] = 'REPORTE DE PROVEEDORES'
        ws.merge_cells('B1:J1')
        ws['B3'] = 'RUC'
        ws['C3'] = 'RAZON_SOCIAL'
        ws['D3'] = 'DIRECCION'
        ws['E3'] = 'TELEFONO'
        ws['F3'] = 'CORREO'
        ws['G3'] = 'ESTADO_SUNAT'
        ws['H3'] = 'CONDICIÓN'
        ws['I3'] = 'REPRESENTANTE'
        ws['J3'] = 'CIIU'
        ws['K3'] = 'FECHA_ALTA'
        cont = 4
        for supplier in proveedores:
            ws.cell(row=cont, column=2).value = supplier.tax_id
            ws.cell(row=cont, column=3).value = supplier.business_name
            ws.cell(row=cont, column=4).value = supplier.address
            ws.cell(row=cont, column=5).value = supplier.phone
            ws.cell(row=cont, column=6).value = supplier.email
            ws.cell(row=cont, column=7).value = supplier.sunat_status
            ws.cell(row=cont, column=8).value = supplier.sunat_condition
            try:
                ws.cell(row=cont, column=9).value = supplier.representante.name
            except ObjectDoesNotExist:
                ws.cell(row=cont, column=9).value = '-'
            ws.cell(row=cont, column=10).value = supplier.ciiu
            ws.cell(row=cont, column=11).value = supplier.registration_date
            ws.cell(row=cont, column=11).number_format = 'dd/mm/yyyy'
            cont = cont + 1
        nombre_archivo = "ListadoProveedores.xlsx"
        response = HttpResponse(content_type="application/ms-excel")
        contenido = "attachment; filename={0}".format(nombre_archivo)
        response["Content-Disposition"] = contenido
        wb.save(response)
        return response


class ReporteExcelOrdenesServiciosFecha(FormView):
    form_class = FormularioReporteOrdenesFecha
    template_name = "compras/reporte_ordenes.html"

    def form_valid(self, form):
        data = form.cleaned_data
        tipo_busqueda = data['tipo_busqueda']
        wb = Workbook()
        ws = wb.active
        if tipo_busqueda == 'F':
            p_start_date = data['start_date']
            p_fecha_final = data['end_date']
            anio = int(p_start_date[6:])
            month = int(p_start_date[3:5])
            dia = int(p_start_date[0:2])
            start_date = timezone.make_aware(datetime.datetime(anio, month, dia, 23, 59, 59))
            anio = int(p_fecha_final[6:])
            month = int(p_fecha_final[3:5])
            dia = int(p_fecha_final[0:2])
            fecha_final = timezone.make_aware(datetime.datetime(anio, month, dia, 23, 59, 59))
            ws['B2'] = 'REPORTE DE ORDENES DE SERVICIOS POR FECHA'
            ws.merge_cells('B2:H2')
            ws['B3'] = 'DESDE'
            ws['C3'] = p_start_date
            ws['C3'].number_format = 'dd/mm/yyyy'
            ws['D3'] = 'HASTA'
            ws['E3'] = p_fecha_final
            ws['F3'].number_format = 'dd/mm/yyyy'
            ordenes_servicios = ServiceOrder.objects.filter(date__range=[start_date, fecha_final])
        elif tipo_busqueda == 'M':
            month = data['month'].strip()
            year = data['year'].strip()
            ws['B2'] = 'REPORTE DE ORDENES DE SERVICIOS POR MES'
            ws.merge_cells('B2:H2')
            ws['B3'] = 'MES'
            ws['C3'] = month
            ws['D3'] = 'AÑO'
            ws['E3'] = year
            ordenes_servicios = ServiceOrder.objects.filter(date__month=month, date__year=year)
        elif tipo_busqueda == 'A':
            year = data['year'].strip()
            ws['B2'] = 'REPORTE DE ORDENES DE SERVICIOS POR AÑO'
            ws.merge_cells('B2:H2')
            ws['B3'] = 'AÑO'
            ws['C3'] = year
            ordenes_servicios = ServiceOrder.objects.filter(date__year=year)
        ws['B5'] = 'CODIGO'
        ws['C5'] = 'FECHA'
        ws['D5'] = 'PROVEEDOR'
        ws['E5'] = 'IMPORTE'
        ws['F5'] = 'FORMA_PAGO'
        ws['G5'] = 'CREADO'
        ws['H5'] = 'ESTADO'
        ordenes_servicios = ordenes_servicios.select_related(
            'supplier', 'payment_method', 'quotation__supplier'
        ).prefetch_related('details')
        cont = 6
        for order in ordenes_servicios:
            ws.cell(row=cont, column=2).value = order.code
            ws.cell(row=cont, column=3).value = order.date
            ws.cell(row=cont, column=3).number_format = 'dd/mm/yyyy'
            try:
                ws.cell(row=cont, column=4).value = order.quotation.supplier.business_name
            except ObjectDoesNotExist:
                ws.cell(row=cont, column=4).value = order.supplier.business_name
            ws.cell(row=cont, column=5).value = order.total
            ws.cell(row=cont, column=6).value = order.payment_method.description
            ws.cell(row=cont, column=6).number_format = 'dd/mm/yyyy hh:mm:ss'
            ws.cell(row=cont, column=7).value = order.created
            ws.cell(row=cont, column=7).number_format = 'dd/mm/yyyy hh:mm:ss'
            ws.cell(row=cont, column=8).value = order.get_status_display()
            cont = cont + 1
        nombre_archivo = "ReporteOrdenesServicio.xlsx"
        response = HttpResponse(content_type="application/ms-excel")
        contenido = "attachment; filename={0}".format(nombre_archivo)
        response["Content-Disposition"] = contenido
        wb.save(response)
        return response


class ReporteExcelOrdenesCompraFecha(FormView):
    form_class = FormularioReporteOrdenesFecha
    template_name = "compras/reporte_ordenes.html"

    def form_valid(self, form):
        data = form.cleaned_data
        tipo_busqueda = data['tipo_busqueda']
        wb = Workbook()
        ws = wb.active
        if tipo_busqueda == 'F':
            p_start_date = data['start_date']
            p_fecha_final = data['end_date']
            anio = int(p_start_date[6:])
            month = int(p_start_date[3:5])
            dia = int(p_start_date[0:2])
            start_date = timezone.make_aware(datetime.datetime(anio, month, dia, 23, 59, 59))
            anio = int(p_fecha_final[6:])
            month = int(p_fecha_final[3:5])
            dia = int(p_fecha_final[0:2])
            fecha_final = timezone.make_aware(datetime.datetime(anio, month, dia, 23, 59, 59))
            ws['B2'] = 'REPORTE DE ORDENES DE COMPRA POR FECHA'
            ws.merge_cells('B2:H2')
            ws['B3'] = 'DESDE'
            ws['C3'] = p_start_date
            ws['C3'].number_format = 'dd/mm/yyyy'
            ws['D3'] = 'HASTA'
            ws['E3'] = p_fecha_final
            ws['F3'].number_format = 'dd/mm/yyyy'
            ordenes_compra = PurchaseOrder.objects.filter(date__range=[start_date, fecha_final])
        elif tipo_busqueda == 'M':
            month = data['month'].strip()
            year = data['year'].strip()
            ws['B2'] = 'REPORTE DE ORDENES DE COMPRA POR MES'
            ws.merge_cells('B2:H2')
            ws['B3'] = 'MES'
            ws['C3'] = month
            ws['D3'] = 'AÑO'
            ws['E3'] = year
            ordenes_compra = PurchaseOrder.objects.filter(date__month=month, date__year=year)
        elif tipo_busqueda == 'A':
            year = data['year'].strip()
            ws['B2'] = 'REPORTE DE ORDENES DE COMPRA POR AÑO'
            ws.merge_cells('B2:H2')
            ws['B3'] = 'AÑO'
            ws['C3'] = year
            ordenes_compra = PurchaseOrder.objects.filter(date__year=year)
        ws['B5'] = 'CODIGO'
        ws['C5'] = 'FECHA'
        ws['D5'] = 'PROVEEDOR'
        ws['E5'] = 'IMPORTE'
        ws['F5'] = 'FORMA_PAGO'
        ws['G5'] = 'CREADO'
        ws['H5'] = 'ESTADO'
        ordenes_compra = ordenes_compra.select_related(
            'supplier', 'payment_method', 'quotation__supplier'
        ).prefetch_related('details')
        cont = 6
        for orden_compra in ordenes_compra:
            ws.cell(row=cont, column=2).value = orden_compra.code
            ws.cell(row=cont, column=3).value = orden_compra.date
            ws.cell(row=cont, column=3).number_format = 'dd/mm/yyyy'
            try:
                ws.cell(row=cont, column=4).value = orden_compra.quotation.supplier.business_name
            except ObjectDoesNotExist:
                ws.cell(row=cont, column=4).value = orden_compra.supplier.business_name
            ws.cell(row=cont, column=5).value = orden_compra.total
            ws.cell(row=cont, column=6).value = orden_compra.payment_method.description
            ws.cell(row=cont, column=6).number_format = 'dd/mm/yyyy hh:mm:ss'
            ws.cell(row=cont, column=7).value = orden_compra.created
            ws.cell(row=cont, column=7).number_format = 'dd/mm/yyyy hh:mm:ss'
            ws.cell(row=cont, column=8).value = orden_compra.get_status_display()
            cont = cont + 1
        nombre_archivo = "ReporteOrdenesCompra.xlsx"
        response = HttpResponse(content_type="application/ms-excel")
        contenido = "attachment; filename={0}".format(nombre_archivo)
        response["Content-Disposition"] = contenido
        wb.save(response)
        return response


class TransferenciaCotizacion(TemplateView):
    template_name = 'compras/transferencia_cotizacion.html'

    def get_context_data(self, **kwargs):
        context = super(TransferenciaCotizacion, self).get_context_data(**kwargs)
        context['cotizaciones'] = Quotation.objects.filter(status=Quotation.STATUS.PEND)
        return context


class TransferenciaOrdenCompra(TemplateView):
    template_name = 'compras/transferencia_orden_compra.html'

    def get_context_data(self, **kwargs):
        context = super(TransferenciaOrdenCompra, self).get_context_data(**kwargs)
        context['ordenes'] = PurchaseOrder.objects.filter(
            Q(status=PurchaseOrder.STATUS.PEND) | Q(status=PurchaseOrder.STATUS.ING_PARC))
        return context


class TransferenciaOrdenServicios(TemplateView):
    template_name = 'compras/transferencia_orden_servicios.html'

    def get_context_data(self, **kwargs):
        context = super(TransferenciaOrdenServicios, self).get_context_data(**kwargs)
        context['ordenes'] = ServiceOrder.objects.filter(status=ServiceOrder.STATUS.PEND)
        return context
