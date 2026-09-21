# -*- coding: utf-8 -*- 
import logging

from django.views.generic.base import View, TemplateView
from django.views.generic.list import ListView
from django.views.generic.edit import FormView, UpdateView, CreateView
from django.urls import reverse_lazy, reverse
from django.http.response import HttpResponseRedirect
import json
from django.http import HttpResponse
import simplejson
from openpyxl import Workbook
from django.views.generic.detail import DetailView
from seguridad.permisos import requires
from django.utils.decorators import method_decorator
from contabilidad.forms import UploadForm
from django.shortcuts import render
from productos.models import Product, UnitOfMeasure, ProductGroup
from productos.forms import ProductGroupForm, ProductForm, ServiceForm, \
    UnitOfMeasureForm
from contabilidad.models import Account, StockType
from tambox.views import CsvImportMixin, AjaxOnlyMixin

logger = logging.getLogger(__name__)


class Dashboard(View):

    def get(self, request, *args, **kwargs):
        lista_notificaciones = []
        cant_productos = Product.objects.filter(is_service=False).count()
        cant_tipos_unidad_medida = UnitOfMeasure.objects.count()
        cant_grupos_suministros = ProductGroup.objects.count()
        cant_servicios = Product.objects.filter(is_service=True).count()
        unit_of_measure, creado = UnitOfMeasure.objects.get_or_create(code='SERV',
                                                                   defaults={'description': 'SERVICIO'})
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
        return render(request, 'productos/tablero_productos.html', context)


class ProductDescriptionSearch(AjaxOnlyMixin, TemplateView):

    required_params = ('description', 'tipo_busqueda')

    def get(self, request, *args, **kwargs):
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            description = request.GET['description']
            tipo_busqueda = request.GET['tipo_busqueda']
            if tipo_busqueda == 'TODOS':
                productos = Product.objects.filter(description__icontains=description).select_related(
                    'unit_of_measure').order_by('description')[:20]
            elif tipo_busqueda == 'PRODUCTOS':
                productos = Product.objects.filter(description__icontains=description,
                                                    is_service=False).select_related(
                    'unit_of_measure').order_by('description')[:20]
            elif tipo_busqueda == 'SERVICIOS':
                productos = Product.objects.filter(description__icontains=description,
                                                    is_service=True).select_related(
                    'unit_of_measure').order_by('description')[:20]

            lista_productos = []
            for product in productos:
                producto_json = {}
                producto_json['label'] = product.description
                producto_json['code'] = product.code
                producto_json['description'] = product.description
                producto_json['unidad'] = product.unit_of_measure.description
                producto_json['price'] = str(product.price)
                lista_productos.append(producto_json)
            data = json.dumps(lista_productos)
            return HttpResponse(data, 'application/json')


class ProductCodeSearch(AjaxOnlyMixin, TemplateView):

    required_params = ('code',)

    def get(self, request, *args, **kwargs):
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            code = request.GET['code']
            productos = Product.objects.filter(code__icontains=code).select_related('unit_of_measure')[:20]
            lista_productos = []
            for product in productos:
                producto_json = {}
                producto_json['label'] = product.code
                producto_json['code'] = product.code
                producto_json['description'] = product.description
                producto_json['unidad'] = product.unit_of_measure.description
                producto_json['price'] = str(product.price)
                lista_productos.append(producto_json)
            data = json.dumps(lista_productos)
            return HttpResponse(data, 'application/json')


class ProductGroupImport(CsvImportMixin, FormView):
    template_name = 'productos/cargar_grupo_productos.html'
    form_class = UploadForm
    success_url = reverse_lazy('productos:product_group_list')

    def process_row(self, fila):
        try:
            account_number = Account.objects.get(account_number=fila[0])
            ProductGroup.objects.get_or_create(description=fila[1],
                                                 defaults={'account': account_number})
        except Account.DoesNotExist:
            pass


