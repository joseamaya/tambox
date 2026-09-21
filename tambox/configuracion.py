from functools import lru_cache


@lru_cache(maxsize=1)
def configuracion():
    from contabilidad.models import Configuration
    return Configuration.objects.first()


@lru_cache(maxsize=1)
def empresa():
    from contabilidad.models import Company
    return Company.load()


def limpiar_cache():
    configuracion.cache_clear()
    empresa.cache_clear()


def _campo_configuracion(name):
    config = configuracion()
    return getattr(config, name) if config is not None else None


def oficina_administracion():
    return _campo_configuracion('administracion')


def presupuesto():
    return _campo_configuracion('presupuesto')


def logistica():
    return _campo_configuracion('logistica')


def operaciones():
    return _campo_configuracion('operaciones')


def purchase_tax():
    return _campo_configuracion('purchase_tax')
