# -*- coding: utf-8 -*- 
from django.shortcuts import render
from django.views.generic.list import ListView
from contabilidad.models import Account, DocumentType, Tax, \
    Configuration, PaymentMethod, Company, StockType, ExchangeRate
from django.views.generic.base import View, TemplateView
from contabilidad.forms import DocumentTypeForm, AccountForm, \
    TaxForm, ConfigurationForm, PaymentMethodForm, ExchangeRateForm
from django.http.response import HttpResponseRedirect
from django.urls import reverse, reverse_lazy
from django.views.generic.edit import FormView, UpdateView, CreateView, \
    BaseCreateView
import simplejson
from django.http import HttpResponse
from django.views.generic.detail import DetailView
from openpyxl import Workbook
from contabilidad.forms import UploadForm
from tambox.views import CsvImportMixin, AjaxOnlyMixin
from seguridad.permisos import requiere
from django.utils.decorators import method_decorator
import datetime


class Dashboard(View):

    def get(self, request, *args, **kwargs):
        lista_notificaciones = []
        cant_cuentas_contables = Account.objects.count()
        document_type, creado = DocumentType.objects.get_or_create(sunat_code='PEC',
                                                                     defaults={'description': 'PECOSA',
                                                                               'name': 'PECOSA'})
        if creado:
            lista_notificaciones.append("Se ha creado el tipo de documento PECOSA")
        if cant_cuentas_contables == 0:
            lista_notificaciones.append("No se ha creado ninguna cuenta contable")
        context = {'notificaciones': lista_notificaciones}
        return render(request, 'contabilidad/tablero_contabilidad.html', context)


class AccountImport(CsvImportMixin, FormView):
    template_name = 'contabilidad/cargar_cuentas_contables.html'
    form_class = UploadForm
    success_url = reverse_lazy('contabilidad:account_list')

    def process_row(self, fila):
        Account.objects.get_or_create(account_number=fila[0].strip(),
                                             defaults={'description': fila[1].strip()})


class StockTypeImport(CsvImportMixin, FormView):
    template_name = 'contabilidad/cargar_tipos_existencias.html'
    form_class = UploadForm
    success_url = reverse_lazy('contabilidad:stock_type_list')

    def process_row(self, fila):
        StockType.objects.get_or_create(sunat_code=fila[0].strip(),
                                             defaults={'description': fila[1].strip()})


class DocumentTypeImport(CsvImportMixin, FormView):
    template_name = 'contabilidad/cargar_tipos_documentos.html'
    form_class = UploadForm
    success_url = reverse_lazy('contabilidad:document_type_list')

    def process_row(self, fila):
        DocumentType.objects.create(sunat_code=fila[0],
                                     name=fila[1],
                                     description=fila[1])


class PaymentMethodCreate(CreateView):
    model = PaymentMethod
    template_name = 'contabilidad/forma_pago.html'
    form_class = PaymentMethodForm

    @method_decorator(requiere('contabilidad.add_paymentmethod'))
    def dispatch(self, *args, **kwargs):
        return super(PaymentMethodCreate, self).dispatch(*args, **kwargs)

    def get_success_url(self):
        return reverse('contabilidad:payment_method_detail', args=[self.object.pk])


class DocumentTypeCreate(CreateView):
    model = DocumentType
    template_name = 'contabilidad/tipo_documento.html'
    form_class = DocumentTypeForm

    @method_decorator(requiere('contabilidad.add_documenttype'))
    def dispatch(self, *args, **kwargs):
        return super(DocumentTypeCreate, self).dispatch(*args, **kwargs)

    def get_success_url(self):
        return reverse('contabilidad:document_type_detail', args=[self.object.pk])


class ExchangeRateCreate(CreateView):
    model = ExchangeRate
    template_name = 'contabilidad/tipo_cambio.html'
    form_class = ExchangeRateForm

    @method_decorator(requiere('contabilidad.add_exchangerate'))
    def dispatch(self, *args, **kwargs):
        return super(ExchangeRateCreate, self).dispatch(*args, **kwargs)

    def get_success_url(self):
        return reverse('contabilidad:exchange_rate_detail', args=[self.object.pk])


class AccountCreate(CreateView):
    model = Account
    template_name = 'contabilidad/cuenta_contable.html'
    form_class = AccountForm

    @method_decorator(
        requiere('contabilidad.add_account'))
    def dispatch(self, *args, **kwargs):
        return super(AccountCreate, self).dispatch(*args, **kwargs)

    def get_success_url(self):
        return reverse('contabilidad:account_detail', args=[self.object.pk])


