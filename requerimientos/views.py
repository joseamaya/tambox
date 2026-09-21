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
            det['producto'] = ''
            det['unidad'] = ''
            det['quantity'] = '0'
            det['uso'] = ''
            lista_detalles.append(det)
            formset = DetalleRequerimientoFormSet(initial=lista_detalles)
            lista_json = []
            for form in formset:
                detalle_json = {}
                detalle_json['code'] = str(form['code'])
                detalle_json['producto'] = str(form['producto'])
                detalle_json['unidad'] = str(form['unidad'])
                detalle_json['quantity'] = str(form['quantity'])
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

    def get_initial(self):
        initial = super(CrearRequerimiento, self).get_initial()
        initial['annio'] = date.today().year
        initial['date'] = date.today().strftime('%d/%m/%Y')
        initial['mes'] = date.today().month
        return initial

    def get(self, request, *args, **kwargs):
        self.object = None
        oficinas = Oficina.objects.all()
        if not oficinas:
            return HttpResponseRedirect(reverse('administracion:crear_oficina'))
        try:
            trabajador = self.request.user.trabajador
        except ObjectDoesNotExist:
            return HttpResponseRedirect(reverse('administracion:crear_trabajador'))
        if trabajador.firma == '':
            return HttpResponseRedirect(reverse('administracion:modificar_trabajador', args=[trabajador.pk]))
        puesto = trabajador.puesto
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
                    uso = detalle_requerimiento_form.cleaned_data.get('uso')
                    if code and quantity:
                        producto = Producto.objects.get(code=code)
                        detalles.append(DetalleRequerimiento(requerimiento=self.object,
                                                             nro_detalle=cont,
                                                             producto=producto,
                                                             quantity=quantity,
                                                             uso=uso))
                        cont = cont + 1
                DetalleRequerimiento.objects.bulk_create(detalles)
                puesto_jefe = self.object.solicitante.puesto.puesto_superior  # Puesto.objects.get(oficina=self.object.oficina, es_jefatura=True, estado=True)
                jefe = puesto_jefe.trabajador
                destinatario = jefe.usuario.email
                if jefe.pk != self.object.solicitante.pk:
                    correo_creacion_requerimiento(destinatario, self.object)
                return HttpResponseRedirect(reverse('requerimientos:detalle_requerimiento', args=[self.object.code]))
        except IntegrityError:
            messages.error(self.request, 'Error guardando el requerimiento.')

    def form_invalid(self, form, detalle_requerimiento_formset):
        return self.render_to_response(self.get_context_data(form=form,
                                                             detalle_requerimiento_formset=detalle_requerimiento_formset))


class DetalleOperacionRequerimiento(DetailView):
    model = Requerimiento
    slug_field = 'code'
    slug_url_kwarg = 'code'
    template_name = 'requerimientos/detalle_requerimiento.html'

    @method_decorator(
        requiere('requerimientos.ver_detalle_requerimiento'))
    def dispatch(self, *args, **kwargs):
        requerimiento = self.get_object()
        if requerimiento.verificar_acceso(self.request.user, oficina_administracion(), logistica(), presupuesto()):
            return super(DetalleOperacionRequerimiento, self).dispatch(*args, **kwargs)
        else:
            return HttpResponseRedirect(
                reverse('requerimientos:detalle_requerimiento', args=[requerimiento.siguiente()]))


