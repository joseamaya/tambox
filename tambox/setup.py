"""Comprobacion y creacion de los datos minimos para operar.

El sistema necesita unos registros base (oficina, niveles de aprobacion, tipo de
documento, tipos de movimiento y unidad de medida) mas contabilidad (cuenta,
grupo de productos, tipo de existencia, impuesto y configuracion), empresa,
trabajador con puesto, almacen y catalogo. La pantalla de configuracion inicial
(wizard) lee estos predicados para saber que falta y crea los datos base con
`seed_base_data()`.

`checklist()` no crea nada: solo consulta.
"""
from dataclasses import dataclass

from django.core.cache import cache

BASE_MOVEMENTS = (
    ('I00', {'description': 'INVENTARIO INICIAL', 'sunat_code': '16',
             'increases': True, 'is_active': True}),
    ('I01', {'description': 'INGRESO POR COMPRA', 'sunat_code': '02',
             'increases': True, 'requires_reference': True, 'is_active': True}),
    ('S01', {'description': 'SALIDA POR PEDIDO', 'sunat_code': '10',
             'increases': False, 'requires_reference': True, 'is_active': True}),
)

SETUP_CACHE_KEY = 'tambox:setup:configured'


@dataclass
class SetupStep:
    key: str
    label: str
    done: bool
    required: bool = True


def seed_base_data():
    """Crea de forma idempotente los datos base. Devuelve las etiquetas creadas."""
    from administration.models import Office, ApprovalLevel
    from accounting.models import DocumentType
    from warehouse.models import MovementType
    from products.models import UnitOfMeasure

    created = []

    _, was_created = Office.objects.get_or_create(
        code='GGEN', defaults={'name': 'GERENCIA GENERAL', 'is_management': True})
    if was_created:
        created.append('Oficina GERENCIA GENERAL')

    logistics, was_created = ApprovalLevel.objects.get_or_create(description='LOGISTICA')
    if was_created:
        created.append('Nivel de aprobación LOGISTICA')

    _, was_created = ApprovalLevel.objects.get_or_create(
        description='USUARIO', defaults={'superior_level': logistics})
    if was_created:
        created.append('Nivel de aprobación USUARIO')

    _, was_created = DocumentType.objects.get_or_create(
        sunat_code='PEC', defaults={'description': 'PECOSA', 'name': 'PECOSA'})
    if was_created:
        created.append('Tipo de documento PEC')

    for code, defaults in BASE_MOVEMENTS:
        _, was_created = MovementType.objects.get_or_create(code=code, defaults=defaults)
        if was_created:
            created.append('Tipo de movimiento %s' % code)

    _, was_created = UnitOfMeasure.objects.get_or_create(
        code='SERV', defaults={'description': 'SERVICIO'})
    if was_created:
        created.append('Unidad de medida SERV')

    clear_setup_cache()
    return created


# --------------------------------------------------------------------------- #
# Predicados de "ya esta listo" (no crean nada)
# --------------------------------------------------------------------------- #

def base_done():
    from administration.models import Office, ApprovalLevel
    from accounting.models import DocumentType
    from warehouse.models import MovementType
    from products.models import UnitOfMeasure

    codes = [code for code, _ in BASE_MOVEMENTS]
    return (Office.objects.filter(code='GGEN').exists()
            and ApprovalLevel.objects.filter(description='LOGISTICA').exists()
            and ApprovalLevel.objects.filter(description='USUARIO').exists()
            and DocumentType.objects.filter(sunat_code='PEC').exists()
            and MovementType.objects.filter(code__in=codes).count() == len(codes)
            and UnitOfMeasure.objects.filter(code='SERV').exists())


def account_done():
    from accounting.models import Account
    return Account.objects.exists()


def group_done():
    from products.models import ProductGroup
    return ProductGroup.objects.exists()


def stock_type_done():
    from accounting.models import StockType
    return StockType.objects.exists()


def tax_done():
    from accounting.models import Tax
    return Tax.objects.exists()


def configuration_done():
    from accounting.models import Configuration
    return Configuration.objects.exists()


def company_done():
    from accounting.models import Company
    company = Company.objects.filter(pk=1).first()
    return bool(company and company.business_name and company.tax_id)


def worker_done():
    from administration.models import Worker
    return Worker.objects.exists()


def position_done():
    from administration.models import Position
    return Position.objects.exists()


def warehouse_done():
    from warehouse.models import Warehouse
    return Warehouse.objects.exists()


def product_done():
    from products.models import Product
    return Product.objects.exists()


def supplier_done():
    from purchases.models import Supplier
    return Supplier.objects.exists()


def checklist():
    """Pasos de configuracion con su estado. No crea ni modifica nada."""
    return [
        SetupStep('base', 'Datos base del sistema', base_done()),
        SetupStep('account', 'Cuenta contable', account_done()),
        SetupStep('group', 'Grupo de productos', group_done()),
        SetupStep('stock_type', 'Tipo de existencia', stock_type_done()),
        SetupStep('tax', 'Impuesto', tax_done()),
        SetupStep('configuration', 'Configuración contable', configuration_done()),
        SetupStep('company', 'Empresa', company_done()),
        SetupStep('worker', 'Trabajador', worker_done()),
        SetupStep('position', 'Puesto', position_done()),
        SetupStep('warehouse', 'Almacén', warehouse_done()),
        SetupStep('product', 'Producto o servicio', product_done()),
        SetupStep('supplier', 'Proveedor', supplier_done(), required=False),
    ]


def is_configured():
    return all(step.done for step in checklist() if step.required)


def is_configured_cached():
    """Igual que `is_configured`, cacheado para el middleware.

    Se invalida al guardar un paso del wizard y al crear los datos base.
    """
    value = cache.get(SETUP_CACHE_KEY)
    if value is None:
        value = is_configured()
        cache.set(SETUP_CACHE_KEY, value, 60)
    return value


def clear_setup_cache():
    cache.delete(SETUP_CACHE_KEY)


def summary():
    """Devuelve `(configurado, etiquetas_pendientes)` con una sola consulta."""
    steps = checklist()
    configured = all(step.done for step in steps if step.required)
    pending = [step.label for step in steps if not step.done]
    return configured, pending