class ServiceImport(CsvImportMixin, FormView):
    template_name = 'productos/cargar_servicios.html'
    form_class = UploadForm
    success_url = reverse_lazy('productos:service_list')

    def form_valid(self, form):
        try:
            return super(ServiceImport, self).form_valid(form)
        except ProductGroup.DoesNotExist:
            return HttpResponseRedirect(reverse('productos:product_group_create'))

    def process_row(self, fila):
        grupo = ProductGroup.objects.get(code=fila[0].strip())
        Product.objects.get_or_create(description=fila[1],
                                       defaults={'product_group': grupo,
                                                 'is_service': True})


class ProductImport(CsvImportMixin, FormView):
    template_name = 'productos/cargar_productos.html'
    form_class = UploadForm
    success_url = reverse_lazy('productos:product_list')

    def process_row(self, fila):
        try:
            grupo = ProductGroup.objects.get(code=fila[0].strip())
            cod_und = fila[2][0:5]
            und, creado = UnitOfMeasure.objects.get_or_create(code=cod_und.strip(),
                                                             defaults={'code': cod_und,
                                                                       'description': fila[2].strip()})
            if fila[3] != '':
                price = fila[3]
            else:
                price = 0
            stock_type = StockType.objects.get(sunat_code=fila[4].strip())
            product, creado = Product.objects.get_or_create(description=fila[1].strip(),
                                                              defaults={'unit_of_measure': und,
                                                                        'product_group': grupo,
                                                                        'price': price,
                                                                        'stock_type': stock_type})
        except Exception:
            logger.warning("No se pudo importar el producto %s", fila[1], exc_info=True)


class ProductStockQuery(AjaxOnlyMixin, TemplateView):

    required_params = ('code',)

    def get(self, request, *args, **kwargs):
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            code = request.GET['code']
            product = Product.objects.get(code=code)
            producto_json = {}
            producto_json['stock'] = product.stock
            data = simplejson.dumps(producto_json)
            return HttpResponse(data, 'application/json')


class ProductGroupCreate(CreateView):
    model = ProductGroup
    template_name = 'productos/grupo_productos.html'
    form_class = ProductGroupForm
    success_url = reverse_lazy('productos:product_group_list')

    @method_decorator(requires('productos.add_productgroup'))
    def dispatch(self, *args, **kwargs):
        return super(ProductGroupCreate, self).dispatch(*args, **kwargs)

    def get_success_url(self):
        return reverse('productos:product_group_detail', args=[self.object.pk])


class ProductCreate(CreateView):
    model = Product
    context_object_name = 'product'
    template_name = 'productos/producto.html'
    form_class = ProductForm

    @method_decorator(requires('productos.add_product'))
    def dispatch(self, *args, **kwargs):
        return super(ProductCreate, self).dispatch(*args, **kwargs)

    def get_success_url(self):
        return reverse('productos:product_detail', args=[self.object.pk])


class UnitOfMeasureCreate(CreateView):
    template_name = 'productos/unidad_medida.html'
    form_class = UnitOfMeasureForm

    @method_decorator(requires('productos.add_unitofmeasure'))
    def dispatch(self, *args, **kwargs):
        return super(UnitOfMeasureCreate, self).dispatch(*args, **kwargs)

    def form_valid(self, form):
        self.object = form.save(commit=False)
        self.object.changed_by = self.request.user
        self.object.save()
        return super(UnitOfMeasureCreate, self).form_valid(form)

    def get_success_url(self):
        return reverse('productos:unit_of_measure_detail', args=[self.object.pk])


class ServiceCreate(CreateView):
    template_name = 'productos/servicio.html'
    form_class = ServiceForm

    @method_decorator(requires('productos.add_product'))
    def dispatch(self, *args, **kwargs):
        return super(ServiceCreate, self).dispatch(*args, **kwargs)

    def get_success_url(self):
        return reverse('productos:service_detail', args=[self.object.code])


class ProductDetail(DetailView):
    model = Product
    template_name = 'productos/detalle_producto.html'


class ProductGroupDetail(DetailView):
    model = ProductGroup
    template_name = 'productos/detalle_grupo_productos.html'


class UnitOfMeasureDetail(DetailView):
    model = UnitOfMeasure
    template_name = 'productos/detalle_unidad_medida.html'


class ServiceDetail(DetailView):
    model = Product
    template_name = 'productos/detalle_servicio.html'


