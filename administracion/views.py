# -*- coding: utf-8 -*-
import logging

from django.shortcuts import render
from administracion.forms import OficinaForm, TrabajadorForm, PuestoForm, ModificacionPuestoForm, \
    ProfesionForm, NivelAprobacionForm, ProductorForm
from almacen.models import MovementType
from contabilidad.forms import UploadForm
from tambox.vistas import CargarCsvMixin, SoloAjaxMixin
from django.urls import reverse_lazy
from django.views.generic.edit import FormView, UpdateView, CreateView
from django.views.generic.list import ListView
from administracion.models import Office, Worker, Position, Profession, \
    ApprovalLevel, Producer
from django.views.generic.base import View, TemplateView
from django.views.generic.detail import DetailView
from django.urls import reverse
from django.contrib.auth.models import User
from openpyxl import Workbook
from django.http import HttpResponse
import datetime
from seguridad.permisos import requiere
from django.utils.decorators import method_decorator
import simplejson
import json
from django.db.models import Q

logger = logging.getLogger(__name__)


class Tablero(View):

    def get(self, request, *args, **kwargs):
        lista_notificaciones = []
        cant_trabajadores = Worker.objects.all().count()
        cant_puestos = Position.objects.all().count()
        cant_profesiones = Profession.objects.all().count()
        office, creada = Office.objects.get_or_create(code='GGEN',
                                                       defaults={'name': 'GERENCIA GENERAL',
                                                                 'is_management': True})
        if creada:
            lista_notificaciones.append("Se ha creado la oficina de GERENCIA GENERAL")
        if cant_trabajadores == 0:
            lista_notificaciones.append("No se ha registrado ningún trabajador")
        if cant_puestos == 0:
            lista_notificaciones.append("No se ha registrado ningún puesto")
        if cant_profesiones == 0:
            lista_notificaciones.append("No se ha registrado ninguna profesión")
        nivel_logistica, creada = ApprovalLevel.objects.get_or_create(description="LOGISTICA")
        _, creado = ApprovalLevel.objects.get_or_create(description="USUARIO",
                                                         defaults={'superior_level': nivel_logistica})
        if creada or creado:
            lista_notificaciones.append("Se han creado los niveles de aprobación básicos")
        context = {'notificaciones': lista_notificaciones}
        return render(request, 'administracion/tablero_administracion.html', context)


class BusquedaReceptorDni(SoloAjaxMixin, TemplateView):

    parametros_requeridos = ('dni', 'movement_type')
    def get(self, request, *args, **kwargs):
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            dni = request.GET['dni']
            movement_type = MovementType.objects.get(pk=request.GET['movement_type'])
            if movement_type.is_sale:
                receptor = Producer.objects.get(dni=dni)
            else:
                receptor = Worker.objects.get(dni=dni)
            receptor_json = {}
            receptor_json['dni'] = receptor.dni
            receptor_json['nombre_completo'] = str(receptor.nombre_completo())
            data = simplejson.dumps(receptor_json)
            return HttpResponse(data, 'application/json')


class BusquedaReceptorNombre(SoloAjaxMixin, TemplateView):

    parametros_requeridos = ('name', 'movement_type')
    def get(self, request, *args, **kwargs):
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            name = request.GET['name']
            movement_type = MovementType.objects.get(pk=request.GET['movement_type'])
            if movement_type.is_sale:
                receptores = Producer.objects.filter(last_name__icontains=name)[:20]
            else:
                receptores = Worker.objects.filter(
                    Q(last_name__icontains=name) | Q(
                        first_name__icontains=name))[:20]
            lista_receptores = []
            for receptor in receptores:
                receptor_json = {}
                receptor_json['label'] = str(receptor.nombre_completo())
                receptor_json['dni'] = receptor.dni
                lista_receptores.append(receptor_json)
            data = json.dumps(lista_receptores)
            return HttpResponse(data, 'application/json')


class CargarOficinas(CargarCsvMixin, FormView):
    template_name = 'administracion/cargar_oficinas.html'
    form_class = UploadForm
    success_url = reverse_lazy('administracion:maestro_oficinas')

    def procesar_fila(self, fila):
        Office.objects.get_or_create(code=fila[0],
                                      defaults={
                                          'name': fila[1],
                                          'dependency': Office.objects.get(code=fila[2])},
                                      )


class CargarProductores(CargarCsvMixin, FormView):
    template_name = 'administracion/cargar_productores.html'
    form_class = UploadForm
    success_url = reverse_lazy('administracion:maestro_productores')

    def procesar_fila(self, fila):
        dni = fila[0]
        if dni != "":
            try:
                Producer.objects.get_or_create(dni=dni,
                                                defaults={'last_name': (fila[1] + ' ' + fila[2]).upper(),
                                                          'first_name': fila[3].upper()})
            except Exception:
                logger.warning("No se pudo importar el productor con DNI %s", dni, exc_info=True)


