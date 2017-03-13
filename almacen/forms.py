# -*- coding: utf-8 -*-
from django import forms

from administracion.models import Productor, Trabajador
from almacen.models import Almacen, TipoMovimiento, Movimiento, Pedido
from contabilidad.models import Tipo, Upload
import datetime
from compras.models import OrdenCompra
from django.forms import formsets
from django.core.exceptions import ValidationError
from almacen.settings import MESES, PARAMETROS, FORMATOS,\
    CHOICES_TIPOS_MOVIMIENTO, CHOICES_ALMACENES, CHOICES_MESES, CHOICES_ANNIOS,\
    CHOICES_CONSOLIDADO, SELECCION

class FormularioCargarAlmacenes(forms.Form):
    docfile = forms.FileField()

class TipoMovimientoForm(forms.ModelForm):
    
    class Meta:
        model = TipoMovimiento
        fields =['descripcion','codigo_sunat','incrementa','pide_referencia','es_compra','es_venta']
        
    def __init__(self, *args, **kwargs):
        self.aestado= True
        super(TipoMovimientoForm, self).__init__(*args, **kwargs)
        self.fields['descripcion'].widget.attrs.update({'class': 'form-control'})
        self.fields['codigo_sunat'].widget.attrs.update({'class': 'form-control'})

    def save(self, *args, **kwargs):
        self.instance.aestado= self.aestado
        return super(TipoMovimientoForm, self).save(*args, **kwargs)

class TipoSalidaForm(forms.ModelForm):

    class Meta:
        model = Tipo
        fields =['codigo','descripcion_valor']

    def __init__(self, *args, **kwargs):
        self.tabla = "tipo_Salida"
        self.descripcion_campo = "tipo_Salida"
        super(TipoSalidaForm, self).__init__(*args, **kwargs)

    def save(self, *args, **kwargs):
        self.instance.tabla = self.tabla
        self.instance.descripcion_campo = self.descripcion_campo
        super(TipoSalidaForm, self).save(*args, **kwargs)

class TipoStockForm(forms.ModelForm):

    class Meta:
        model = Tipo
        fields =['codigo','descripcion_valor']

    def __init__(self, *args, **kwargs):
        self.tabla = "tipo_stock"
        self.descripcion_campo = "tipo_stock"
        super(TipoStockForm, self).__init__(*args, **kwargs)
        for field in iter(self.fields):
            self.fields[field].widget.attrs.update({
                'class': 'form-control'
        })

    def save(self, *args, **kwargs):
        self.instance.tabla = self.tabla
        self.instance.descripcion_campo = self.descripcion_campo
        super(TipoStockForm, self).save(*args, **kwargs)  

class AlmacenForm(forms.ModelForm):

    class Meta:
        model = Almacen
        fields =['codigo','descripcion']
    
    def __init__(self, *args, **kwargs):
        super(AlmacenForm, self).__init__(*args, **kwargs)
        for field in iter(self.fields):
            self.fields[field].widget.attrs.update({
                'class': 'form-control'
        })

class FormularioDetalleMovimiento(forms.Form):
    almacen = forms.CharField(widget=forms.HiddenInput())
    codigo = forms.CharField(14, widget= forms.TextInput(attrs={'size': 17, 'class': 'entero form-control'}))    
    nombre = forms.CharField(100, widget= forms.TextInput(attrs={'size': 35, 'class': 'form-control'}))
    unidad = forms.CharField(6, widget= forms.TextInput(attrs={'size': 6,'readonly':"readonly", 'class': 'form-control'}))
    cantidad = forms.IntegerField(6, widget= forms.TextInput(attrs={'size': 6, 'class': 'form-control decimal'}))
    precio = forms.IntegerField(7, widget= forms.TextInput(attrs={'size': 7, 'readonly':"readonly", 'class': 'form-control decimal'}))
    valor = forms.IntegerField(10, widget= forms.TextInput(attrs={'size': 10, 'readonly':"readonly", 'class': 'form-control decimal'}))
    
