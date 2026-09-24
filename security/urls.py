from django.urls import re_path
from django.contrib.auth.views import LogoutView
from security.views import Home, Login, PasswordUpdate, PermissionDeniedView, Setup, WizardStepView
from django.views.decorators.http import require_POST

app_name = 'security'

urlpatterns = [
    re_path(r'^$', Login.as_view(), name="login"),
    re_path(r'^home/$', Home.as_view(), name="home"),
    re_path(r'^configuracion/$', Setup.as_view(), name="setup"),
    re_path(r'^configuracion/(?P<key>[\w-]+)/$', WizardStepView.as_view(), name="wizard_step"),
    re_path(r'^permission_denied/$', PermissionDeniedView.as_view(), name="permission_denied"),
    re_path(r'^password_change$', PasswordUpdate.as_view(), name="password_change"),
    re_path(r'^logout$', require_POST(LogoutView.as_view(next_page='security:login')), name="logout"),
]
