from django import template
from django.core.urlresolvers import reverse
from contabilidad.models import Configuracion

register = template.Library()
try:
    configuracion = Configuracion.objects.first()
    oficina_administracion = configuracion.administracion
    presupuesto = configuracion.presupuesto
    logistica = configuracion.logistica
except:
    configuracion = None
    oficina_administracion = None
    presupuesto = None
    logistica = None

@register.simple_tag
def url_anterior(url, instancia, usuario):
    ant = instancia.anterior()
    if ant.verificar_acceso(usuario, oficina_administracion, logistica, presupuesto):
        url = reverse(url, args=[ant])
        return url        
    else:
        return url_anterior(url, ant, usuario)
    
@register.simple_tag
def url_siguiente(url, instancia, usuario):
    sig = instancia.siguiente()
    if sig.verificar_acceso(usuario, oficina_administracion, logistica, presupuesto):
        url = reverse(url, args=[sig])
        return url
    else:           
        return url_siguiente(url, sig, usuario)    