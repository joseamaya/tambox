# -*- coding: utf-8 -*-
from django.shortcuts import render, get_object_or_404
from django.views.generic.base import View, TemplateView
from django.views.generic.list import ListView
from django.views.generic.edit import FormView, UpdateView, CreateView
from django.urls import reverse_lazy, reverse
from django.http.response import HttpResponseRedirect
import json
from django.http import HttpResponse
import simplejson
from django.views.generic.detail import DetailView
from administracion.models import Oficina, NivelAprobacion
import locale
from seguridad.permisos import requiere
from django.utils.decorators import method_decorator
from django.db import transaction, IntegrityError
from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Q
from django.contrib import messages
from requerimientos.models import AprobacionRequerimiento, Requerimiento, \
    DetalleRequerimiento
from requerimientos.forms import AprobacionRequerimientoForm, RequerimientoForm, DetalleRequerimientoFormSet
from compras.forms import DetalleCotizacionFormSet
from compras.models import Cotizacion
from productos.models import Producto
from requerimientos.mail import correo_creacion_requerimiento
from openpyxl import Workbook
from requerimientos.reports import ReporteRequerimiento
from datetime import date
from tambox.configuracion import configuracion, oficina_administracion, \
    logistica, presupuesto

locale.setlocale(locale.LC_ALL, "")


from tambox.vistas import SoloAjaxMixin
class Tablero(View):
    def get(self, request, *args, **kwargs):
        lista_notificaciones = []
        context = {'notificaciones': lista_notificaciones}
        return render(request, 'requerimientos/tablero_requerimientos.html', context)


class AprobarRequerimiento(UpdateView):
    model = AprobacionRequerimiento
    template_name = 'requerimientos/aprobar_requerimiento.html'
    form_class = AprobacionRequerimientoForm
    success_url = reverse_lazy('requerimientos:listado_aprobacion_requerimientos')

    @method_decorator(requiere('requerimientos.change_aprobacionrequerimiento'))
    def dispatch(self, *args, **kwargs):
        aprobacion_requerimiento = get_object_or_404(self.model, pk=kwargs['pk'])
        usuario = self.request.user
        if aprobacion_requerimiento.verificar_acceso_aprobacion(usuario):
            return super(AprobarRequerimiento, self).dispatch(*args, **kwargs)
        else:
            return HttpResponseRedirect(reverse('seguridad:permiso_denegado'))

    def get_form_kwargs(self):
        kwargs = super(AprobarRequerimiento, self).get_form_kwargs()
        kwargs['request'] = self.request
        return kwargs

    def form_valid(self, form):
        form.save()
        return HttpResponseRedirect(self.get_success_url())

    def form_invalid(self, form):
        return self.render_to_response(self.get_context_data(form=form))


class CrearDetalleRequerimiento(SoloAjaxMixin, FormView):
    def get(self, request, *args, **kwargs):
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            lista_detalles = []
            det = {}
            det['code'] = ''
            det['product'] = ''
            det['unidad'] = ''
            det['quantity'] = '0'
            det['use'] = ''
            lista_detalles.append(det)
            formset = DetalleRequerimientoFormSet(initial=lista_detalles)
            lista_json = []
            for form in formset:
                detalle_json = {}
                detalle_json['code'] = str(form['code'])
                detalle_json['product'] = str(form['product'])
                detalle_json['unidad'] = str(form['unidad'])
                detalle_json['quantity'] = str(form['quantity'])
                detalle_json['use'] = str(form['use'])
                lista_json.append(detalle_json)
            data = json.dumps(lista_json)
            return HttpResponse(data, 'application/json')