class FormularioReporteMovimientos(forms.Form):
    tipo_busqueda = forms.ChoiceField(widget=forms.RadioSelect(attrs={'class': 'radiobutton'}),label='Seleccione:', choices=PARAMETROS)
    fecha_inicio = forms.CharField(10, widget= forms.TextInput(attrs={'size': 10, 'class': 'form-control'}),label='Fecha de Inicio:',required=False)
    fecha_fin = forms.CharField(10, widget= forms.TextInput(attrs={'size': 10, 'class': 'form-control'}),label='Fecha de Fin:',required=False)
    mes = forms.ChoiceField(choices=MESES, widget=forms.Select(attrs={'class': 'form-control'}),required=False)
    annio = forms.CharField(4, widget= forms.TextInput(attrs={'size': 4, 'class': 'form-control'}),label='Año',required=False)
    tipos_movimiento =  forms.ChoiceField(choices=CHOICES_TIPOS_MOVIMIENTO, widget=forms.Select(attrs={'class': 'form-control'}))
    almacenes =  forms.ChoiceField(choices=CHOICES_ALMACENES, widget=forms.Select(attrs={'class': 'form-control'}))
    
class MovimientoForm(forms.ModelForm):
    fecha = forms.CharField(100, widget= forms.TextInput(attrs={'size': 100, 'class': 'form-control'}))
    hora = forms.CharField(100, widget= forms.TextInput(attrs={'size': 100, 'class': 'form-control'}))
    doc_referencia = forms.CharField(100, widget= forms.TextInput(attrs={'size': 100,'readonly':"readonly", 'class': 'form-control'}))
    dni_receptor = forms.CharField(8, widget=forms.TextInput(attrs={'size': 100, 'readonly': "readonly", 'class': 'form-control'}))
    receptor = forms.CharField(150, widget=forms.TextInput(attrs={'size': 100, 'readonly': "readonly", 'class': 'form-control'}))
    cdetalles = forms.CharField(widget=forms.HiddenInput(),initial=0)
    total = forms.DecimalField(max_digits=25,decimal_places=8, widget= forms.TextInput(attrs={'size': 10,'readonly':"readonly", 'class': 'form-control'}))
    
    def __init__(self, *args, **kwargs):
        self.tipo_movimiento = kwargs.pop("tipo_movimiento")
        super(MovimientoForm, self).__init__(*args, **kwargs)
        self.fields['id_movimiento'].required = False
        self.fields['tipo_documento'].required = False
        self.fields['serie'].required = False
        self.fields['numero'].required = False
        self.fields['observaciones'].required = False
        self.fields['oficina'].required = False
        self.fields['dni_receptor'].required = False
        self.fields['receptor'].required = False
        self.fields['doc_referencia'].required = False
        if self.tipo_movimiento == 'I':
            self.fields['tipo_movimiento'].queryset = TipoMovimiento.objects.filter(incrementa=True)
        elif self.tipo_movimiento == 'S':
            self.fields['tipo_movimiento'].queryset = TipoMovimiento.objects.filter(incrementa=False)
        for field in iter(self.fields):             
            self.fields[field].widget.attrs.update({
                'class': 'form-control'
            })            

    def clean_dni_receptor(self):
        dni_receptor = self.cleaned_data.get('dni_receptor')
        if dni_receptor != "":
            if self.cleaned_data['tipo_movimiento'].es_venta:
                try:
                    Productor.objects.get(dni=self.cleaned_data['dni_receptor'])
                except Productor.DoesNotExist:
                    raise ValidationError("El DNI no corresponde a ningun productor")
            else:
                try:
                    Trabajador.objects.get(dni=self.cleaned_data['dni_receptor'])
                except Trabajador.DoesNotExist:
                    raise ValidationError("El DNI no correspone a ningun trabajador")
        return self.cleaned_data['dni_receptor']

    def obtener_fecha_hora(self,r_fecha,r_hora):
        r_hora = r_hora.replace(" ","")
        anio = int(r_fecha[6:])
        mes = int(r_fecha[3:5])
        dia = int(r_fecha[0:2])
        horas = int(r_hora[0:2])
        minutos = int(r_hora[3:5])
        segundos = int(r_hora[6:8])
        fecha = datetime.datetime(anio,mes,dia,horas,minutos,segundos)
        return fecha
                
    def save(self, *args, **kwargs):
        if self.tipo_movimiento=='I':
            try:
                self.instance.referencia = OrdenCompra.objects.get(pk=self.cleaned_data['doc_referencia'])
            except:
                self.instance.referencia = None
        print self.cleaned_data['tipo_movimiento']
        if self.cleaned_data['tipo_movimiento'].es_venta:
            try:
                self.instance.productor = Productor.objects.get(dni=self.cleaned_data['dni_receptor'])
            except:
                self.instance.productor = None
        else:
            try:
                self.instance.trabajador = Trabajador.objects.get(dni=self.cleaned_data['dni_receptor'])
            except:
                self.instance.trabajador = None
        self.instance.fecha_operacion = self.obtener_fecha_hora(self.cleaned_data['fecha'],self.cleaned_data['hora'])
        return super(MovimientoForm, self).save(*args, **kwargs)
    
    class Meta:
        model = Movimiento
        fields =['id_movimiento','tipo_movimiento','tipo_documento','serie','numero','almacen','oficina','observaciones']
    
