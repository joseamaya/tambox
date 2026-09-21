# -*- coding: utf-8 -*- 
from django.shortcuts import render
from django.views.generic.list import ListView
from contabilidad.models import CuentaContable, TipoDocumento, Impuesto, \
    Configuracion, FormaPago, Empresa, TipoExistencia, TipoCambio
from django.views.generic.base import View, TemplateView
from contabilidad.forms import TipoDocumentoForm, CuentaContableForm, \
    ImpuestoForm, ConfiguracionForm, FormaPagoForm, TipoCambioForm
from django.http.response import HttpResponseRedirect
from django.urls import reverse, reverse_lazy
from django.views.generic.edit import FormView, UpdateView, CreateView, \
    BaseCreateView
import simplejson
from django.http import HttpResponse
from django.views.generic.detail import DetailView
from openpyxl import Workbook
from contabilidad.forms import UploadForm
from tambox.vistas import CargarCsvMixin, SoloAjaxMixin
from seguridad.permisos import requiere
from django.utils.decorators import method_decorator
import datetime


class Tablero(View):

    def get(self, request, *args, **kwargs):
        lista_notificaciones = []
        cant_cuentas_contables = CuentaContable.objects.count()
        document_type, creado = TipoDocumento.objects.get_or_create(sunat_code='PEC',
                                                                     defaults={'description': 'PECOSA',
                                                                               'name': 'PECOSA'})
        if creado:
            lista_notificaciones.append("Se ha creado el tipo de documento PECOSA")
        if cant_cuentas_contables == 0:
            lista_notificaciones.append("No se ha creado ninguna cuenta contable")
        context = {'notificaciones': lista_notificaciones}
        return render(request, 'contabilidad/tablero_contabilidad.html', context)


class CargarCuentasContables(CargarCsvMixin, FormView):
    template_name = 'contabilidad/cargar_cuentas_contables.html'
    form_class = UploadForm
    success_url = reverse_lazy('contabilidad:cuentas_contables')

    def procesar_fila(self, fila):
        CuentaContable.objects.get_or_create(account_number=fila[0].strip(),
                                             defaults={'description': fila[1].strip()})


class CargarTiposExistencias(CargarCsvMixin, FormView):
    template_name = 'contabilidad/cargar_tipos_existencias.html'
    form_class = UploadForm
    success_url = reverse_lazy('contabilidad:tipos_existencias')

    def procesar_fila(self, fila):
        TipoExistencia.objects.get_or_create(sunat_code=fila[0].strip(),
                                             defaults={'description': fila[1].strip()})


class CargarTiposDocumentos(CargarCsvMixin, FormView):
    template_name = 'contabilidad/cargar_tipos_documentos.html'
    form_class = UploadForm
    success_url = reverse_lazy('contabilidad:tipos_documentos')

    def procesar_fila(self, fila):
        TipoDocumento.objects.create(sunat_code=fila[0],
                                     name=fila[1],
                                     description=fila[1])


class CrearFormaPago(CreateView):
    model = FormaPago
    template_name = 'contabilidad/forma_pago.html'
    form_class = FormaPagoForm

    @method_decorator(requiere('contabilidad.add_formapago'))
    def dispatch(self, *args, **kwargs):
        return super(CrearFormaPago, self).dispatch(*args, **kwargs)

    def get_success_url(self):
        return reverse('contabilidad:detalle_forma_pago', args=[self.object.pk])


class CrearTipoDocumento(CreateView):
    model = TipoDocumento
    template_name = 'contabilidad/tipo_documento.html'
    form_class = TipoDocumentoForm

    @method_decorator(requiere('contabilidad.add_tipodocumento'))
    def dispatch(self, *args, **kwargs):
        return super(CrearTipoDocumento, self).dispatch(*args, **kwargs)

    def get_success_url(self):
        return reverse('contabilidad:detalle_tipo_documento', args=[self.object.pk])


class CrearTipoCambio(CreateView):
    model = TipoCambio
    template_name = 'contabilidad/tipo_cambio.html'
    form_class = TipoCambioForm

    @method_decorator(requiere('contabilidad.add_tipocambio'))
    def dispatch(self, *args, **kwargs):
        return super(CrearTipoCambio, self).dispatch(*args, **kwargs)

    def get_success_url(self):
        return reverse('contabilidad:detalle_tipo_cambio', args=[self.object.pk])