class EliminarRequerimiento(TemplateView):
    http_method_names = ['post']

    @method_decorator(requiere('requerimientos.delete_requerimiento'))
    def dispatch(self, *args, **kwargs):
        return super(EliminarRequerimiento, self).dispatch(*args, **kwargs)

    def post(self, request, *args, **kwargs):
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            code = request.POST['code']
            requerimiento = Requerimiento.objects.get(code=code)
            requerimiento_json = {}
            requerimiento_json['code'] = code
            cotizaciones = requerimiento.cotizacion_set.all()
            if len(cotizaciones) > 0:
                requerimiento_json['cotizaciones'] = 'SI'
            else:
                requerimiento_json['cotizaciones'] = 'NO'
                with transaction.atomic():
                    requerimiento.eliminar_requerimiento()
                    DetalleRequerimiento.objects.filter(requerimiento=requerimiento).delete()
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
            trabajador = self.request.user.trabajador
        except ObjectDoesNotExist:
            return HttpResponseRedirect(reverse('administracion:crear_trabajador'))
        if trabajador.firma == '':
            return HttpResponseRedirect(reverse('administracion:modificar_trabajador', args=[trabajador.pk]))
        puesto = trabajador.puesto
        if puesto is None:
            return HttpResponseRedirect(reverse('administracion:crear_puesto'))
        if not puesto.es_jefatura:
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
        requerimiento = Requerimiento.objects.get(pk=self.kwargs['requerimiento'])
        queryset = requerimiento.cotizacion_set.all()
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
    form_class = RequerimientoForm

    @method_decorator(
        requiere('requerimientos.change_requerimiento'))
    def dispatch(self, *args, **kwargs):
        requerimiento = self.get_object()
        if (requerimiento.aprobacionrequerimiento.estado == AprobacionRequerimiento.NIVEL.USU or
                requerimiento.aprobacionrequerimiento.estado == AprobacionRequerimiento.NIVEL.JEF or
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
        detalles = DetalleRequerimiento.objects.filter(requerimiento=self.object).order_by('nro_detalle')
        detalles_data = []
        for detalle in detalles:
            try:
                d = {'code': detalle.producto.code,
                     'producto': detalle.producto.description,
                     'quantity': detalle.quantity,
                     'unidad': detalle.producto.unidad_medida.code,
                     'uso': detalle.uso}
            except AttributeError:
                d = {'code': '',
                     'producto': detalle.otro,
                     'quantity': detalle.quantity,
                     'unidad': '',
                     'uso': detalle.uso}
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
                DetalleRequerimiento.objects.filter(requerimiento=self.object).delete()
                form.save()
                detalles = []
                cont = 1
                for detalle_requerimiento_form in detalle_requerimiento_formset:
                    code = detalle_requerimiento_form.cleaned_data.get('code')
                    quantity = detalle_requerimiento_form.cleaned_data.get('quantity')
                    uso = detalle_requerimiento_form.cleaned_data.get('uso')
                    if code and quantity:
                        producto = Producto.objects.get(code=code)
                        detalles.append(
                            DetalleRequerimiento(requerimiento=self.object, nro_detalle=cont, producto=producto,
                                                 quantity=quantity, uso=uso))
                        cont = cont + 1
                    elif quantity:
                        producto = detalle_requerimiento_form.cleaned_data.get('producto')
                        detalles.append(DetalleRequerimiento(requerimiento=self.object, nro_detalle=cont, otro=producto,
                                                             quantity=quantity, uso=uso))
                        cont = cont + 1
                DetalleRequerimiento.objects.bulk_create(detalles)
                return HttpResponseRedirect(reverse('requerimientos:detalle_requerimiento', args=[self.object.code]))
        except IntegrityError:
            messages.error(self.request, 'Error guardando el requerimiento.')

    def form_invalid(self, form, detalle_requerimiento_formset):
        return self.render_to_response(self.get_context_data(form=form,
                                                             detalle_requerimiento_formset=detalle_requerimiento_formset))


class ObtenerDetalleRequerimiento(SoloAjaxMixin, TemplateView):

    parametros_requeridos = ('requerimiento', 'tipo_busqueda')
    def get(self, request, *args, **kwargs):
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            requerimiento = request.GET['requerimiento']
            tipo_busqueda = request.GET['tipo_busqueda']
            if tipo_busqueda == 'TODOS':
                detalles = DetalleRequerimiento.objects.filter(
                    Q(estado=DetalleRequerimiento.STATUS.PEND) | Q(estado=DetalleRequerimiento.STATUS.COTIZ),
                    requerimiento__code=requerimiento).order_by('nro_detalle')
            elif tipo_busqueda == 'PRODUCTOS':
                detalles = DetalleRequerimiento.objects.filter(Q(estado=DetalleRequerimiento.STATUS.PEND) |
                                                               Q(estado=DetalleRequerimiento.STATUS.COTIZ),
                                                               requerimiento__code=requerimiento,
                                                               producto__isnull=False).order_by('nro_detalle')
            lista_detalles = []
            for detalle in detalles:
                det = {}
                det['requerimiento'] = detalle.id
                try:
                    det['code'] = detalle.producto.code
                    det['name'] = detalle.producto.description
                    det['unidad'] = detalle.producto.unidad_medida.code
                    # det['uso'] = detalle.uso
                    det['quantity'] = str(detalle.quantity - detalle.served_quantity)
                    # det['price'] = str(detalle.producto.price)
                    # det['amount'] = str(detalle.producto.price*(detalle.quantity-detalle.served_quantity))
                    lista_detalles.append(det)
                except AttributeError:
                    pass
            formset = DetalleCotizacionFormSet(initial=lista_detalles)
            lista_json = []
            for form in formset:
                detalle_json = {}
                detalle_json['requerimiento'] = str(form['requerimiento'])
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
        for requerimiento in requerimientos:
            ws.cell(row=cont, column=2).value = requerimiento.code
            ws.cell(row=cont, column=3).value = requerimiento.oficina.name
            ws.cell(row=cont, column=4).value = requerimiento.get_estado_display()
            ws.cell(row=cont, column=5).value = requerimiento.aprobacionrequerimiento.get_estado_display()
            ws.cell(row=cont, column=6).value = requerimiento.created
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
        requerimiento = Requerimiento.objects.get(code=code)
        response = HttpResponse(content_type='application/pdf')
        reporte = ReporteRequerimiento('A4', requerimiento)
        pdf = reporte.imprimir()
        response.write(pdf)
        return response