class FormularioKardexProducto(forms.Form):
    almacenes = forms.ModelChoiceField(queryset=Almacen.objects.all(),widget=forms.Select(attrs={'class': 'form-control'}))
    consolidado = forms.ChoiceField(choices=CHOICES_CONSOLIDADO, widget=forms.RadioSelect,required=False)
    desde = forms.DateTimeField(input_formats = ['%d/%m/%Y'], widget= forms.TextInput(attrs={'size': 100, 'class': 'form-control'}))
    hasta = forms.DateTimeField(input_formats = ['%d/%m/%Y'], widget= forms.TextInput(attrs={'size': 100, 'class': 'form-control'}))
    cod_producto = forms.CharField(widget= forms.TextInput(attrs={'size': 100, 'class': 'form-control'}),required=False)
    desc_producto = forms.CharField(widget= forms.TextInput(attrs={'size': 100, 'class': 'form-control'}),required=False) 
    formatos = forms.ChoiceField(choices=FORMATOS, widget=forms.RadioSelect,required=False)

    def clean_hasta(self):
        self.cleaned_data['hasta'] = self.cleaned_data.get('hasta') + datetime.timedelta(days=1)
        return self.cleaned_data['hasta']
    
class FormularioMovimientosProducto(forms.Form):
    almacen = forms.ModelChoiceField(queryset=Almacen.objects.all(),widget=forms.Select(attrs={'class': 'form-control'}))
    desde = forms.DateTimeField(input_formats = ['%d/%m/%Y'], widget= forms.TextInput(attrs={'size': 100, 'class': 'form-control'}))
    hasta = forms.DateTimeField(input_formats = ['%d/%m/%Y'], widget= forms.TextInput(attrs={'size': 100, 'class': 'form-control'}))
    producto = forms.CharField(widget= forms.TextInput(attrs={'size': 100, 'class': 'form-control'}))
    descripcion = forms.CharField(widget= forms.TextInput(attrs={'size': 100, 'class': 'form-control'}))

    def clean_hasta(self):
        self.cleaned_data['hasta'] = self.cleaned_data.get('hasta') + datetime.timedelta(days=1)
        return self.cleaned_data['hasta']
    
class FormularioReprocesoPrecio(forms.Form):
    almacen = forms.ModelChoiceField(queryset=Almacen.objects.all(),widget=forms.Select(attrs={'class': 'form-control'}))
    desde = forms.DateTimeField(input_formats = ['%d/%m/%Y'], widget= forms.TextInput(attrs={'size': 100, 'class': 'form-control'}))
    producto = forms.CharField(widget= forms.TextInput(attrs={'size': 100, 'class': 'form-control'}),required=False)
    descripcion = forms.CharField(widget= forms.TextInput(attrs={'size': 100, 'class': 'form-control'}),required=False)
    seleccion = forms.ChoiceField(choices=SELECCION, widget=forms.RadioSelect)
    
class CargarInventarioInicialForm(forms.ModelForm):
    almacenes = forms.ModelChoiceField(queryset=Almacen.objects.all(),widget=forms.Select(attrs={'class': 'form-control'}))
    fecha = forms.CharField(100, widget= forms.TextInput(attrs={'size': 100, 'class': 'form-control'}))
    hora = forms.CharField(widget= forms.TextInput(attrs={'class': 'form-control','type':'time'}))
    
    class Meta:
        model = Upload
        fields =['archivo']
        
    def __init__(self, *args, **kwargs):
        super(CargarInventarioInicialForm, self).__init__(*args, **kwargs)
        for field in iter(self.fields):
            self.fields[field].widget.attrs.update({
                'class': 'form-control'
        })
            