class CargarTrabajadores(CargarCsvMixin, FormView):
    template_name = 'administracion/cargar_trabajadores.html'
    form_class = UploadForm
    success_url = reverse_lazy('administracion:maestro_trabajadores')

    def procesar_fila(self, fila):
        usuario_hoja = fila[0]
        if usuario_hoja != "":
            usuario, creado = User.objects.get_or_create(username=usuario_hoja,
                                                         defaults={'email': fila[5]}, )
            if creado:
                usuario.set_unusable_password()
                usuario.save()
                Worker.objects.get_or_create(user=usuario,
                                                 defaults={'dni': fila[1].strip(),
                                                           'last_name': (fila[2] + ' ' + fila[3]).strip(),
                                                           'first_name': fila[4]})
        else:
            Worker.objects.get_or_create(dni=fila[1].strip(),
                                             defaults={'last_name': (fila[2] + ' ' + fila[3]).strip(),
                                                       'first_name': fila[4]})


class CargarPuestos(CargarCsvMixin, FormView):
    template_name = 'administracion/cargar_puestos.html'
    form_class = UploadForm
    success_url = reverse_lazy('administracion:maestro_puestos')

    def procesar_fila(self, fila):
        date = datetime.date(int(fila[3][6:]), int(fila[3][3:5]), int(fila[3][0:2]))
        try:
            Position.objects.get_or_create(name=fila[0],
                                         defaults={'office': Office.objects.get(code=fila[1].strip()),
                                                   'worker': Worker.objects.get(dni=fila[2].strip()),
                                                   'start_date': date,
                                                   'is_leadership': fila[4] == 'SI'})
        except Exception:
            logger.warning("No se pudo importar el puesto %s", fila[0], exc_info=True)


class CrearNivelAprobacion(CreateView):
    template_name = 'administracion/nivel_aprobacion.html'
    form_class = NivelAprobacionForm

    @method_decorator(
        requiere('administracion.add_approvallevel'))
    def dispatch(self, *args, **kwargs):
        return super(CrearNivelAprobacion, self).dispatch(*args, **kwargs)

    def get_success_url(self):
        return reverse('administracion:detalle_nivel_aprobacion', args=[self.object.pk])


class CrearProfesion(CreateView):
    template_name = 'administracion/profesion.html'
    form_class = ProfesionForm

    @method_decorator(requiere('administracion.add_profession'))
    def dispatch(self, *args, **kwargs):
        return super(CrearProfesion, self).dispatch(*args, **kwargs)

    def get_success_url(self):
        return reverse('administracion:detalle_profesion', args=[self.object.pk])


class CrearOficina(CreateView):
    template_name = 'administracion/oficina.html'
    form_class = OficinaForm

    @method_decorator(requiere('administracion.add_office'))
    def dispatch(self, *args, **kwargs):
        return super(CrearOficina, self).dispatch(*args, **kwargs)

    def get_success_url(self):
        return reverse('administracion:maestro_oficinas')


class CrearTrabajador(CreateView):
    template_name = 'administracion/trabajador.html'
    form_class = TrabajadorForm

    @method_decorator(requiere('administracion.add_worker'))
    def dispatch(self, *args, **kwargs):
        return super(CrearTrabajador, self).dispatch(*args, **kwargs)

    def get_success_url(self):
        return reverse('administracion:detalle_trabajador', args=[self.object.pk])


class CrearProductor(CreateView):
    template_name = 'administracion/productor.html'
    form_class = ProductorForm

    @method_decorator(requiere('administracion.add_producer'))
    def dispatch(self, *args, **kwargs):
        return super(CrearProductor, self).dispatch(*args, **kwargs)

    def get_success_url(self):
        return reverse('administracion:detalle_productor', args=[self.object.pk])


class CrearPuesto(CreateView):
    template_name = 'administracion/puesto.html'
    form_class = PuestoForm

    @method_decorator(requiere('administracion.add_position'))
    def dispatch(self, *args, **kwargs):
        return super(CrearPuesto, self).dispatch(*args, **kwargs)

    def get_success_url(self):
        return reverse('administracion:detalle_puesto', args=[self.object.pk])


class DetalleOficina(DetailView):
    model = Office
    template_name = 'administracion/detalle_oficina.html'


class DetalleTrabajador(DetailView):
    model = Worker
    template_name = 'administracion/detalle_trabajador.html'


class DetalleProductor(DetailView):
    model = Producer
    template_name = 'administracion/detalle_productor.html'


