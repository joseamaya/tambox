from django import template
from django.urls import reverse
from tambox.config import administration_office, logistics, budget

register = template.Library()


@register.simple_tag
def previous_url(url, instancia, usuario):
    ant = instancia.previous()
    if ant.check_access(usuario, administration_office(), logistics(), budget()):
        url = reverse(url, args=[ant])
        return url
    else:
        return previous_url(url, ant, usuario)


@register.simple_tag
def next_url(url, instancia, usuario):
    sig = instancia.next()
    if sig.check_access(usuario, administration_office(), logistics(), budget()):
        url = reverse(url, args=[sig])
        return url
    else:
        return next_url(url, sig, usuario)