class UnitOfMeasureDelete(TemplateView):
    http_method_names = ['post']

    @method_decorator(requires('productos.delete_unitofmeasure'))
    def dispatch(self, *args, **kwargs):
        return super(UnitOfMeasureDelete, self).dispatch(*args, **kwargs)

    def post(self, request, *args, **kwargs):
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            id = request.POST['id']
            unit_of_measure = UnitOfMeasure.objects.get(pk=id)
            unidad_medida_json = {}
            unidad_medida_json['unidad'] = unit_of_measure.unidad
            if len(unit_of_measure.products.all()) > 0:
                unidad_medida_json['productos'] = 'SI'
            else:
                unidad_medida_json['productos'] = 'NO'
                UnitOfMeasure.objects.filter(pk=id).update(is_active=False)
            data = simplejson.dumps(unidad_medida_json)
            return HttpResponse(data, 'application/json')


class ProductGroupDelete(TemplateView):
    http_method_names = ['post']

    @method_decorator(requires('productos.delete_productgroup'))
    def dispatch(self, *args, **kwargs):
        return super(ProductGroupDelete, self).dispatch(*args, **kwargs)

    def post(self, request, *args, **kwargs):
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            code = request.POST['code']
            product_group = ProductGroup.objects.get(pk=code)
            grupo_productos_json = {}
            grupo_productos_json['code'] = product_group.code
            grupo_productos_json['description'] = product_group.description
            if len(product_group.products.all()) > 0:
                grupo_productos_json['productos'] = 'SI'
            else:
                grupo_productos_json['productos'] = 'NO'
                ProductGroup.objects.filter(pk=code).update(is_active=False)
            data = simplejson.dumps(grupo_productos_json)
            return HttpResponse(data, 'application/json')


class ProductDelete(TemplateView):
    http_method_names = ['post']

    @method_decorator(requires('productos.delete_product'))
    def dispatch(self, *args, **kwargs):
        return super(ProductDelete, self).dispatch(*args, **kwargs)

    def post(self, request, *args, **kwargs):
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            code = request.POST['code']
            product = Product.objects.get(pk=code)
            producto_json = {}
            producto_json['code'] = product.code
            producto_json['description'] = product.description
            if len(product.details.all()) > 0:
                producto_json['relaciones'] = 'SI'
            elif len(product.details.all()) > 0:
                producto_json['relaciones'] = 'SI'
            else:
                producto_json['relaciones'] = 'NO'
                Product.objects.filter(pk=code).update(is_active=False)
            data = simplejson.dumps(producto_json)
            return HttpResponse(data, 'application/json')


class ServiceDelete(TemplateView):
    http_method_names = ['post']

    @method_decorator(requires('productos.delete_product'))
    def dispatch(self, *args, **kwargs):
        return super(ServiceDelete, self).dispatch(*args, **kwargs)

    def post(self, request, *args, **kwargs):
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            code = request.POST['code']
            servicio = Product.objects.get(code=code)
            servicio_json = {}
            servicio_json['code'] = code
            if len(servicio.service_order_details.all()) > 0:
                servicio_json['ordenes'] = 'SI'
            else:
                servicio_json['ordenes'] = 'NO'
                Product.objects.filter(code=code).update(is_active=False)
            data = simplejson.dumps(servicio_json)
            return HttpResponse(data, 'application/json')


class UnitOfMeasureList(ListView):
    model = UnitOfMeasure
    template_name = 'productos/unidades_medida.html'
    context_object_name = 'unidades'
    queryset = UnitOfMeasure.objects.filter(is_active=True).order_by('description')

    @method_decorator(
        requires('productos.ver_tabla_unidades_medida'))
    def dispatch(self, *args, **kwargs):
        return super(UnitOfMeasureList, self).dispatch(*args, **kwargs)


class ServiceList(ListView):
    model = Product
    template_name = 'productos/servicios.html'
    context_object_name = 'servicios'
    queryset = Product.objects.filter(is_active=True, is_service=True).order_by('description')

    @method_decorator(requires('productos.ver_tabla_productos'))
    def dispatch(self, *args, **kwargs):
        return super(ServiceList, self).dispatch(*args, **kwargs)


