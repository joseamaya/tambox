from django.urls import re_path
from django.contrib.auth.views import LogoutView
from seguridad.views import Home, Login, PasswordUpdate, PermissionDeniedView
from django.views.decorators.http import require_POST

app_name = 'seguridad'

urlpatterns = [
    re_path(r'^$', Login.as_view(), name="login"),
    re_path(r'^home/$', Home.as_view(), name="home"),
    re_path(r'^permission_denied/$', PermissionDeniedView.as_view(), name="permission_denied"),
    re_path(r'^password_change$', PasswordUpdate.as_view(), name="password_change"),
    re_path(r'^logout$', require_POST(LogoutView.as_view(next_page='seguridad:login')), name="logout"),
]
