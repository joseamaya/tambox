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
from administracion.models import Office, ApprovalLevel
import locale
from seguridad.permisos import requires
from django.utils.decorators import method_decorator
from django.db import transaction, IntegrityError
from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Q
from django.contrib import messages
from requerimientos.models import RequirementApproval, Requirement, \
    RequirementDetail
from requerimientos.forms import RequirementApprovalForm, RequirementForm, RequirementDetailFormSet
from compras.forms import QuotationDetailFormSet
from compras.models import Quotation
from productos.models import Product
from requerimientos.mail import requirement_creation_mail
from openpyxl import Workbook
from requerimientos.reports import RequirementReport
from datetime import date
from tambox.config import configuration, administration_office, \
    logistics, budget

locale.setlocale(locale.LC_ALL, "")


from tambox.views import AjaxOnlyMixin
class Dashboard(View):
    def get(self, request, *args, **kwargs):
        lista_notificaciones = []
        context = {'notificaciones': lista_notificaciones}
        return render(request, 'requerimientos/tablero_requerimientos.html', context)


class RequirementApprove(UpdateView):
    model = RequirementApproval
    template_name = 'requerimientos/aprobar_requerimiento.html'
    form_class = RequirementApprovalForm
    success_url = reverse_lazy('requerimientos:requirement_approval_list')

    @method_decorator(requires('requerimientos.change_requirementapproval'))
    def dispatch(self, *args, **kwargs):
        aprobacion_requerimiento = get_object_or_404(self.model, pk=kwargs['pk'])
        usuario = self.request.user
        if aprobacion_requerimiento.check_approval_access(usuario):
            return super(RequirementApprove, self).dispatch(*args, **kwargs)
        else:
            return HttpResponseRedirect(reverse('seguridad:permission_denied'))

    def get_form_kwargs(self):
        kwargs = super(RequirementApprove, self).get_form_kwargs()
        kwargs['request'] = self.request
        return kwargs

    def form_valid(self, form):
        form.save()
        return HttpResponseRedirect(self.get_success_url())

    def form_invalid(self, form):
        return self.render_to_response(self.get_context_data(form=form))


class RequirementDetailCreate(AjaxOnlyMixin, FormView):
    def get(self, request, *args, **kwargs):
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            lista_detalles = []
            det = {}
            det['code'] = ''
            det['product'] = ''
            det['unit'] = ''
            det['quantity'] = '0'
            det['use'] = ''
            lista_detalles.append(det)
            formset = RequirementDetailFormSet(initial=lista_detalles)
            lista_json = []
            for form in formset:
                detalle_json = {}
                detalle_json['code'] = str(form['code'])
                detalle_json['product'] = str(form['product'])
                detalle_json['unit'] = str(form['unit'])
                detalle_json['quantity'] = str(form['quantity'])
                detalle_json['use'] = str(form['use'])
                lista_json.append(detalle_json)
            data = json.dumps(lista_json)
            return HttpResponse(data, 'application/json')