class TaxCreate(CreateView):
    model = Tax
    template_name = 'contabilidad/impuesto.html'
    form_class = TaxForm

    @method_decorator(requiere('contabilidad.add_tax'))
    def dispatch(self, *args, **kwargs):
        return super(TaxCreate, self).dispatch(*args, **kwargs)

    def get_success_url(self):
        return reverse('contabilidad:tax_detail', args=[self.object.pk])


class ConfigurationCreate(CreateView):
    model = Configuration
    template_name = 'contabilidad/configuracion.html'
    form_class = ConfigurationForm

    @method_decorator(requiere('contabilidad.add_configuration'))
    def dispatch(self, *args, **kwargs):
        return super(ConfigurationCreate, self).dispatch(*args, **kwargs)

    def get(self, request, *args, **kwargs):
        self.object = None
        configuration = Configuration.objects.first()
        if configuration is None:
            return super(BaseCreateView, self).get(request, *args, **kwargs)
        else:
            return HttpResponseRedirect(reverse('contabilidad:configuration_update', args=[configuration.pk]))

    def get_success_url(self):
        return reverse('contabilidad:configuration_update', args=[self.object.pk])


class ExchangeRateDetail(DetailView):
    model = ExchangeRate
    template_name = 'contabilidad/detalle_tipo_cambio.html'


class DocumentTypeDetail(DetailView):
    model = DocumentType
    template_name = 'contabilidad/detalle_tipo_documento.html'


class AccountDetail(DetailView):
    model = Account
    template_name = 'contabilidad/detalle_cuenta_contable.html'


class TaxDetail(DetailView):
    model = Tax
    template_name = 'contabilidad/detalle_impuesto.html'


class CompanyDetail(DetailView):
    model = Company
    template_name = 'contabilidad/detalle_empresa.html'


class PaymentMethodDetail(DetailView):
    model = PaymentMethod
    template_name = 'contabilidad/detalle_forma_pago.html'


class PaymentMethodDelete(TemplateView):
    http_method_names = ['post']

    @method_decorator(requiere('contabilidad.delete_paymentmethod'))
    def dispatch(self, *args, **kwargs):
        return super(PaymentMethodDelete, self).dispatch(*args, **kwargs)

    def post(self, request, *args, **kwargs):
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            code = request.POST['code']
            payment_method = PaymentMethod.objects.get(pk=code)
            forma_pago_json = {}
            forma_pago_json['code'] = payment_method.code
            forma_pago_json['description'] = payment_method.description
            if len(payment_method.purchase_orders.all()) > 0:
                forma_pago_json['relaciones'] = 'SI'
            elif len(payment_method.detalleordencompra_set.all()) > 0:
                forma_pago_json['relaciones'] = 'SI'
            elif len(payment_method.detallemovimiento_set.all()) > 0:
                forma_pago_json['relaciones'] = 'SI'
            else:
                forma_pago_json['relaciones'] = 'NO'
                PaymentMethod.objects.filter(pk=code).update(is_active=False)
            data = simplejson.dumps(forma_pago_json)
            return HttpResponse(data, 'application/json')


class DocumentTypeDelete(TemplateView):
    http_method_names = ['post']

    @method_decorator(requiere('contabilidad.delete_documenttype'))
    def dispatch(self, *args, **kwargs):
        return super(DocumentTypeDelete, self).dispatch(*args, **kwargs)

    def post(self, request, *args, **kwargs):
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            id = request.POST['id']
            document_type = DocumentType.objects.get(pk=id)
            tipo_documento_json = {}
            tipo_documento_json['sunat_code'] = document_type.sunat_code
            tipo_documento_json['name'] = document_type.name
            if len(document_type.movements.all()) > 0:
                tipo_documento_json['relaciones'] = 'SI'
            else:
                tipo_documento_json['relaciones'] = 'NO'
                DocumentType.objects.filter(pk=id).update(is_active=False)
            data = simplejson.dumps(tipo_documento_json)
            return HttpResponse(data, 'application/json')


class DocumentTypeList(ListView):
    model = DocumentType
    template_name = 'contabilidad/tipos_documento.html'
    context_object_name = 'tipos'
    queryset = DocumentType.objects.filter(is_active=True).order_by('name')

    @method_decorator(
        requiere('contabilidad.ver_tabla_tipos_documentos'))
    def dispatch(self, *args, **kwargs):
        return super(DocumentTypeList, self).dispatch(*args, **kwargs)


