from django.conf.urls import url
from django.contrib.auth.views import logout
from seguridad.views import Inicio, Login, ModificarPassword, PermisoDenegado
from django.contrib.auth.decorators import login_required
from django.core.urlresolvers import reverse

urlpatterns = [
    url(r'^$', Login.as_view(), name="login"),
    url(r'^inicio/$', login_required(Inicio.as_view()), name="inicio"),
    url(r'^permiso_denegado/$', login_required(PermisoDenegado.as_view()), name="permiso_denegado"),
    url(r'^cambiar_password$', login_required(ModificarPassword.as_view()), name="cambiar_password"),
    url(r'^salir$', logout, name="salir", kwargs={'next_page': 'seguridad:login'}),
]