class RequirementCreate(CreateView):
    template_name = 'requerimientos/requerimiento.html'
    form_class = RequirementForm
    model = Requirement
    context_object_name = 'requirement'

    def get_form_kwargs(self):
        kwargs = super(RequirementCreate, self).get_form_kwargs()
        kwargs['request'] = self.request
        return kwargs

    def get_initial(self):
        initial = super(RequirementCreate, self).get_initial()
        initial['year'] = date.today().year
        initial['date'] = date.today().strftime('%d/%m/%Y')
        initial['month'] = date.today().month
        return initial

    def get(self, request, *args, **kwargs):
        self.object = None
        oficinas = Office.objects.all()
        if not oficinas:
            return HttpResponseRedirect(reverse('administracion:office_create'))
        try:
            worker = self.request.user.worker
        except ObjectDoesNotExist:
            return HttpResponseRedirect(reverse('administracion:worker_create'))
        if worker.signature == '':
            return HttpResponseRedirect(reverse('administracion:worker_update', args=[worker.pk]))
        position = worker.position
        if position is None:
            return HttpResponseRedirect(reverse('administracion:position_create'))
        puesto_jefe = position.superior_position
        if puesto_jefe is None:
            return HttpResponseRedirect(reverse('administracion:position_create'))
        niveles_aprobacion = ApprovalLevel.objects.all()
        if not niveles_aprobacion:
            return HttpResponseRedirect(reverse('administracion:approval_level_create'))
        if configuration() is not None:
            form_class = self.get_form_class()
            form = self.get_form(form_class)
            detalle_requerimiento_formset = RequirementDetailFormSet()
            return self.render_to_response(self.get_context_data(form=form,
                                                                 detalle_requerimiento_formset=detalle_requerimiento_formset))
        else:
            return HttpResponseRedirect(reverse('contabilidad:configuration'))

    def post(self, request, *args, **kwargs):
        self.object = None
        form_class = self.get_form_class()
        form = self.get_form(form_class)
        detalle_requerimiento_formset = RequirementDetailFormSet(request.POST)
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
                        product = Product.objects.get(code=code)
                        detalles.append(RequirementDetail(requirement=self.object,
                                                             line_number=cont,
                                                             product=product,
                                                             quantity=quantity,
                                                             use=use))
                        cont = cont + 1
                RequirementDetail.objects.bulk_create(detalles)
                puesto_jefe = self.object.requester.position.superior_position  # Position.objects.get(office=self.object.office, is_leadership=True, is_active=True)
                jefe = puesto_jefe.worker
                destinatario = jefe.user.email
                if jefe.pk != self.object.requester.pk:
                    requirement_creation_mail(destinatario, self.object)
                return HttpResponseRedirect(reverse('requerimientos:requirement_detail', args=[self.object.code]))
        except IntegrityError:
            messages.error(self.request, 'Error guardando el requerimiento.')

    def form_invalid(self, form, detalle_requerimiento_formset):
        return self.render_to_response(self.get_context_data(form=form,
                                                             detalle_requerimiento_formset=detalle_requerimiento_formset))


class RequirementDetailView(DetailView):
    model = Requirement
    context_object_name = 'requirement'
    slug_field = 'code'
    slug_url_kwarg = 'code'
    template_name = 'requerimientos/detalle_requerimiento.html'

    @method_decorator(
        requires('requerimientos.ver_detalle_requerimiento'))
    def dispatch(self, *args, **kwargs):
        requirement = self.get_object()
        if requirement.check_access(self.request.user, administration_office(), logistics(), budget()):
            return super(RequirementDetailView, self).dispatch(*args, **kwargs)
        else:
            return HttpResponseRedirect(
                reverse('requerimientos:requirement_detail', args=[requirement.next()]))


class RequirementDelete(TemplateView):
    http_method_names = ['post']

    @method_decorator(requires('requerimientos.delete_requirement'))
    def dispatch(self, *args, **kwargs):
        return super(RequirementDelete, self).dispatch(*args, **kwargs)

    def post(self, request, *args, **kwargs):
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            code = request.POST['code']
            requirement = Requirement.objects.get(code=code)
            requerimiento_json = {}
            requerimiento_json['code'] = code
            cotizaciones = requirement.quotations.all()
            if len(cotizaciones) > 0:
                requerimiento_json['cotizaciones'] = 'SI'
            else:
                requerimiento_json['cotizaciones'] = 'NO'
                with transaction.atomic():
                    requirement.delete_requirement()
                    RequirementDetail.objects.filter(requirement=requirement).delete()
            data = simplejson.dumps(requerimiento_json)
            return HttpResponse(data, 'application/json')


class RequirementApprovalList(ListView):
    model = RequirementApproval
    template_name = 'requerimientos/listado_aprobacion_requerimientos.html'
    context_object_name = 'aprobacion_requerimientos'

    @method_decorator(
        requires('requerimientos.ver_tabla_requerimientos'))
    def dispatch(self, *args, **kwargs):
        return super(RequirementApprovalList, self).dispatch(*args, **kwargs)

    def get(self, request, *args, **kwargs):
        try:
            worker = self.request.user.worker
        except ObjectDoesNotExist:
            return HttpResponseRedirect(reverse('administracion:worker_create'))
        if worker.signature == '':
            return HttpResponseRedirect(reverse('administracion:worker_update', args=[worker.pk]))
        position = worker.position
        if position is None:
            return HttpResponseRedirect(reverse('administracion:position_create'))
        if not position.is_leadership:
            return HttpResponseRedirect(reverse('seguridad:permission_denied'))
        return super(RequirementApprovalList, self).get(request, *args, **kwargs)

    def get_queryset(self):
        return RequirementApproval.get_pending_approvals(self.request.user)


