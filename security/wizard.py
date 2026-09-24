"""Wizard de configuracion inicial.

Define los pasos, sus formularios y el orden. Cada paso puede tener uno o varios
formularios; los pasos con formularios dependientes (grupo de productos necesita
cuenta contable, puesto necesita trabajador) ocultan el campo de la dependencia y
lo asignan al objeto creado en el mismo paso.

La vista vive en `security.views`; aqui solo esta el modelo del wizard.
"""
from dataclasses import dataclass
from datetime import date

from django import forms

from accounting.forms import (AccountForm, CompanyForm, ConfigurationForm,
                              StockTypeForm, TaxForm)
from administration.forms import PositionForm, WorkerForm
from products.forms import ProductForm, ProductGroupForm
from purchases.forms import SupplierForm
from warehouse.forms import WarehouseForm

from tambox import setup


class WizardProductForm(ProductForm):
    """Producto o servicio en un solo formulario."""

    is_service = forms.BooleanField(label='Es un servicio', required=False)

    def save(self, commit=True):
        product = super().save(commit=False)
        product.is_service = self.cleaned_data.get('is_service', False)
        if commit:
            product.save()
        return product


@dataclass
class FormSpec:
    prefix: str
    form_class: type
    done: object = None       # callable -> bool
    instance: object = None   # callable -> instancia a editar (o None)
    initial: object = None    # callable(request) -> dict
    auto_fk: str = ''         # campo FK a rellenar con otro formulario del paso
    auto_from: str = ''       # prefijo del formulario que lo crea


@dataclass
class WizardStep:
    key: str
    title: str
    section: str
    done: object
    forms: tuple = ()
    intro: str = ''
    optional: bool = False


# --------------------------------------------------------------------------- #
# Iniciales
# --------------------------------------------------------------------------- #

def _tax_initial(request):
    return {'abbreviation': 'IGV', 'description': 'IMPUESTO GENERAL A LAS VENTAS',
            'amount': 18, 'start_date': date.today()}


def _configuration_instance():
    from accounting.models import Configuration
    return Configuration.objects.first()


def _configuration_initial(request):
    from accounting.models import Configuration, Tax
    from administration.models import Office

    if Configuration.objects.exists():
        return {}
    ggen = Office.objects.filter(code='GGEN').first()
    tax = Tax.objects.order_by('pk').first()
    return {'purchase_tax': tax, 'operations': ggen, 'administration': ggen,
            'budget': ggen, 'logistics': ggen}


def _company_instance():
    from accounting.models import Company
    return Company.objects.filter(pk=1).first()


def _worker_initial(request):
    return {'user': request.user}


def _position_initial(request):
    from administration.models import Office
    return {'office': Office.objects.filter(code='GGEN').first()}


def _product_initial(request):
    from accounting.models import StockType
    from products.models import ProductGroup, UnitOfMeasure

    return {'product_group': ProductGroup.objects.first(),
            'unit_of_measure': UnitOfMeasure.objects.filter(code='SERV').first(),
            'stock_type': StockType.objects.first()}


# --------------------------------------------------------------------------- #
# Pasos
# --------------------------------------------------------------------------- #

