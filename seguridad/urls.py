from django.urls import path
from django.contrib.auth import views as auth_views
from seguridad.views import Inicio, Login, ModificarPassword, PermisoDenegado
from django.contrib.auth.decorators import login_required
from django.urls import reverse

app_name = 'seguridad'

urlpatterns = [
    path('', Login.as_view(), name="login"),
    path('inicio/', login_required(Inicio.as_view()), name="inicio"),
    path('permiso_denegado/', login_required(PermisoDenegado.as_view()), name="permiso_denegado"),
    path('cambiar_password/', login_required(ModificarPassword.as_view()), name="cambiar_password"),
    path('salir/', auth_views.LogoutView.as_view(next_page='seguridad:login'), name="salir"),
]