class QuotationListByRequirement(ListView):
    model = Quotation
    template_name = 'compras/cotizaciones.html'
    context_object_name = 'cotizaciones'

    @method_decorator(requires('compras.ver_tabla_cotizaciones'))
    def dispatch(self, *args, **kwargs):
        return super(QuotationListByRequirement, self).dispatch(*args, **kwargs)

    def get_queryset(self):
        requirement = Requirement.objects.get(pk=self.kwargs['requirement'])
        queryset = requirement.quotations.all()
        return queryset


class RequirementList(ListView):
    model = Requirement
    template_name = 'requerimientos/listado_requerimientos.html'
    context_object_name = 'requerimientos'

    def get_queryset(self):
        usuario = self.request.user
        requerimientos_visibles = Requirement.get_visible_requirements(usuario)
        return requerimientos_visibles

    @method_decorator(
        requires('requerimientos.ver_tabla_requerimientos'))
    def dispatch(self, *args, **kwargs):
        return super(RequirementList, self).dispatch(*args, **kwargs)


class RequirementUpdate(UpdateView):
    template_name = 'requerimientos/requerimiento.html'
    model = Requirement
    context_object_name = 'requirement'
    form_class = RequirementForm

    @method_decorator(
        requires('requerimientos.change_requirement'))
    def dispatch(self, *args, **kwargs):
        requirement = self.get_object()
        if (requirement.approval.is_active == RequirementApproval.NIVEL.USU or
                requirement.approval.is_active == RequirementApproval.NIVEL.JEF or
                self.request.user.is_superuser):
            return super(RequirementUpdate, self).dispatch(*args, **kwargs)
        else:
            return HttpResponseRedirect(reverse('seguridad:permission_denied'))

    def get_form_kwargs(self):
        kwargs = super(RequirementUpdate, self).get_form_kwargs()
        kwargs['request'] = self.request
        return kwargs

    def get_initial(self):
        initial = super(RequirementUpdate, self).get_initial()
        initial['date'] = self.object.date.strftime('%d/%m/%Y')
        return initial

    def get_context_data(self, **kwargs):
        context = super(RequirementUpdate, self).get_context_data(**kwargs)
        return context

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        form_class = self.get_form_class()
        form = self.get_form(form_class)
        detalles = RequirementDetail.objects.filter(requirement=self.object).order_by('line_number')
        detalles_data = []
        for detail in detalles:
            try:
                d = {'code': detail.product.code,
                     'product': detail.product.description,
                     'quantity': detail.quantity,
                     'unit': detail.product.unit_of_measure.code,
                     'use': detail.use}
            except AttributeError:
                d = {'code': '',
                     'product': detail.otro,
                     'quantity': detail.quantity,
                     'unit': '',
                     'use': detail.use}
            detalles_data.append(d)
        detalle_requerimiento_formset = RequirementDetailFormSet(initial=detalles_data)
        return self.render_to_response(self.get_context_data(form=form,
                                                             detalle_requerimiento_formset=detalle_requerimiento_formset))

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        form_class = self.get_form_class()
        form = self.get_form(form_class)
        detalle_requerimiento_formset = RequirementDetailFormSet(request.POST)
        if form.is_valid() and detalle_requerimiento_formset.is_valid():
            return self.form_valid(form, detalle_requerimiento_formset)
        else:
            return self.form_invalid(form, detalle_requerimiento_formset)

    def form_valid(self, form, detalle_requerimiento_formset):
        try:
            with transaction.atomic():
                RequirementDetail.objects.filter(requirement=self.object).delete()
                form.save()
                detalles = []
                cont = 1
                for detalle_requerimiento_form in detalle_requerimiento_formset:
                    code = detalle_requerimiento_form.cleaned_data.get('code')
                    quantity = detalle_requerimiento_form.cleaned_data.get('quantity')
                    use = detalle_requerimiento_form.cleaned_data.get('use')
                    if code and quantity:
                        product = Product.objects.get(code=code)
                        detalles.append(
                            RequirementDetail(requirement=self.object, line_number=cont, product=product,
                                                 quantity=quantity, use=use))
                        cont = cont + 1
                    elif quantity:
                        product = detalle_requerimiento_form.cleaned_data.get('product')
                        detalles.append(RequirementDetail(requirement=self.object, line_number=cont, otro=product,
                                                             quantity=quantity, use=use))
                        cont = cont + 1
                RequirementDetail.objects.bulk_create(detalles)
                return HttpResponseRedirect(reverse('requerimientos:requirement_detail', args=[self.object.code]))
        except IntegrityError:
            messages.error(self.request, 'Error guardando el requerimiento.')

    def form_invalid(self, form, detalle_requerimiento_formset):
        return self.render_to_response(self.get_context_data(form=form,
                                                             detalle_requerimiento_formset=detalle_requerimiento_formset))