class ExchangeRateList(ListView):
    model = ExchangeRate
    template_name = 'contabilidad/tipos_cambio.html'
    context_object_name = 'tipos'

    @method_decorator(
        requiere('contabilidad.ver_tabla_tipos_cambio'))
    def dispatch(self, *args, **kwargs):
        return super(ExchangeRateList, self).dispatch(*args, **kwargs)


class AccountList(ListView):
    model = Account
    template_name = 'contabilidad/cuentas_contables.html'
    context_object_name = 'cuentas_contables'
    queryset = Account.objects.all().order_by('account_number')

    @method_decorator(
        requiere('contabilidad.ver_tabla_cuentas_contables'))
    def dispatch(self, *args, **kwargs):
        return super(AccountList, self).dispatch(*args, **kwargs)


class StockTypeList(ListView):
    model = StockType
    template_name = 'contabilidad/tipos_existencias.html'
    context_object_name = 'tipos_existencias'
    queryset = StockType.objects.all().order_by('sunat_code')

    @method_decorator(
        requiere('contabilidad.ver_tabla_tipos_existencias'))
    def dispatch(self, *args, **kwargs):
        return super(StockTypeList, self).dispatch(*args, **kwargs)


class PaymentMethodList(ListView):
    model = PaymentMethod
    template_name = 'contabilidad/formas_pago.html'
    context_object_name = 'formas_pago'
    paginate_by = 10
    queryset = PaymentMethod.objects.order_by('code')

    @method_decorator(requiere('contabilidad.ver_tabla_formas_pago'))
    def dispatch(self, *args, **kwargs):
        return super(PaymentMethodList, self).dispatch(*args, **kwargs)


class TaxList(ListView):
    model = Tax
    template_name = 'contabilidad/impuestos.html'
    context_object_name = 'impuestos'

    @method_decorator(
        requiere('contabilidad.ver_tabla_impuestos'))
    def dispatch(self, *args, **kwargs):
        return super(TaxList, self).dispatch(*args, **kwargs)


class PaymentMethodUpdate(UpdateView):
    model = PaymentMethod
    template_name = 'contabilidad/forma_pago.html'
    form_class = PaymentMethodForm

    @method_decorator(requiere('contabilidad.change_paymentmethod'))
    def dispatch(self, *args, **kwargs):
        return super(PaymentMethodUpdate, self).dispatch(*args, **kwargs)

    def get_success_url(self):
        return reverse('contabilidad:payment_method_detail', args=[self.object.pk])


class ExchangeRateUpdate(UpdateView):
    model = ExchangeRate
    template_name = 'contabilidad/tipo_cambio.html'
    form_class = ExchangeRateForm

    @method_decorator(requiere('contabilidad.change_exchangerate'))
    def dispatch(self, *args, **kwargs):
        return super(ExchangeRateUpdate, self).dispatch(*args, **kwargs)

    def get_success_url(self):
        return reverse('contabilidad:exchange_rate_detail', args=[self.object.pk])


class DocumentTypeUpdate(UpdateView):
    model = DocumentType
    template_name = 'contabilidad/tipo_documento.html'
    form_class = DocumentTypeForm

    @method_decorator(
        requiere('contabilidad.change_documenttype'))
    def dispatch(self, *args, **kwargs):
        return super(DocumentTypeUpdate, self).dispatch(*args, **kwargs)

    def get_success_url(self):
        return reverse('contabilidad:document_type_detail', args=[self.object.pk])


class AccountUpdate(UpdateView):
    model = Account
    template_name = 'contabilidad/cuenta_contable.html'
    form_class = AccountForm

    @method_decorator(
        requiere('contabilidad.change_account'))
    def dispatch(self, *args, **kwargs):
        return super(AccountUpdate, self).dispatch(*args, **kwargs)

    def get_success_url(self):
        return reverse('contabilidad:account_detail', args=[self.object.pk])


class ConfigurationUpdate(UpdateView):
    model = Configuration
    template_name = 'contabilidad/configuracion.html'
    form_class = ConfigurationForm

    @method_decorator(
        requiere('contabilidad.change_configuration'))
    def dispatch(self, *args, **kwargs):
        return super(ConfigurationUpdate, self).dispatch(*args, **kwargs)

    def get_success_url(self):
        return reverse('contabilidad:configuration_update', args=[self.object.pk])


