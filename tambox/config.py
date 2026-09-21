from functools import lru_cache


@lru_cache(maxsize=1)
def configuration():
    from contabilidad.models import Configuration
    return Configuration.objects.first()


@lru_cache(maxsize=1)
def company():
    from contabilidad.models import Company
    return Company.load()


def clear_cache():
    configuration.cache_clear()
    company.cache_clear()


def _config_field(name):
    config = configuration()
    return getattr(config, name) if config is not None else None


def administration_office():
    return _config_field('administration')


def budget():
    return _config_field('budget')


def logistics():
    return _config_field('logistics')


def operations():
    return _config_field('operations')


def purchase_tax():
    return _config_field('purchase_tax')