class CrearCuentaContable(CreateView):
    model = CuentaContable
    template_name = 'contabilidad/cuenta_contable.html'
    form_class = CuentaContableForm

    @method_decorator(
        requiere('contabilidad.add_cuentacontable'))
    def dispatch(self, *args, **kwargs):
        return super(CrearCuentaContable, self).dispatch(*args, **kwargs)

    def get_success_url(self):
        return reverse('contabilidad:detalle_cuenta_contable', args=[self.object.pk])


class CrearImpuesto(CreateView):
    model = Impuesto
    template_name = 'contabilidad/impuesto.html'
    form_class = ImpuestoForm

    @method_decorator(requiere('contabilidad.add_impuesto'))
    def dispatch(self, *args, **kwargs):
        return super(CrearImpuesto, self).dispatch(*args, **kwargs)

    def get_success_url(self):
        return reverse('contabilidad:detalle_impuesto', args=[self.object.pk])


class CrearConfiguracion(CreateView):
    model = Configuracion
    template_name = 'contabilidad/configuracion.html'
    form_class = ConfiguracionForm

    @method_decorator(requiere('contabilidad.add_configuracion'))
    def dispatch(self, *args, **kwargs):
        return super(CrearConfiguracion, self).dispatch(*args, **kwargs)

    def get(self, request, *args, **kwargs):
        self.object = None
        configuracion = Configuracion.objects.first()
        if configuracion is None:
            return super(BaseCreateView, self).get(request, *args, **kwargs)
        else:
            return HttpResponseRedirect(reverse('contabilidad:modificar_configuracion', args=[configuracion.pk]))

    def get_success_url(self):
        return reverse('contabilidad:modificar_configuracion', args=[self.object.pk])


class DetalleTipoCambio(DetailView):
    model = TipoCambio
    template_name = 'contabilidad/detalle_tipo_cambio.html'


class DetalleTipoDocumento(DetailView):
    model = TipoDocumento
    template_name = 'contabilidad/detalle_tipo_documento.html'


class DetalleCuentaContable(DetailView):
    model = CuentaContable
    template_name = 'contabilidad/detalle_cuenta_contable.html'


class DetalleImpuesto(DetailView):
    model = Impuesto
    template_name = 'contabilidad/detalle_impuesto.html'


class DetalleEmpresa(DetailView):
    model = Empresa
    template_name = 'contabilidad/detalle_empresa.html'


class DetalleFormaPago(DetailView):
    model = FormaPago
    template_name = 'contabilidad/detalle_forma_pago.html'


class EliminarFormaPago(TemplateView):
    http_method_names = ['post']

    @method_decorator(requiere('contabilidad.delete_formapago'))
    def dispatch(self, *args, **kwargs):
        return super(EliminarFormaPago, self).dispatch(*args, **kwargs)

    def post(self, request, *args, **kwargs):
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            code = request.POST['code']
            forma_pago = FormaPago.objects.get(pk=code)
            forma_pago_json = {}
            forma_pago_json['code'] = forma_pago.code
            forma_pago_json['description'] = forma_pago.description
            if len(forma_pago.purchase_orders.all()) > 0:
                forma_pago_json['relaciones'] = 'SI'
            elif len(forma_pago.detalleordencompra_set.all()) > 0:
                forma_pago_json['relaciones'] = 'SI'
            elif len(forma_pago.detallemovimiento_set.all()) > 0:
                forma_pago_json['relaciones'] = 'SI'
            else:
                forma_pago_json['relaciones'] = 'NO'
                FormaPago.objects.filter(pk=code).update(is_active=False)
            data = simplejson.dumps(forma_pago_json)
            return HttpResponse(data, 'application/json')


class EliminarTipoDocumento(TemplateView):
    http_method_names = ['post']

    @method_decorator(requiere('contabilidad.delete_tipodocumento'))
    def dispatch(self, *args, **kwargs):
        return super(EliminarTipoDocumento, self).dispatch(*args, **kwargs)

    def post(self, request, *args, **kwargs):
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            id = request.POST['id']
            document_type = TipoDocumento.objects.get(pk=id)
            tipo_documento_json = {}
            tipo_documento_json['sunat_code'] = document_type.sunat_code
            tipo_documento_json['name'] = document_type.name
            if len(document_type.movements.all()) > 0:
                tipo_documento_json['relaciones'] = 'SI'
            else:
                tipo_documento_json['relaciones'] = 'NO'
                TipoDocumento.objects.filter(pk=id).update(is_active=False)
            data = simplejson.dumps(tipo_documento_json)
            return HttpResponse(data, 'application/json')


