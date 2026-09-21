from django import template
from django.urls import reverse
from tambox.config import administration_office, logistics, budget

register = template.Library()


@register.simple_tag
def previous_url(url, instance, user):
    previous = instance.previous()
    if previous.check_access(user, administration_office(), logistics(), budget()):
        url = reverse(url, args=[previous])
        return url
    else:
        return previous_url(url, previous, user)


@register.simple_tag
def next_url(url, instance, user):
    sig = instance.next()
    if sig.check_access(user, administration_office(), logistics(), budget()):
        url = reverse(url, args=[sig])
        return url
    else:
        return next_url(url, sig, user)