STEPS = (
    WizardStep(
        'catalog', 'Cuenta contable y grupo de productos', 'Contabilidad',
        lambda: setup.account_done() and setup.group_done(),
        intro='La cuenta contable clasifica el grupo de productos.',
        forms=(
            FormSpec('account', AccountForm, done=setup.account_done),
            FormSpec('group', ProductGroupForm, done=setup.group_done,
                     auto_fk='account', auto_from='account'),
        ),
    ),
    WizardStep(
        'stock', 'Tipo de existencia', 'Contabilidad', setup.stock_type_done,
        intro='Clasifica los productos para el control de existencias.',
        forms=(FormSpec('stock', StockTypeForm),),
    ),
    WizardStep(
        'tax', 'Impuesto', 'Contabilidad', setup.tax_done,
        intro='Impuesto que se aplica en las compras.',
        forms=(FormSpec('tax', TaxForm, initial=_tax_initial),),
    ),
    WizardStep(
        'configuration', 'Configuración contable', 'Contabilidad',
        setup.configuration_done,
        intro='Impuesto de compras y oficinas del flujo documentario.',
        forms=(FormSpec('configuration', ConfigurationForm,
                        instance=_configuration_instance,
                        initial=_configuration_initial),),
    ),
    WizardStep(
        'company', 'Empresa', 'Organización', setup.company_done,
        intro='Datos que aparecen en los documentos y reportes.',
        forms=(FormSpec('company', CompanyForm, instance=_company_instance),),
    ),
    WizardStep(
        'staff', 'Trabajador y puesto', 'Organización',
        lambda: setup.worker_done() and setup.position_done(),
        intro='El trabajador con su puesto podrá registrar y aprobar requerimientos.',
        forms=(
            FormSpec('worker', WorkerForm, done=setup.worker_done,
                     initial=_worker_initial),
            FormSpec('position', PositionForm, done=setup.position_done,
                     initial=_position_initial,
                     auto_fk='worker', auto_from='worker'),
        ),
    ),
    WizardStep(
        'warehouse', 'Almacén', 'Almacén y catálogo', setup.warehouse_done,
        intro='Donde se registran los ingresos y las salidas.',
        forms=(FormSpec('warehouse', WarehouseForm),),
    ),
    WizardStep(
        'product', 'Producto o servicio', 'Almacén y catálogo',
        setup.product_done,
        intro='Primer ítem del catálogo que se pide, compra y mueve.',
        forms=(FormSpec('product', WizardProductForm, initial=_product_initial),),
    ),
    WizardStep(
        'supplier', 'Proveedor', 'Almacén y catálogo', setup.supplier_done,
        intro='Opcional: necesario para emitir órdenes de compra.',
        optional=True,
        forms=(FormSpec('supplier', SupplierForm),),
    ),
)


def get_step(key):
    for step in STEPS:
        if step.key == key:
            return step
    return None


def first_pending_step():
    """Primer paso obligatorio pendiente; `None` si ya no queda ninguno.

    Los pasos opcionales (proveedor) no bloquean: se ofrecen en el indice pero
    no impiden terminar.
    """
    for step in STEPS:
        if not step.optional and not step.done():
            return step
    return None


def build_forms(request, step, data=None, files=None):
    """Instancia los formularios pendientes del paso.

    Los sub-formularios ya completados se omiten. Si una dependencia se esta
    creando en este mismo paso, se oculta su campo FK para asignarla al guardar.
    """
    pending = [spec for spec in step.forms if not (spec.done and spec.done())]
    pending_prefixes = {spec.prefix for spec in pending}
    entries = []
    for spec in pending:
        kwargs = {'prefix': spec.prefix}
        if data is not None:
            kwargs['data'] = data
            kwargs['files'] = files
        elif spec.initial:
            kwargs['initial'] = spec.initial(request)
        if spec.instance:
            instance = spec.instance()
            if instance is not None:
                kwargs['instance'] = instance
        form = spec.form_class(**kwargs)
        if spec.auto_fk and spec.auto_from in pending_prefixes:
            form.fields.pop(spec.auto_fk, None)
        entries.append({'spec': spec, 'form': form})
    return entries


def save_forms(entries):
    """Guarda los formularios validos, resolviendo las dependencias del paso."""
    saved = {}
    for entry in entries:
        spec, form = entry['spec'], entry['form']
        instance = form.save(commit=False)
        if spec.auto_fk and spec.auto_from in saved:
            setattr(instance, spec.auto_fk, saved[spec.auto_from])
        instance.save()
        form.save_m2m()
        saved[spec.prefix] = instance
    return saved