class ListadoTiposDocumentos(ListView):
    model = TipoDocumento
    template_name = 'contabilidad/tipos_documento.html'
    context_object_name = 'tipos'
    queryset = TipoDocumento.objects.filter(is_active=True).order_by('name')

    @method_decorator(
        requiere('contabilidad.ver_tabla_tipos_documentos'))
    def dispatch(self, *args, **kwargs):
        return super(ListadoTiposDocumentos, self).dispatch(*args, **kwargs)


class ListadoTiposCambio(ListView):
    model = TipoCambio
    template_name = 'contabilidad/tipos_cambio.html'
    context_object_name = 'tipos'

    @method_decorator(
        requiere('contabilidad.ver_tabla_tipos_cambio'))
    def dispatch(self, *args, **kwargs):
        return super(ListadoTiposCambio, self).dispatch(*args, **kwargs)


class ListadoCuentasContables(ListView):
    model = CuentaContable
    template_name = 'contabilidad/cuentas_contables.html'
    context_object_name = 'cuentas_contables'
    queryset = CuentaContable.objects.all().order_by('account_number')

    @method_decorator(
        requiere('contabilidad.ver_tabla_cuentas_contables'))
    def dispatch(self, *args, **kwargs):
        return super(ListadoCuentasContables, self).dispatch(*args, **kwargs)


class ListadoTiposExistencias(ListView):
    model = TipoExistencia
    template_name = 'contabilidad/tipos_existencias.html'
    context_object_name = 'tipos_existencias'
    queryset = TipoExistencia.objects.all().order_by('sunat_code')

    @method_decorator(
        requiere('contabilidad.ver_tabla_tipos_existencias'))
    def dispatch(self, *args, **kwargs):
        return super(ListadoTiposExistencias, self).dispatch(*args, **kwargs)


class ListadoFormasPago(ListView):
    model = FormaPago
    template_name = 'contabilidad/formas_pago.html'
    context_object_name = 'formas_pago'
    paginate_by = 10
    queryset = FormaPago.objects.order_by('code')

    @method_decorator(requiere('contabilidad.ver_tabla_formas_pago'))
    def dispatch(self, *args, **kwargs):
        return super(ListadoFormasPago, self).dispatch(*args, **kwargs)


class ListadoImpuestos(ListView):
    model = Impuesto
    template_name = 'contabilidad/impuestos.html'
    context_object_name = 'impuestos'

    @method_decorator(
        requiere('contabilidad.ver_tabla_impuestos'))
    def dispatch(self, *args, **kwargs):
        return super(ListadoImpuestos, self).dispatch(*args, **kwargs)


class ModificarFormaPago(UpdateView):
    model = FormaPago
    template_name = 'contabilidad/forma_pago.html'
    form_class = FormaPagoForm

    @method_decorator(requiere('contabilidad.change_formapago'))
    def dispatch(self, *args, **kwargs):
        return super(ModificarFormaPago, self).dispatch(*args, **kwargs)

    def get_success_url(self):
        return reverse('contabilidad:detalle_forma_pago', args=[self.object.pk])


class ModificarTipoCambio(UpdateView):
    model = TipoCambio
    template_name = 'contabilidad/tipo_cambio.html'
    form_class = TipoCambioForm

    @method_decorator(requiere('contabilidad.change_tipocambio'))
    def dispatch(self, *args, **kwargs):
        return super(ModificarTipoCambio, self).dispatch(*args, **kwargs)

    def get_success_url(self):
        return reverse('contabilidad:detalle_tipo_cambio', args=[self.object.pk])


class ModificarTipoDocumento(UpdateView):
    model = TipoDocumento
    template_name = 'contabilidad/tipo_documento.html'
    form_class = TipoDocumentoForm

    @method_decorator(
        requiere('contabilidad.change_tipodocumento'))
    def dispatch(self, *args, **kwargs):
        return super(ModificarTipoDocumento, self).dispatch(*args, **kwargs)

    def get_success_url(self):
        return reverse('contabilidad:detalle_tipo_documento', args=[self.object.pk])