class ProductGroupList(ListView):
    model = ProductGroup
    template_name = 'productos/grupos_productos.html'
    context_object_name = 'grupos_productos'
    queryset = ProductGroup.objects.filter(is_active=True).order_by('code')

    @method_decorator(
        requires('productos.ver_tabla_grupos_productos'))
    def dispatch(self, *args, **kwargs):
        return super(ProductGroupList, self).dispatch(*args, **kwargs)


class ProductList(ListView):
    model = Product
    template_name = 'productos/productos.html'
    context_object_name = 'productos'
    queryset = Product.objects.filter(is_service=False, is_active=True).order_by('code')

    @method_decorator(requires('productos.ver_tabla_productos'))
    def dispatch(self, *args, **kwargs):
        return super(ProductList, self).dispatch(*args, **kwargs)


class ProductListByGroup(ListView):
    model = Product
    template_name = 'productos/productos.html'
    context_object_name = 'productos'

    @method_decorator(requires('productos.ver_tabla_productos'))
    def dispatch(self, *args, **kwargs):
        return super(ProductListByGroup, self).dispatch(*args, **kwargs)

    def get_queryset(self):
        grupo = ProductGroup.objects.get(pk=self.kwargs['grupo'])
        queryset = grupo.products.all()
        return queryset


class ProductUpdate(UpdateView):
    model = Product
    context_object_name = 'product'
    template_name = 'productos/producto.html'
    form_class = ProductForm

    @method_decorator(requires('productos.change_product'))
    def dispatch(self, *args, **kwargs):
        return super(ProductUpdate, self).dispatch(*args, **kwargs)

    def get_success_url(self):
        return reverse('productos:product_detail', args=[self.object.pk])


class UnitOfMeasureUpdate(UpdateView):
    model = UnitOfMeasure
    template_name = 'productos/unidad_medida.html'
    form_class = UnitOfMeasureForm

    @method_decorator(requires('productos.change_unitofmeasure'))
    def dispatch(self, *args, **kwargs):
        return super(UnitOfMeasureUpdate, self).dispatch(*args, **kwargs)

    def get_success_url(self):
        return reverse('productos:unit_of_measure_detail', args=[self.object.pk])


class ProductGroupUpdate(UpdateView):
    model = ProductGroup
    template_name = 'productos/grupo_productos.html'
    form_class = ProductGroupForm
    success_url = reverse_lazy('productos:product_group_list')

    @method_decorator(
        requires('productos.change_productgroup'))
    def dispatch(self, *args, **kwargs):
        return super(ProductGroupUpdate, self).dispatch(*args, **kwargs)

    def get_success_url(self):
        return reverse('productos:product_group_detail', args=[self.object.pk])


class ServiceUpdate(UpdateView):
    model = Product
    template_name = 'productos/servicio.html'
    form_class = ServiceForm

    @method_decorator(requires('productos.change_product'))
    def dispatch(self, *args, **kwargs):
        return super(ServiceUpdate, self).dispatch(*args, **kwargs)

    def get_success_url(self):
        return reverse('productos:service_detail', args=[self.object.pk])


class ProductExcelReport(TemplateView):

    def get(self, request, *args, **kwargs):
        productos = Product.objects.filter(is_active=True).order_by('code')
        wb = Workbook()
        ws = wb.active
        ws['B1'] = 'REPORTE DE PRODUCTOS'
        ws.merge_cells('B1:J1')
        ws['B3'] = 'CODIGO'
        ws['C3'] = 'DESCRIPCION'
        ws['D3'] = 'DESCR_ABREV'
        ws['E3'] = 'GRUPO'
        ws['F3'] = 'UNIDAD'
        ws['G3'] = 'MARCA'
        ws['H3'] = 'MODELO'
        ws['I3'] = 'PRECIO'
        ws['J3'] = 'CREADO'
        cont = 4
        for product in productos:
            ws.cell(row=cont, column=2).value = product.code
            ws.cell(row=cont, column=3).value = product.description
            ws.cell(row=cont, column=4).value = product.desc_abreviada
            ws.cell(row=cont, column=5).value = product.product_group.description
            ws.cell(row=cont, column=6).value = product.unit_of_measure.description
            ws.cell(row=cont, column=7).value = product.brand
            ws.cell(row=cont, column=8).value = product.model
            ws.cell(row=cont, column=9).value = product.price
            ws.cell(row=cont, column=9).number_format = '#.00000'
            ws.cell(row=cont, column=10).value = product.created
            ws.cell(row=cont, column=10).number_format = 'dd/mm/yyyy hh:mm:ss'
            cont = cont + 1
        nombre_archivo = "ProductList.xlsx"
        response = HttpResponse(content_type="application/ms-excel")
        contenido = "attachment; filename={0}".format(nombre_archivo)
        response["Content-Disposition"] = contenido
        wb.save(response)
        return response


