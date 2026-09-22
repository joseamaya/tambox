# -*- coding: utf-8 -*- 
from django.shortcuts import render
from django.views.generic.list import ListView
from accounting.models import Account, DocumentType, Tax,\
    Configuration, PaymentMethod, Company, StockType, ExchangeRate
from django.views.generic.base import View, TemplateView
from accounting.forms import DocumentTypeForm, AccountForm,\
    TaxForm, ConfigurationForm, PaymentMethodForm, ExchangeRateForm
from django.http.response import HttpResponseRedirect
from django.urls import reverse, reverse_lazy
from django.views.generic.edit import FormView, UpdateView, CreateView,\
    BaseCreateView
import simplejson
from django.http import HttpResponse
from django.views.generic.detail import DetailView
from openpyxl import Workbook
from accounting.forms import UploadForm
from tambox.views import CsvImportMixin, AjaxOnlyMixin
from security.permissions import requires
from django.utils.decorators import method_decorator
import datetime


class Dashboard(View):

    def get(self, request, *args, **kwargs):
        lista_notificaciones = []
        account_count = Account.objects.count()
        document_type, creado = DocumentType.objects.get_or_create(sunat_code='PEC',
                                                                     defaults={'description': 'PECOSA',
                                                                               'name': 'PECOSA'})
        if creado:
            lista_notificaciones.append("Se ha creado el tipo de documento PECOSA")
        if account_count == 0:
            lista_notificaciones.append("No se ha creado ninguna cuenta contable")
        context = {'notificaciones': lista_notificaciones}
        return render(request, 'accounting/accounting_dashboard.html', context)


class AccountImport(CsvImportMixin, FormView):
    template_name = 'accounting/account_upload.html'
    form_class = UploadForm
    success_url = reverse_lazy('accounting:account_list')

    def process_row(self, row):
        Account.objects.get_or_create(account_number=row[0].strip(),
                                             defaults={'description': row[1].strip()})


class StockTypeImport(CsvImportMixin, FormView):
    template_name = 'accounting/stock_type_upload.html'
    form_class = UploadForm
    success_url = reverse_lazy('accounting:stock_type_list')

    def process_row(self, row):
        StockType.objects.get_or_create(sunat_code=row[0].strip(),
                                             defaults={'description': row[1].strip()})


class DocumentTypeImport(CsvImportMixin, FormView):
    template_name = 'accounting/document_type_upload.html'
    form_class = UploadForm
    success_url = reverse_lazy('accounting:document_type_list')

    def process_row(self, row):
        DocumentType.objects.create(sunat_code=row[0],
                                     name=row[1],
                                     description=row[1])


class PaymentMethodCreate(CreateView):
    model = PaymentMethod
    template_name = 'accounting/payment_method_form.html'
    form_class = PaymentMethodForm

    @method_decorator(requires('accounting.add_paymentmethod'))
    def dispatch(self, *args, **kwargs):
        return super(PaymentMethodCreate, self).dispatch(*args, **kwargs)

    def get_success_url(self):
        return reverse('accounting:payment_method_detail', args=[self.object.pk])


class DocumentTypeCreate(CreateView):
    model = DocumentType
    template_name = 'accounting/document_type_form.html'
    form_class = DocumentTypeForm

    @method_decorator(requires('accounting.add_documenttype'))
    def dispatch(self, *args, **kwargs):
        return super(DocumentTypeCreate, self).dispatch(*args, **kwargs)

    def get_success_url(self):
        return reverse('accounting:document_type_detail', args=[self.object.pk])


class ExchangeRateCreate(CreateView):
    model = ExchangeRate
    template_name = 'accounting/exchange_rate_form.html'
    form_class = ExchangeRateForm

    @method_decorator(requires('accounting.add_exchangerate'))
    def dispatch(self, *args, **kwargs):
        return super(ExchangeRateCreate, self).dispatch(*args, **kwargs)

    def get_success_url(self):
        return reverse('accounting:exchange_rate_detail', args=[self.object.pk])


class AccountCreate(CreateView):
    model = Account
    template_name = 'accounting/account_form.html'
    form_class = AccountForm

    @method_decorator(
        requires('accounting.add_account'))
    def dispatch(self, *args, **kwargs):
        return super(AccountCreate, self).dispatch(*args, **kwargs)

    def get_success_url(self):
        return reverse('accounting:account_detail', args=[self.object.pk])


