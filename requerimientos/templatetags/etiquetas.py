from django import template
from django.core.urlresolvers import reverse
from contabilidad.models import Configuracion
from requerimientos.settings import OFICINA_ADMINISTRACION, LOGISTICA, PRESUPUESTO

register = template.Library()


@register.simple_tag
def url_anterior(url, instancia, usuario):
    ant = instancia.anterior()
    if ant.verificar_acceso(usuario, OFICINA_ADMINISTRACION, LOGISTICA, PRESUPUESTO):
        url = reverse(url, args=[ant])
        return url
    else:
        return url_anterior(url, ant, usuario)


@register.simple_tag
def url_siguiente(url, instancia, usuario):
    sig = instancia.siguiente()
    if sig.verificar_acceso(usuario, OFICINA_ADMINISTRACION, LOGISTICA, PRESUPUESTO):
        url = reverse(url, args=[sig])
        return url
    else:
        return url_siguiente(url, sig, usuario)