class ProductGroupExcelReport(TemplateView):

    def get(self, request, *args, **kwargs):
        grupos_productos = ProductGroup.objects.filter(is_active=True).order_by('code')
        wb = Workbook()
        ws = wb.active
        ws['B1'] = 'REPORTE DE GRUPOS DE PRODUCTOS'
        ws.merge_cells('B1:J1')
        ws['B3'] = 'CODIGO'
        ws['C3'] = 'DESCRIPCION'
        ws['D3'] = 'CTA_CONTABLE'
        ws['E3'] = 'CREADO'
        cont = 4
        for product_group in grupos_productos:
            ws.cell(row=cont, column=2).value = product_group.code
            ws.cell(row=cont, column=3).value = product_group.description
            ws.cell(row=cont, column=4).value = product_group.account.account_number
            ws.cell(row=cont, column=5).value = product_group.created
            ws.cell(row=cont, column=5).number_format = 'dd/mm/yyyy hh:mm:ss'
            cont = cont + 1
        nombre_archivo = "ProductGroupList.xlsx"
        response = HttpResponse(content_type="application/ms-excel")
        contenido = "attachment; filename={0}".format(nombre_archivo)
        response["Content-Disposition"] = contenido
        wb.save(response)
        return response


class UnitOfMeasureExcelReport(TemplateView):

    def get(self, request, *args, **kwargs):
        unidades = UnitOfMeasure.objects.filter(is_active=True).order_by('code')
        wb = Workbook()
        ws = wb.active
        ws['B1'] = 'REPORTE DE UNIDADES DE MEDIDA'
        ws.merge_cells('B1:J1')
        ws['B3'] = 'UNIDAD'
        ws['C3'] = 'DESCRIPCIÓN'
        ws['D3'] = 'ESTADO'
        cont = 4
        for unidad in unidades:
            ws.cell(row=cont, column=2).value = unidad.code
            ws.cell(row=cont, column=3).value = unidad.description
            ws.cell(row=cont, column=4).value = unidad.is_active
            cont = cont + 1
        nombre_archivo = "UnidadesMedida.xlsx"
        response = HttpResponse(content_type="application/ms-excel")
        contenido = "attachment; filename={0}".format(nombre_archivo)
        response["Content-Disposition"] = contenido
        wb.save(response)
        return response


class ServiceExcelReport(TemplateView):

    def get(self, request, *args, **kwargs):
        servicios = Product.objects.filter(is_service=True, is_active=True).order_by('code')
        wb = Workbook()
        ws = wb.active
        ws['B1'] = 'REPORTE DE SERVICIOS'
        ws.merge_cells('B1:J1')
        ws['B3'] = 'CODIGO'
        ws['C3'] = 'DESCRIPCION'
        ws['D3'] = 'ESTADO'
        cont = 4
        for servicio in servicios:
            ws.cell(row=cont, column=2).value = servicio.code
            ws.cell(row=cont, column=3).value = servicio.description
            ws.cell(row=cont, column=4).value = servicio.is_active
            cont = cont + 1
        nombre_archivo = "ServiceList.xlsx"
        response = HttpResponse(content_type="application/ms-excel")
        contenido = "attachment; filename={0}".format(nombre_archivo)
        response["Content-Disposition"] = contenido
        wb.save(response)
        return response