class TaxUpdate(UpdateView):
    model = Tax
    template_name = 'contabilidad/impuesto.html'
    form_class = TaxForm

    @method_decorator(requiere('contabilidad.change_tax'))
    def dispatch(self, *args, **kwargs):
        return super(TaxUpdate, self).dispatch(*args, **kwargs)

    def get_initial(self):
        initial = super(TaxUpdate, self).get_initial()
        initial['start_date'] = self.object.start_date.strftime('%d/%m/%Y')
        if self.object.end_date is not None:
            initial['end_date'] = self.object.end_date.strftime('%d/%m/%Y')
        return initial

    def get_success_url(self):
        return reverse('contabilidad:tax_detail', args=[self.object.pk])


class ExchangeRateFetch(AjaxOnlyMixin, TemplateView):

    required_params = ('date',)

    def get(self, request, *args, **kwargs):
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            fecha_get = request.GET['date']
            anio = int(fecha_get[6:])
            month = int(fecha_get[3:5])
            dia = int(fecha_get[0:2])
            date = datetime.date(anio, month, dia)
            try:
                tipo_cambio = ExchangeRate.objects.get(date=date)
            except ExchangeRate.DoesNotExist:
                tipo_cambio = {'date': fecha_get, 'amount': 0}
            data = simplejson.dumps(tipo_cambio)
            return HttpResponse(data, 'application/json')


class AccountExcelReport(TemplateView):

    def get(self, request, *args, **kwargs):
        cuentas = Account.objects.all().order_by('account_number')
        wb = Workbook()
        ws = wb.active
        ws['B1'] = 'REPORTE DE UNIDADES DE MEDIDA'
        ws.merge_cells('B1:J1')
        ws['B3'] = 'CUENTA'
        ws['C3'] = 'DESCRIPCIÓN'
        ws['D3'] = 'DEPRECIACION'
        cont = 4
        for account_number in cuentas:
            ws.cell(row=cont, column=2).value = account_number.account_number
            ws.cell(row=cont, column=3).value = account_number.description
            ws.cell(row=cont, column=4).value = account_number.depreciation
            cont = cont + 1
        nombre_archivo = "AccountList.xlsx"
        response = HttpResponse(content_type="application/ms-excel")
        contenido = "attachment; filename={0}".format(nombre_archivo)
        response["Content-Disposition"] = contenido
        wb.save(response)
        return response


class PaymentMethodExcelReport(TemplateView):

    def get(self, request, *args, **kwargs):
        formas_pago = PaymentMethod.objects.all().order_by('code')
        wb = Workbook()
        ws = wb.active
        ws['B1'] = 'REPORTE DE FORMAS DE PAGO'
        ws.merge_cells('B1:J1')
        ws['B3'] = 'CODIGO'
        ws['C3'] = 'DESCRIPCIÓN'
        ws['D3'] = 'DIAS_CREDITO'
        cont = 4
        for payment_method in formas_pago:
            ws.cell(row=cont, column=2).value = payment_method.code
            ws.cell(row=cont, column=3).value = payment_method.description
            ws.cell(row=cont, column=4).value = payment_method.credit_days
            cont = cont + 1
        nombre_archivo = "PaymentMethodList.xlsx"
        response = HttpResponse(content_type="application/ms-excel")
        contenido = "attachment; filename={0}".format(nombre_archivo)
        response["Content-Disposition"] = contenido
        wb.save(response)
        return response


class DocumentTypeExcelReport(TemplateView):

    def get(self, request, *args, **kwargs):
        tipos = DocumentType.objects.all().order_by('sunat_code')
        wb = Workbook()
        ws = wb.active
        ws['B1'] = 'REPORTE DE TIPOS DE DOCUMENTOS'
        ws.merge_cells('B1:J1')
        ws['B3'] = 'CODIGO SUNAT'
        ws['C3'] = 'NOMBRE'
        ws['D3'] = 'DESCRIPCIÓN'
        cont = 4
        for tipo in tipos:
            ws.cell(row=cont, column=2).value = tipo.sunat_code
            ws.cell(row=cont, column=3).value = tipo.name
            ws.cell(row=cont, column=4).value = tipo.description
            cont = cont + 1
        nombre_archivo = "DocumentTypeList.xlsx"
        response = HttpResponse(content_type="application/ms-excel")
        contenido = "attachment; filename={0}".format(nombre_archivo)
        response["Content-Disposition"] = contenido
        wb.save(response)
        return response