class TaxCreate(CreateView):
    model = Tax
    template_name = 'accounting/tax_form.html'
    form_class = TaxForm

    @method_decorator(requires('accounting.add_tax'))
    def dispatch(self, *args, **kwargs):
        return super(TaxCreate, self).dispatch(*args, **kwargs)

    def get_success_url(self):
        return reverse('accounting:tax_detail', args=[self.object.pk])


class ConfigurationCreate(CreateView):
    model = Configuration
    template_name = 'accounting/configuration.html'
    form_class = ConfigurationForm

    @method_decorator(requires('accounting.add_configuration'))
    def dispatch(self, *args, **kwargs):
        return super(ConfigurationCreate, self).dispatch(*args, **kwargs)

    def get(self, request, *args, **kwargs):
        self.object = None
        configuration = Configuration.objects.first()
        if configuration is None:
            return super(BaseCreateView, self).get(request, *args, **kwargs)
        else:
            return HttpResponseRedirect(reverse('accounting:configuration_update', args=[configuration.pk]))

    def get_success_url(self):
        return reverse('accounting:configuration_update', args=[self.object.pk])


class ExchangeRateDetail(DetailView):
    model = ExchangeRate
    template_name = 'accounting/exchange_rate_detail.html'


class DocumentTypeDetail(DetailView):
    model = DocumentType
    template_name = 'accounting/document_type_detail.html'


class AccountDetail(DetailView):
    model = Account
    template_name = 'accounting/account_detail.html'


class TaxDetail(DetailView):
    model = Tax
    template_name = 'accounting/tax_detail.html'


class CompanyDetail(DetailView):
    model = Company
    template_name = 'accounting/company_detail.html'


class PaymentMethodDetail(DetailView):
    model = PaymentMethod
    template_name = 'accounting/payment_method_detail.html'


class PaymentMethodDelete(TemplateView):
    http_method_names = ['post']

    @method_decorator(requires('accounting.delete_paymentmethod'))
    def dispatch(self, *args, **kwargs):
        return super(PaymentMethodDelete, self).dispatch(*args, **kwargs)

    def post(self, request, *args, **kwargs):
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            code = request.POST['code']
            payment_method = PaymentMethod.objects.get(pk=code)
            payment_method_json = {}
            payment_method_json['code'] = payment_method.code
            payment_method_json['description'] = payment_method.description
            if len(payment_method.purchase_orders.all()) > 0:
                payment_method_json['relaciones'] = 'SI'
            elif len(payment_method.detalleordencompra_set.all()) > 0:
                payment_method_json['relaciones'] = 'SI'
            elif len(payment_method.detallemovimiento_set.all()) > 0:
                payment_method_json['relaciones'] = 'SI'
            else:
                payment_method_json['relaciones'] = 'NO'
                PaymentMethod.objects.filter(pk=code).update(is_active=False)
            data = simplejson.dumps(payment_method_json)
            return HttpResponse(data, 'application/json')


class DocumentTypeDelete(TemplateView):
    http_method_names = ['post']

    @method_decorator(requires('accounting.delete_documenttype'))
    def dispatch(self, *args, **kwargs):
        return super(DocumentTypeDelete, self).dispatch(*args, **kwargs)

    def post(self, request, *args, **kwargs):
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            id = request.POST['id']
            document_type = DocumentType.objects.get(pk=id)
            document_type_json = {}
            document_type_json['sunat_code'] = document_type.sunat_code
            document_type_json['name'] = document_type.name
            if len(document_type.movements.all()) > 0:
                document_type_json['relaciones'] = 'SI'
            else:
                document_type_json['relaciones'] = 'NO'
                DocumentType.objects.filter(pk=id).update(is_active=False)
            data = simplejson.dumps(document_type_json)
            return HttpResponse(data, 'application/json')


class DocumentTypeList(ListView):
    model = DocumentType
    template_name = 'accounting/document_type_list.html'
    context_object_name = 'types'
    queryset = DocumentType.objects.filter(is_active=True).order_by('name')

    @method_decorator(
        requires('accounting.ver_tabla_tipos_documentos'))
    def dispatch(self, *args, **kwargs):
        return super(DocumentTypeList, self).dispatch(*args, **kwargs)