class PedidoForm(forms.ModelForm):
    
    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop("request")
        super(PedidoForm, self).__init__(*args, **kwargs)
        self.fields['codigo'].required = False
        self.fields['observaciones'].required = False
        self.fields['fecha'].input_formats = ['%d/%m/%Y']
        for field in iter(self.fields):             
            self.fields[field].widget.attrs.update({
                'class': 'form-control'
            })
            if field=='total':
                self.fields[field].widget.attrs.update({
                    'readonly':"readonly"
                })
                
    def save(self, *args, **kwargs):
        self.instance.solicitante = self.request.user.trabajador
        puestos = self.request.user.trabajador.puesto_set.all().filter(estado=True)
        self.instance.oficina= puestos[0].oficina
        return super(PedidoForm, self).save(*args, **kwargs)
    
    class Meta:
        model = Pedido
        fields =['codigo','fecha','observaciones']
        
class AprobacionPedidoForm(forms.ModelForm):
    cod_pedido = forms.CharField(widget= forms.TextInput(attrs={'size': 100,'class': 'entero form-control'}))
    fecha = forms.CharField(100, widget= forms.TextInput(attrs={'size': 100, 'class': 'form-control'}))
    hora = forms.CharField(100, widget= forms.TextInput(attrs={'size': 100, 'class': 'form-control'}))
    total = forms.DecimalField(max_digits=15,decimal_places=5, widget= forms.TextInput(attrs={'size': 10,
                                                                                              'readonly':"readonly", 
                                                                                              'class': 'form-control'}))
    
    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop("request")
        super(AprobacionPedidoForm, self).__init__(*args, **kwargs)
        self.fields['observaciones'].required = False
        self.fields['fecha'].input_formats = ['%d/%m/%Y']
        for field in iter(self.fields):             
            self.fields[field].widget.attrs.update({
                'class': 'form-control'
            })    
            
    def obtener_fecha_hora(self,r_fecha,r_hora):
        r_hora = r_hora.replace(" ","")
        anio = int(r_fecha[6:])
        mes = int(r_fecha[3:5])
        dia = int(r_fecha[0:2])
        horas = int(r_hora[0:2])
        minutos = int(r_hora[3:5])
        segundos = int(r_hora[6:8])
        fecha = datetime.datetime(anio,mes,dia,horas,minutos,segundos)
        return fecha
                
    def save(self, *args, **kwargs):
        self.instance.pedido = Pedido.objects.get(codigo=self.cleaned_data['cod_pedido'])
        self.instance.fecha_operacion = self.obtener_fecha_hora(self.cleaned_data['fecha'],self.cleaned_data['hora'])
        self.instance.tipo_movimiento = TipoMovimiento.objects.get(codigo="S01")
        self.instance.oficina = self.instance.pedido.oficina
        return super(AprobacionPedidoForm, self).save(*args, **kwargs)
    
    class Meta:
        model = Movimiento
        fields =['almacen','observaciones']    

class FormularioPedido(forms.Form):
    cod_pedido = forms.CharField(100, widget= forms.TextInput(attrs={'size': 100, 'class': 'form-control'}))
    almacenes = forms.ModelChoiceField(queryset=Almacen.objects.all(),widget=forms.Select(attrs={'class': 'form-control'}))
    fecha = forms.CharField(100, widget= forms.TextInput(attrs={'size': 100, 'class': 'form-control'}))
    observaciones = forms.CharField(widget=forms.Textarea(attrs={'cols': 141, 'rows': 5}))
    total = forms.CharField(100, widget= forms.TextInput(attrs={'size': 100,'readonly':"readonly", 'class': 'form-control'}))
    
class FormularioDetallePedido(forms.Form):
    codigo = forms.CharField(14, widget= forms.TextInput(attrs={'size': 17, 'readonly':"readonly", 'class': 'entero form-control'}))    
    nombre = forms.CharField(100, widget= forms.TextInput(attrs={'size': 35, 'class': 'form-control productos'}))
    unidad = forms.CharField(20, widget= forms.TextInput(attrs={'size': 6,'readonly':"readonly", 'class': 'form-control'}))
    cantidad = forms.DecimalField(max_digits=15,decimal_places=5, widget= forms.TextInput(attrs={'size': 6, 'class': 'cantidad decimal form-control'}))
    