class CrearRequerimiento(CreateView):
    template_name = 'requerimientos/requerimiento.html'
    form_class = RequerimientoForm
    model = Requerimiento
    context_object_name = 'requirement'

    def get_form_kwargs(self):
        kwargs = super(CrearRequerimiento, self).get_form_kwargs()
        kwargs['request'] = self.request
        return kwargs

    def get_initial(self):
        initial = super(CrearRequerimiento, self).get_initial()
        initial['year'] = date.today().year
        initial['date'] = date.today().strftime('%d/%m/%Y')
        initial['month'] = date.today().month
        return initial

    def get(self, request, *args, **kwargs):
        self.object = None
        oficinas = Oficina.objects.all()
        if not oficinas:
            return HttpResponseRedirect(reverse('administracion:crear_oficina'))
        try:
            worker = self.request.user.worker
        except ObjectDoesNotExist:
            return HttpResponseRedirect(reverse('administracion:crear_trabajador'))
        if worker.signature == '':
            return HttpResponseRedirect(reverse('administracion:modificar_trabajador', args=[worker.pk]))
        puesto = worker.puesto
        if puesto is None:
            return HttpResponseRedirect(reverse('administracion:crear_puesto'))
        puesto_jefe = puesto.puesto_superior
        if puesto_jefe is None:
            return HttpResponseRedirect(reverse('administracion:crear_puesto'))
        niveles_aprobacion = NivelAprobacion.objects.all()
        if not niveles_aprobacion:
            return HttpResponseRedirect(reverse('administracion:crear_nivel_aprobacion'))
        if configuracion() is not None:
            form_class = self.get_form_class()
            form = self.get_form(form_class)
            detalle_requerimiento_formset = DetalleRequerimientoFormSet()
            return self.render_to_response(self.get_context_data(form=form,
                                                                 detalle_requerimiento_formset=detalle_requerimiento_formset))
        else:
            return HttpResponseRedirect(reverse('contabilidad:configuracion'))

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
                    code = detalle_requerimiento_form.cleaned_data.get('code')
                    quantity = detalle_requerimiento_form.cleaned_data.get('quantity')
                    use = detalle_requerimiento_form.cleaned_data.get('use')
                    if code and quantity:
                        product = Producto.objects.get(code=code)
                        detalles.append(DetalleRequerimiento(requirement=self.object,
                                                             line_number=cont,
                                                             product=product,
                                                             quantity=quantity,
                                                             use=use))
                        cont = cont + 1
                DetalleRequerimiento.objects.bulk_create(detalles)
                puesto_jefe = self.object.requester.puesto.puesto_superior  # Puesto.objects.get(office=self.object.office, is_leadership=True, is_active=True)
                jefe = puesto_jefe.worker
                destinatario = jefe.user.email
                if jefe.pk != self.object.requester.pk:
                    correo_creacion_requerimiento(destinatario, self.object)
                return HttpResponseRedirect(reverse('requerimientos:requirement_detail', args=[self.object.code]))
        except IntegrityError:
            messages.error(self.request, 'Error guardando el requerimiento.')

    def form_invalid(self, form, detalle_requerimiento_formset):
        return self.render_to_response(self.get_context_data(form=form,
                                                             detalle_requerimiento_formset=detalle_requerimiento_formset))


class DetalleOperacionRequerimiento(DetailView):
    model = Requerimiento
    context_object_name = 'requirement'
    slug_field = 'code'
    slug_url_kwarg = 'code'
    template_name = 'requerimientos/detalle_requerimiento.html'

    @method_decorator(
        requiere('requerimientos.ver_detalle_requerimiento'))
    def dispatch(self, *args, **kwargs):
        requirement = self.get_object()
        if requirement.verificar_acceso(self.request.user, oficina_administracion(), logistica(), presupuesto()):
            return super(DetalleOperacionRequerimiento, self).dispatch(*args, **kwargs)
        else:
            return HttpResponseRedirect(
                reverse('requerimientos:requirement_detail', args=[requirement.siguiente()]))


class EliminarRequerimiento(TemplateView):
    http_method_names = ['post']

    @method_decorator(requiere('requerimientos.delete_requerimiento'))
    def dispatch(self, *args, **kwargs):
        return super(EliminarRequerimiento, self).dispatch(*args, **kwargs)

    def post(self, request, *args, **kwargs):
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            code = request.POST['code']
            requirement = Requerimiento.objects.get(code=code)
            requerimiento_json = {}
            requerimiento_json['code'] = code
            cotizaciones = requirement.quotations.all()
            if len(cotizaciones) > 0:
                requerimiento_json['cotizaciones'] = 'SI'
            else:
                requerimiento_json['cotizaciones'] = 'NO'
                with transaction.atomic():
                    requirement.eliminar_requerimiento()
                    DetalleRequerimiento.objects.filter(requirement=requirement).delete()
            data = simplejson.dumps(requerimiento_json)
            return HttpResponse(data, 'application/json')


class ListadoAprobacionRequerimientos(ListView):
    model = AprobacionRequerimiento
    template_name = 'requerimientos/listado_aprobacion_requerimientos.html'
    context_object_name = 'aprobacion_requerimientos'

    @method_decorator(
        requiere('requerimientos.ver_tabla_requerimientos'))
    def dispatch(self, *args, **kwargs):
        return super(ListadoAprobacionRequerimientos, self).dispatch(*args, **kwargs)

    def get(self, request, *args, **kwargs):
        try:
            worker = self.request.user.worker
        except ObjectDoesNotExist:
            return HttpResponseRedirect(reverse('administracion:crear_trabajador'))
        if worker.signature == '':
            return HttpResponseRedirect(reverse('administracion:modificar_trabajador', args=[worker.pk]))
        puesto = worker.puesto
        if puesto is None:
            return HttpResponseRedirect(reverse('administracion:crear_puesto'))
        if not puesto.is_leadership:
            return HttpResponseRedirect(reverse('seguridad:permiso_denegado'))
        return super(ListadoAprobacionRequerimientos, self).get(request, *args, **kwargs)

    def get_queryset(self):
        return AprobacionRequerimiento.obtener_aprobaciones_pendientes(self.request.user)