class ExchangeRateList(ListView):
    model = ExchangeRate
    template_name = 'accounting/exchange_rate_list.html'
    context_object_name = 'types'

    @method_decorator(
        requires('accounting.ver_tabla_tipos_cambio'))
    def dispatch(self, *args, **kwargs):
        return super(ExchangeRateList, self).dispatch(*args, **kwargs)


class AccountList(ListView):
    model = Account
    template_name = 'accounting/account_list.html'
    context_object_name = 'chart_of_accounts'
    queryset = Account.objects.all().order_by('account_number')

    @method_decorator(
        requires('accounting.ver_tabla_cuentas_contables'))
    def dispatch(self, *args, **kwargs):
        return super(AccountList, self).dispatch(*args, **kwargs)


class StockTypeList(ListView):
    model = StockType
    template_name = 'accounting/stock_type_list.html'
    context_object_name = 'tipos_existencias'
    queryset = StockType.objects.all().order_by('sunat_code')

    @method_decorator(
        requires('accounting.ver_tabla_tipos_existencias'))
    def dispatch(self, *args, **kwargs):
        return super(StockTypeList, self).dispatch(*args, **kwargs)


class PaymentMethodList(ListView):
    model = PaymentMethod
    template_name = 'accounting/payment_method_list.html'
    context_object_name = 'payment_methods'
    paginate_by = 10
    queryset = PaymentMethod.objects.order_by('code')

    @method_decorator(requires('accounting.ver_tabla_formas_pago'))
    def dispatch(self, *args, **kwargs):
        return super(PaymentMethodList, self).dispatch(*args, **kwargs)


class TaxList(ListView):
    model = Tax
    template_name = 'accounting/tax_list.html'
    context_object_name = 'impuestos'

    @method_decorator(
        requires('accounting.ver_tabla_impuestos'))
    def dispatch(self, *args, **kwargs):
        return super(TaxList, self).dispatch(*args, **kwargs)


class PaymentMethodUpdate(UpdateView):
    model = PaymentMethod
    template_name = 'accounting/payment_method_form.html'
    form_class = PaymentMethodForm

    @method_decorator(requires('accounting.change_paymentmethod'))
    def dispatch(self, *args, **kwargs):
        return super(PaymentMethodUpdate, self).dispatch(*args, **kwargs)

    def get_success_url(self):
        return reverse('accounting:payment_method_detail', args=[self.object.pk])


class ExchangeRateUpdate(UpdateView):
    model = ExchangeRate
    template_name = 'accounting/exchange_rate_form.html'
    form_class = ExchangeRateForm

    @method_decorator(requires('accounting.change_exchangerate'))
    def dispatch(self, *args, **kwargs):
        return super(ExchangeRateUpdate, self).dispatch(*args, **kwargs)

    def get_success_url(self):
        return reverse('accounting:exchange_rate_detail', args=[self.object.pk])


class DocumentTypeUpdate(UpdateView):
    model = DocumentType
    template_name = 'accounting/document_type_form.html'
    form_class = DocumentTypeForm

    @method_decorator(
        requires('accounting.change_documenttype'))
    def dispatch(self, *args, **kwargs):
        return super(DocumentTypeUpdate, self).dispatch(*args, **kwargs)

    def get_success_url(self):
        return reverse('accounting:document_type_detail', args=[self.object.pk])


class AccountUpdate(UpdateView):
    model = Account
    template_name = 'accounting/account_form.html'
    form_class = AccountForm

    @method_decorator(
        requires('accounting.change_account'))
    def dispatch(self, *args, **kwargs):
        return super(AccountUpdate, self).dispatch(*args, **kwargs)

    def get_success_url(self):
        return reverse('accounting:account_detail', args=[self.object.pk])


class ConfigurationUpdate(UpdateView):
    model = Configuration
    template_name = 'accounting/configuration.html'
    form_class = ConfigurationForm

    @method_decorator(
        requires('accounting.change_configuration'))
    def dispatch(self, *args, **kwargs):
        return super(ConfigurationUpdate, self).dispatch(*args, **kwargs)

    def get_success_url(self):
        return reverse('accounting:configuration_update', args=[self.object.pk])