class RequirementDetailFetch(AjaxOnlyMixin, TemplateView):

    required_params = ('requirement', 'search_type')
    def get(self, request, *args, **kwargs):
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            requirement = request.GET['requirement']
            search_type = request.GET['search_type']
            if search_type == 'TODOS':
                detalles = RequirementDetail.objects.filter(
                    Q(status=RequirementDetail.STATUS.PEND) | Q(status=RequirementDetail.STATUS.COTIZ),
                    requirement__code=requirement).order_by('line_number')
            elif search_type == 'PRODUCTOS':
                detalles = RequirementDetail.objects.filter(Q(status=RequirementDetail.STATUS.PEND) |
                                                               Q(status=RequirementDetail.STATUS.COTIZ),
                                                               requirement__code=requirement,
                                                               product__isnull=False).order_by('line_number')
            lista_detalles = []
            for detail in detalles:
                det = {}
                det['requirement'] = detail.id
                try:
                    det['code'] = detail.product.code
                    det['name'] = detail.product.description
                    det['unit'] = detail.product.unit_of_measure.code
                    # det['use'] = detail.use
                    det['quantity'] = str(detail.quantity - detail.served_quantity)
                    # det['price'] = str(detail.product.price)
                    # det['amount'] = str(detail.product.price*(detail.quantity-detail.served_quantity))
                    lista_detalles.append(det)
                except AttributeError:
                    pass
            formset = QuotationDetailFormSet(initial=lista_detalles)
            lista_json = []
            for form in formset:
                detalle_json = {}
                detalle_json['requirement'] = str(form['requirement'])
                detalle_json['code'] = str(form['code'])
                detalle_json['name'] = str(form['name'])
                detalle_json['unit'] = str(form['unit'])
                detalle_json['quantity'] = str(form['quantity'])
                lista_json.append(detalle_json)
            data = json.dumps(lista_json)
            return HttpResponse(data, 'application/json')


class RequirementTransfer(TemplateView):
    template_name = 'requerimientos/transferencia_requerimiento.html'

    def get_context_data(self, **kwargs):
        context = super(RequirementTransfer, self).get_context_data(**kwargs)
        # requerimientos = Requirement.objects.all()
        requerimientos = Requirement.get_requirements_ready_for_transfer()
        context['requerimientos'] = requerimientos
        return context


class RequirementExcelReport(TemplateView):
    def get(self, request, *args, **kwargs):
        requerimientos = Requirement.objects.active_requirements_by_user(request.user,
                                                                                  Requirement.STATUS.CANC)
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
        nombre_archivo = "RequirementList.xlsx"
        response = HttpResponse(content_type="application/ms-excel")
        contenido = "attachment; filename={0}".format(nombre_archivo)
        response["Content-Disposition"] = contenido
        wb.save(response)
        return response


class RequirementPdfReport(View):
    def get(self, request, *args, **kwargs):
        code = kwargs['code']
        requirement = Requirement.objects.get(code=code)
        response = HttpResponse(content_type='application/pdf')
        report = RequirementReport('A4', requirement)
        pdf = report.render()
        response.write(pdf)
        return response
