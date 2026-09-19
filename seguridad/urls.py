from django.urls import re_path
from django.contrib.auth.views import LogoutView
from seguridad.views import Inicio, Login, ModificarPassword, PermisoDenegado
from django.views.decorators.http import require_POST

app_name = 'seguridad'

urlpatterns = [
    re_path(r'^$', Login.as_view(), name="login"),
    re_path(r'^inicio/$', Inicio.as_view(), name="inicio"),
    re_path(r'^permiso_denegado/$', PermisoDenegado.as_view(), name="permiso_denegado"),
    re_path(r'^cambiar_password$', ModificarPassword.as_view(), name="cambiar_password"),
    re_path(r'^salir$', require_POST(LogoutView.as_view(next_page='seguridad:login')), name="salir"),
]