class DetallePuesto(DetailView):
    model = Position
    template_name = 'administracion/detalle_puesto.html'


class DetalleProfesion(DetailView):
    model = Profession
    template_name = 'administracion/detalle_profesion.html'


class DetalleNivelAprobacion(DetailView):
    model = ApprovalLevel
    template_name = 'administracion/detalle_nivel_aprobacion.html'


class ListadoOficinas(ListView):
    model = Office
    template_name = 'administracion/oficinas.html'
    context_object_name = 'oficinas'
    queryset = Office.objects.all().order_by('name')


class ListadoTrabajadores(ListView):
    model = Worker
    template_name = 'administracion/trabajadores.html'
    context_object_name = 'trabajadores'


class ListadoProductores(ListView):
    model = Producer
    template_name = 'administracion/productores.html'
    context_object_name = 'productores'


class ListadoPuestos(ListView):
    model = Position
    template_name = 'administracion/puestos.html'
    context_object_name = 'puestos'
    queryset = Position.objects.filter(is_active=True)


class ListadoProfesiones(ListView):
    model = Profession
    template_name = 'administracion/profesiones.html'
    context_object_name = 'profesiones'


class ListadoNivelesAprobacion(ListView):
    model = ApprovalLevel
    template_name = 'administracion/niveles_aprobacion.html'
    context_object_name = 'niveles'


class ModificarNivelAprobacion(UpdateView):
    model = ApprovalLevel
    template_name = 'administracion/nivel_aprobacion.html'
    form_class = NivelAprobacionForm

    @method_decorator(
        requiere('administracion.change_approvallevel'))
    def dispatch(self, *args, **kwargs):
        return super(ModificarNivelAprobacion, self).dispatch(*args, **kwargs)

    def get_success_url(self):
        return reverse('administracion:detalle_nivel_aprobacion', args=[self.object.pk])


class ModificarProfesion(UpdateView):
    model = Profession
    template_name = 'administracion/profesion.html'
    form_class = ProfesionForm

    @method_decorator(
        requiere('administracion.change_profession'))
    def dispatch(self, *args, **kwargs):
        return super(ModificarProfesion, self).dispatch(*args, **kwargs)

    def get_success_url(self):
        return reverse('administracion:detalle_profesion', args=[self.object.pk])


class ModificarOficina(UpdateView):
    model = Office
    template_name = 'administracion/oficina.html'
    form_class = OficinaForm
    success_url = reverse_lazy('administracion:maestro_oficinas')

    @method_decorator(requiere('administracion.change_office'))
    def dispatch(self, *args, **kwargs):
        return super(ModificarOficina, self).dispatch(*args, **kwargs)


class ModificarTrabajador(UpdateView):
    model = Worker
    template_name = 'administracion/trabajador.html'
    form_class = TrabajadorForm

    @method_decorator(
        requiere('administracion.change_worker'))
    def dispatch(self, *args, **kwargs):
        return super(ModificarTrabajador, self).dispatch(*args, **kwargs)

    def get_success_url(self):
        return reverse('administracion:detalle_trabajador', args=[self.object.pk])


class ModificarProductor(UpdateView):
    model = Producer
    template_name = 'administracion/productor.html'
    form_class = ProductorForm

    @method_decorator(
        requiere('administracion.change_producer'))
    def dispatch(self, *args, **kwargs):
        return super(ModificarProductor, self).dispatch(*args, **kwargs)

    def get_success_url(self):
        return reverse('administracion:detalle_productor', args=[self.object.pk])


class ModificarPuesto(UpdateView):
    model = Position
    template_name = 'administracion/puesto.html'
    form_class = ModificacionPuestoForm

    @method_decorator(requiere('administracion.change_position'))
    def dispatch(self, *args, **kwargs):
        return super(ModificarPuesto, self).dispatch(*args, **kwargs)

    def get_initial(self):
        initial = super(ModificarPuesto, self).get_initial()
        initial['start_date'] = self.object.start_date.strftime('%d/%m/%Y')
        if self.object.end_date is not None:
            initial['end_date'] = self.object.end_date.strftime('%d/%m/%Y')
        return initial

    def get_success_url(self):
        return reverse('administracion:detalle_puesto', args=[self.object.pk])