class ModificarCuentaContable(UpdateView):
    model = CuentaContable
    template_name = 'contabilidad/cuenta_contable.html'
    form_class = CuentaContableForm

    @method_decorator(
        requiere('contabilidad.change_cuentacontable'))
    def dispatch(self, *args, **kwargs):
        return super(ModificarCuentaContable, self).dispatch(*args, **kwargs)

    def get_success_url(self):
        return reverse('contabilidad:detalle_cuenta_contable', args=[self.object.pk])


class ModificarConfiguracion(UpdateView):
    model = Configuracion
    template_name = 'contabilidad/configuracion.html'
    form_class = ConfiguracionForm

    @method_decorator(
        requiere('contabilidad.change_configuracion'))
    def dispatch(self, *args, **kwargs):
        return super(ModificarConfiguracion, self).dispatch(*args, **kwargs)

    def get_success_url(self):
        return reverse('contabilidad:modificar_configuracion', args=[self.object.pk])


class ModificarImpuesto(UpdateView):
    model = Impuesto
    template_name = 'contabilidad/impuesto.html'
    form_class = ImpuestoForm

    @method_decorator(requiere('contabilidad.change_impuesto'))
    def dispatch(self, *args, **kwargs):
        return super(ModificarImpuesto, self).dispatch(*args, **kwargs)

    def get_initial(self):
        initial = super(ModificarImpuesto, self).get_initial()
        initial['start_date'] = self.object.start_date.strftime('%d/%m/%Y')
        if self.object.end_date is not None:
            initial['end_date'] = self.object.end_date.strftime('%d/%m/%Y')
        return initial

    def get_success_url(self):
        return reverse('contabilidad:detalle_impuesto', args=[self.object.pk])


class ObtenerTipoCambio(SoloAjaxMixin, TemplateView):

    parametros_requeridos = ('date',)

    def get(self, request, *args, **kwargs):
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            fecha_get = request.GET['date']
            anio = int(fecha_get[6:])
            month = int(fecha_get[3:5])
            dia = int(fecha_get[0:2])
            date = datetime.date(anio, month, dia)
            try:
                tipo_cambio = TipoCambio.objects.get(date=date)
            except TipoCambio.DoesNotExist:
                tipo_cambio = {'date': fecha_get, 'amount': 0}
            data = simplejson.dumps(tipo_cambio)
            return HttpResponse(data, 'application/json')


class ReporteExcelCuentasContables(TemplateView):

    def get(self, request, *args, **kwargs):
        cuentas = CuentaContable.objects.all().order_by('account_number')
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
        nombre_archivo = "ListadoCuentasContables.xlsx"
        response = HttpResponse(content_type="application/ms-excel")
        contenido = "attachment; filename={0}".format(nombre_archivo)
        response["Content-Disposition"] = contenido
        wb.save(response)
        return response


class ReporteExcelFormasPago(TemplateView):

    def get(self, request, *args, **kwargs):
        formas_pago = FormaPago.objects.all().order_by('code')
        wb = Workbook()
        ws = wb.active
        ws['B1'] = 'REPORTE DE FORMAS DE PAGO'
        ws.merge_cells('B1:J1')
        ws['B3'] = 'CODIGO'
        ws['C3'] = 'DESCRIPCIÓN'
        ws['D3'] = 'DIAS_CREDITO'
        cont = 4
        for forma_pago in formas_pago:
            ws.cell(row=cont, column=2).value = forma_pago.code
            ws.cell(row=cont, column=3).value = forma_pago.description
            ws.cell(row=cont, column=4).value = forma_pago.credit_days
            cont = cont + 1
        nombre_archivo = "ListadoFormasPago.xlsx"
        response = HttpResponse(content_type="application/ms-excel")
        contenido = "attachment; filename={0}".format(nombre_archivo)
        response["Content-Disposition"] = contenido
        wb.save(response)
        return response


class ReporteExcelTiposDocumentos(TemplateView):

    def get(self, request, *args, **kwargs):
        tipos = TipoDocumento.objects.all().order_by('sunat_code')
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
        nombre_archivo = "ListadoTiposDocumentos.xlsx"
        response = HttpResponse(content_type="application/ms-excel")
        contenido = "attachment; filename={0}".format(nombre_archivo)
        response["Content-Disposition"] = contenido
        wb.save(response)
        return response