class ListadoCotizacionesPorRequerimiento(ListView):
    model = Cotizacion
    template_name = 'compras/cotizaciones.html'
    context_object_name = 'cotizaciones'

    @method_decorator(requiere('compras.ver_tabla_cotizaciones'))
    def dispatch(self, *args, **kwargs):
        return super(ListadoCotizacionesPorRequerimiento, self).dispatch(*args, **kwargs)

    def get_queryset(self):
        requirement = Requerimiento.objects.get(pk=self.kwargs['requirement'])
        queryset = requirement.quotations.all()
        return queryset


class ListadoRequerimientos(ListView):
    model = Requerimiento
    template_name = 'requerimientos/listado_requerimientos.html'
    context_object_name = 'requerimientos'

    def get_queryset(self):
        usuario = self.request.user
        requerimientos_visibles = Requerimiento.obtener_requerimientos_visibles(usuario)
        return requerimientos_visibles

    @method_decorator(
        requiere('requerimientos.ver_tabla_requerimientos'))
    def dispatch(self, *args, **kwargs):
        return super(ListadoRequerimientos, self).dispatch(*args, **kwargs)


class ModificarRequerimiento(UpdateView):
    template_name = 'requerimientos/requerimiento.html'
    model = Requerimiento
    context_object_name = 'requirement'
    form_class = RequerimientoForm

    @method_decorator(
        requiere('requerimientos.change_requerimiento'))
    def dispatch(self, *args, **kwargs):
        requirement = self.get_object()
        if (requirement.approval.is_active == AprobacionRequerimiento.NIVEL.USU or
                requirement.approval.is_active == AprobacionRequerimiento.NIVEL.JEF or
                self.request.user.is_superuser):
            return super(ModificarRequerimiento, self).dispatch(*args, **kwargs)
        else:
            return HttpResponseRedirect(reverse('seguridad:permiso_denegado'))

    def get_form_kwargs(self):
        kwargs = super(ModificarRequerimiento, self).get_form_kwargs()
        kwargs['request'] = self.request
        return kwargs

    def get_initial(self):
        initial = super(ModificarRequerimiento, self).get_initial()
        initial['date'] = self.object.date.strftime('%d/%m/%Y')
        return initial

    def get_context_data(self, **kwargs):
        context = super(ModificarRequerimiento, self).get_context_data(**kwargs)
        return context

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        form_class = self.get_form_class()
        form = self.get_form(form_class)
        detalles = DetalleRequerimiento.objects.filter(requirement=self.object).order_by('line_number')
        detalles_data = []
        for detalle in detalles:
            try:
                d = {'code': detalle.product.code,
                     'product': detalle.product.description,
                     'quantity': detalle.quantity,
                     'unidad': detalle.product.unit_of_measure.code,
                     'use': detalle.use}
            except AttributeError:
                d = {'code': '',
                     'product': detalle.otro,
                     'quantity': detalle.quantity,
                     'unidad': '',
                     'use': detalle.use}
            detalles_data.append(d)
        detalle_requerimiento_formset = DetalleRequerimientoFormSet(initial=detalles_data)
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
                DetalleRequerimiento.objects.filter(requirement=self.object).delete()
                form.save()
                detalles = []
                cont = 1
                for detalle_requerimiento_form in detalle_requerimiento_formset:
                    code = detalle_requerimiento_form.cleaned_data.get('code')
                    quantity = detalle_requerimiento_form.cleaned_data.get('quantity')
                    use = detalle_requerimiento_form.cleaned_data.get('use')
                    if code and quantity:
                        product = Producto.objects.get(code=code)
                        detalles.append(
                            DetalleRequerimiento(requirement=self.object, line_number=cont, product=product,
                                                 quantity=quantity, use=use))
                        cont = cont + 1
                    elif quantity:
                        product = detalle_requerimiento_form.cleaned_data.get('product')
                        detalles.append(DetalleRequerimiento(requirement=self.object, line_number=cont, otro=product,
                                                             quantity=quantity, use=use))
                        cont = cont + 1
                DetalleRequerimiento.objects.bulk_create(detalles)
                return HttpResponseRedirect(reverse('requerimientos:requirement_detail', args=[self.object.code]))
        except IntegrityError:
            messages.error(self.request, 'Error guardando el requerimiento.')

    def form_invalid(self, form, detalle_requerimiento_formset):
        return self.render_to_response(self.get_context_data(form=form,
                                                             detalle_requerimiento_formset=detalle_requerimiento_formset))