class ReporteExcelOficinas(TemplateView):
    def get(self, request, *args, **kwargs):
        oficinas = Office.objects.filter(is_active=True).order_by('code')
        wb = Workbook()
        ws = wb.active
        ws['B1'] = 'REPORTE DE OFICINAS'
        ws.merge_cells('B1:J1')
        ws['B3'] = 'CODIGO'
        ws['C3'] = 'NOMBRE'
        ws['D3'] = 'DEPENDENCIA'
        ws['E3'] = 'GERENCIA'
        cont = 4
        for office in oficinas:
            try:
                ws.cell(row=cont, column=2).value = office.code
                ws.cell(row=cont, column=3).value = office.name
                ws.cell(row=cont, column=4).value = office.dependency.name
                ws.cell(row=cont, column=5).value = office.gerencia.name
                cont = cont + 1
            except Exception:
                logger.warning("No se pudo exportar la oficina %s", office.pk, exc_info=True)
        nombre_archivo = "Oficinas.xlsx"
        response = HttpResponse(content_type="application/ms-excel")
        contenido = "attachment; filename={0}".format(nombre_archivo)
        response["Content-Disposition"] = contenido
        wb.save(response)
        return response


class ReporteExcelProfesiones(TemplateView):
    def get(self, request, *args, **kwargs):
        profesiones = Profession.objects.filter(is_active=True)
        wb = Workbook()
        ws = wb.active
        ws['B1'] = 'REPORTE DE PROFESIONES'
        ws.merge_cells('B1:J1')
        ws['B3'] = 'ABREVIATURA'
        ws['C3'] = 'DESCRIPCION'
        ws['D3'] = 'ESTADO'
        cont = 4
        for profession in profesiones:
            ws.cell(row=cont, column=2).value = profession.abbreviation
            ws.cell(row=cont, column=3).value = profession.description
            ws.cell(row=cont, column=4).value = profession.is_active
            cont = cont + 1
        nombre_archivo = "Profesiones.xlsx"
        response = HttpResponse(content_type="application/ms-excel")
        contenido = "attachment; filename={0}".format(nombre_archivo)
        response["Content-Disposition"] = contenido
        wb.save(response)
        return response


class ReporteExcelPuestos(TemplateView):
    def get(self, request, *args, **kwargs):
        puestos = Position.objects.filter(is_active=True)
        wb = Workbook()
        ws = wb.active
        ws['B1'] = 'REPORTE DE PUESTOS'
        ws.merge_cells('B1:J1')
        ws['B3'] = 'NOMBRE'
        ws['C3'] = 'OFICINA'
        ws['D3'] = 'TRABAJADOR'
        ws['E3'] = 'FECHA INICIO'
        ws['F3'] = 'FECHA FIN'
        ws['G3'] = 'ES JEFATURA'
        ws['H3'] = 'ESTADO'
        cont = 4
        for puesto in puestos:
            ws.cell(row=cont, column=2).value = puesto.name
            ws.cell(row=cont, column=3).value = puesto.office.name
            ws.cell(row=cont, column=4).value = puesto.worker.nombre_completo()
            ws.cell(row=cont, column=5).value = puesto.start_date.strftime('%d/%m/%Y')
            ws.cell(row=cont, column=6).value = puesto.end_date
            if puesto.is_leadership:
                ws.cell(row=cont, column=7).value = "SI"
            else:
                ws.cell(row=cont, column=7).value = "NO"
            ws.cell(row=cont, column=8).value = puesto.is_active
            cont = cont + 1
        nombre_archivo = "Puestos.xlsx"
        response = HttpResponse(content_type="application/ms-excel")
        contenido = "attachment; filename={0}".format(nombre_archivo)
        response["Content-Disposition"] = contenido
        wb.save(response)
        return response


class ReporteExcelTrabajadores(TemplateView):
    def get(self, request, *args, **kwargs):
        trabajadores = Worker.objects.filter(is_active=True)
        wb = Workbook()
        ws = wb.active
        ws['B1'] = 'REPORTE DE TRABAJADORES'
        ws.merge_cells('B1:I1')
        ws['B3'] = 'USUARIO'
        ws['C3'] = 'DNI'
        ws['D3'] = 'APELLIDOS'
        ws['E3'] = 'NOMBRES'
        ws['F3'] = 'EMAIL'
        ws['G3'] = 'ESTADO'
        cont = 4
        for worker in trabajadores:
            ws.cell(row=cont, column=2).value = worker.user.username
            ws.cell(row=cont, column=3).value = worker.dni
            ws.cell(row=cont, column=4).value = worker.last_name
            ws.cell(row=cont, column=5).value = worker.first_name
            ws.cell(row=cont, column=6).value = worker.user.email
            ws.cell(row=cont, column=7).value = worker.is_active
            cont = cont + 1
        nombre_archivo = "Trabajadores.xlsx"
        response = HttpResponse(content_type="application/ms-excel")
        contenido = "attachment; filename={0}".format(nombre_archivo)
        response["Content-Disposition"] = contenido
        wb.save(response)
        return response