class FormularioReporteStock(forms.Form):
    almacenes = forms.ModelChoiceField(queryset=Almacen.objects.all(),widget=forms.Select(attrs={'class': 'form-control'}))
    
class FormularioDetalleIngreso(forms.Form):
    orden_compra = forms.CharField(widget=forms.HiddenInput())
    codigo = forms.CharField(widget= forms.TextInput(attrs={'size': 8, 'readonly':"readonly", 'class': 'entero form-control'}))    
    nombre = forms.CharField(widget= forms.TextInput(attrs={'size': 35, 'class': 'productos form-control'}))
    unidad = forms.CharField(widget= forms.TextInput(attrs={'size': 5,'readonly':"readonly", 'class': 'form-control'}))
    cantidad = forms.DecimalField(max_digits=25,decimal_places=8, widget= forms.TextInput(attrs={'size': 6, 'class': 'cantidad decimal form-control'}))
    precio = forms.DecimalField(max_digits=25,decimal_places=8, widget= forms.TextInput(attrs={'size': 7, 'class': 'precio decimal form-control'}))
    valor = forms.DecimalField(max_digits=25,decimal_places=8, widget= forms.TextInput(attrs={'size': 10,'readonly':"readonly", 'class': 'form-control'}))
    
class BaseDetalleIngresoFormSet(formsets.BaseFormSet):
    
    def clean(self):
        for form in self.forms:
            if form.cleaned_data:
                pass
            else:
                raise forms.ValidationError(
                        'Registro de datos incompletos.',
                        code='datos_incompletos'
                    )
                
class FormularioDetalleSalida(forms.Form):
    pedido = forms.CharField(widget=forms.HiddenInput(), required=False)
    codigo = forms.CharField(widget= forms.TextInput(attrs={'size': 8, 'readonly':"readonly", 'class': 'entero form-control'}))    
    nombre = forms.CharField(widget= forms.TextInput(attrs={'size': 35, 'class': 'productos form-control'}))
    unidad = forms.CharField(widget= forms.TextInput(attrs={'size': 5,'readonly':"readonly", 'class': 'form-control'}))
    cantidad = forms.DecimalField(max_digits=25,decimal_places=8, widget= forms.TextInput(attrs={'size': 6, 'class': 'cantidad decimal form-control'}))
    precio = forms.DecimalField(max_digits=25,decimal_places=8, widget= forms.TextInput(attrs={'size': 7,'readonly':"readonly", 'class': 'precio decimal form-control'}))
    valor = forms.DecimalField(max_digits=25,decimal_places=8, widget= forms.TextInput(attrs={'size': 10,'readonly':"readonly", 'class': 'form-control'}))
    
    def clean_cantidad(self):
        if self.cleaned_data.get('cantidad') == 0:
            raise ValidationError("La cantidad no puede ser 0")
        elif self.cleaned_data.get('cantidad') < 0:
            raise ValidationError("La cantidad no puede ser negativa")
        return self.cleaned_data['cantidad']
    
class BaseDetalleSalidaFormSet(formsets.BaseFormSet):
    
    def __init__(self, *args, **kwargs):
        super(BaseDetalleSalidaFormSet, self).__init__(*args, **kwargs)
        for form in self.forms:
            form.empty_permitted = False
    
    def clean(self):
        for form in self.forms:
            if form.cleaned_data:
                pass
            else:
                raise forms.ValidationError(
                        'Registro de datos incompletos.',
                        code='datos_incompletos'
                    )
                
class BaseDetallePedidoFormSet(formsets.BaseFormSet):
    
    def clean(self):
        for form in self.forms:
            if form.cleaned_data:
                pass
            else:
                raise forms.ValidationError(
                        'Registro de datos incompletos.',
                        code='datos_incompletos'
                    )
                
DetalleIngresoFormSet = formsets.formset_factory(FormularioDetalleIngreso, BaseDetalleIngresoFormSet,0)
DetalleSalidaFormSet = formsets.formset_factory(FormularioDetalleSalida, BaseDetalleSalidaFormSet,0)
DetallePedidoFormSet = formsets.formset_factory(FormularioDetallePedido, BaseDetallePedidoFormSet,0)