class TaxUpdate(UpdateView):
    model = Tax
    template_name = 'accounting/tax_form.html'
    form_class = TaxForm

    @method_decorator(requires('accounting.change_tax'))
    def dispatch(self, *args, **kwargs):
        return super(TaxUpdate, self).dispatch(*args, **kwargs)

    def get_initial(self):
        initial = super(TaxUpdate, self).get_initial()
        initial['start_date'] = self.object.start_date.strftime('%d/%m/%Y')
        if self.object.end_date is not None:
            initial['end_date'] = self.object.end_date.strftime('%d/%m/%Y')
        return initial

    def get_success_url(self):
        return reverse('accounting:tax_detail', args=[self.object.pk])


class ExchangeRateFetch(AjaxOnlyMixin, TemplateView):

    required_params = ('date',)

    def get(self, request, *args, **kwargs):
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            fetched_date = request.GET['date']
            year = int(fetched_date[6:])
            month = int(fetched_date[3:5])
            dia = int(fetched_date[0:2])
            date = datetime.date(year, month, dia)
            try:
                exchange_rate = ExchangeRate.objects.get(date=date)
            except ExchangeRate.DoesNotExist:
                exchange_rate = {'date': fetched_date, 'amount': 0}
            data = simplejson.dumps(exchange_rate)
            return HttpResponse(data, 'application/json')


class AccountExcelReport(TemplateView):

    def get(self, request, *args, **kwargs):
        accounts = Account.objects.all().order_by('account_number')
        wb = Workbook()
        ws = wb.active
        ws['B1'] = 'REPORTE DE ONES DE MEDIDA'
        ws.merge_cells('B1:J1')
        ws['B3'] = 'CUENTA'
        ws['C3'] = 'DESCRIPCIÓN'
        ws['D3'] = 'DEPRECIACION'
        cont = 4
        for account_number in accounts:
            ws.cell(row=cont, column=2).value = account_number.account_number
            ws.cell(row=cont, column=3).value = account_number.description
            ws.cell(row=cont, column=4).value = account_number.depreciation
            cont = cont + 1
        file_name = "AccountList.xlsx"
        response = HttpResponse(content_type="application/ms-excel")
        contenido = "attachment; filename={0}".format(file_name)
        response["Content-Disposition"] = contenido
        wb.save(response)
        return response


class PaymentMethodExcelReport(TemplateView):

    def get(self, request, *args, **kwargs):
        payment_methods = PaymentMethod.objects.all().order_by('code')
        wb = Workbook()
        ws = wb.active
        ws['B1'] = 'REPORTE DE FORMAS DE PAGO'
        ws.merge_cells('B1:J1')
        ws['B3'] = 'CODIGO'
        ws['C3'] = 'DESCRIPCIÓN'
        ws['D3'] = 'DIAS_CREDITO'
        cont = 4
        for payment_method in payment_methods:
            ws.cell(row=cont, column=2).value = payment_method.code
            ws.cell(row=cont, column=3).value = payment_method.description
            ws.cell(row=cont, column=4).value = payment_method.credit_days
            cont = cont + 1
        file_name = "PaymentMethodList.xlsx"
        response = HttpResponse(content_type="application/ms-excel")
        contenido = "attachment; filename={0}".format(file_name)
        response["Content-Disposition"] = contenido
        wb.save(response)
        return response


class DocumentTypeExcelReport(TemplateView):

    def get(self, request, *args, **kwargs):
        types = DocumentType.objects.all().order_by('sunat_code')
        wb = Workbook()
        ws = wb.active
        ws['B1'] = 'REPORTE DE TIPOS DE DOCUMENTOS'
        ws.merge_cells('B1:J1')
        ws['B3'] = 'CODIGO SUNAT'
        ws['C3'] = 'NOMBRE'
        ws['D3'] = 'DESCRIPCIÓN'
        cont = 4
        for type in types:
            ws.cell(row=cont, column=2).value = type.sunat_code
            ws.cell(row=cont, column=3).value = type.name
            ws.cell(row=cont, column=4).value = type.description
            cont = cont + 1
        file_name = "DocumentTypeList.xlsx"
        response = HttpResponse(content_type="application/ms-excel")
        contenido = "attachment; filename={0}".format(file_name)
        response["Content-Disposition"] = contenido
        wb.save(response)
        return response