class ObtenerDetalleRequerimiento(SoloAjaxMixin, TemplateView):

    parametros_requeridos = ('requirement', 'tipo_busqueda')
    def get(self, request, *args, **kwargs):
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            requirement = request.GET['requirement']
            tipo_busqueda = request.GET['tipo_busqueda']
            if tipo_busqueda == 'TODOS':
                detalles = DetalleRequerimiento.objects.filter(
                    Q(status=DetalleRequerimiento.STATUS.PEND) | Q(status=DetalleRequerimiento.STATUS.COTIZ),
                    requirement__code=requirement).order_by('line_number')
            elif tipo_busqueda == 'PRODUCTOS':
                detalles = DetalleRequerimiento.objects.filter(Q(status=DetalleRequerimiento.STATUS.PEND) |
                                                               Q(status=DetalleRequerimiento.STATUS.COTIZ),
                                                               requirement__code=requirement,
                                                               product__isnull=False).order_by('line_number')
            lista_detalles = []
            for detalle in detalles:
                det = {}
                det['requirement'] = detalle.id
                try:
                    det['code'] = detalle.product.code
                    det['name'] = detalle.product.description
                    det['unidad'] = detalle.product.unit_of_measure.code
                    # det['use'] = detalle.use
                    det['quantity'] = str(detalle.quantity - detalle.served_quantity)
                    # det['price'] = str(detalle.product.price)
                    # det['amount'] = str(detalle.product.price*(detalle.quantity-detalle.served_quantity))
                    lista_detalles.append(det)
                except AttributeError:
                    pass
            formset = DetalleCotizacionFormSet(initial=lista_detalles)
            lista_json = []
            for form in formset:
                detalle_json = {}
                detalle_json['requirement'] = str(form['requirement'])
                detalle_json['code'] = str(form['code'])
                detalle_json['name'] = str(form['name'])
                detalle_json['unidad'] = str(form['unidad'])
                detalle_json['quantity'] = str(form['quantity'])
                lista_json.append(detalle_json)
            data = json.dumps(lista_json)
            return HttpResponse(data, 'application/json')


class TransferenciaRequerimiento(TemplateView):
    template_name = 'requerimientos/transferencia_requerimiento.html'

    def get_context_data(self, **kwargs):
        context = super(TransferenciaRequerimiento, self).get_context_data(**kwargs)
        # requerimientos = Requerimiento.objects.all()
        requerimientos = Requerimiento.obtener_requerimientos_listos_transferencia()
        context['requerimientos'] = requerimientos
        return context


class ReporteExcelRequerimientos(TemplateView):
    def get(self, request, *args, **kwargs):
        requerimientos = Requerimiento.objects.requerimientos_activos_por_usuario(request.user,
                                                                                  Requerimiento.STATUS.CANC)
        wb = Workbook()
        ws = wb.active
        ws['B1'] = 'REPORTE DE REQUERIMIENTOS'
        ws.merge_cells('B1:J1')
        ws['B3'] = 'CODIGO'
        ws['C3'] = 'OFICINA'
        ws['D3'] = 'ESTADO APROBACION'
        ws['E3'] = 'ESTADO'
        ws['F3'] = 'FECHA'
        cont = 4
        for requirement in requerimientos:
            ws.cell(row=cont, column=2).value = requirement.code
            ws.cell(row=cont, column=3).value = requirement.office.name
            ws.cell(row=cont, column=4).value = requirement.get_status_display()
            ws.cell(row=cont, column=5).value = requirement.approval.get_status_display()
            ws.cell(row=cont, column=6).value = requirement.created
            ws.cell(row=cont, column=6).number_format = 'dd/mm/yyyy hh:mm:ss'
            cont = cont + 1
        nombre_archivo = "ListadoRequerimientos.xlsx"
        response = HttpResponse(content_type="application/ms-excel")
        contenido = "attachment; filename={0}".format(nombre_archivo)
        response["Content-Disposition"] = contenido
        wb.save(response)
        return response


class ReportePDFRequerimiento(View):
    def get(self, request, *args, **kwargs):
        code = kwargs['code']
        requirement = Requerimiento.objects.get(code=code)
        response = HttpResponse(content_type='application/pdf')
        reporte = ReporteRequerimiento('A4', requirement)
        pdf = reporte.imprimir()
        response.write(pdf)
        return response
