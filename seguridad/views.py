from django.shortcuts import render
from django.urls import reverse_lazy
from django.http.response import HttpResponseRedirect
from django.contrib.auth import login
from django.contrib.auth.decorators import login_not_required
from seguridad.forms import PasswordChangeForm, LoginForm
from django.views.generic import View
from django.views.generic.edit import FormView
from django.views.generic.base import TemplateView
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.cache import never_cache
from django.utils.decorators import method_decorator


class Home(View):

    def get(self, request, *args, **kwargs):
        return render(request, 'seguridad/welcome.html')


class Login(FormView):
    template_name = 'seguridad/login.html'
    form_class = LoginForm
    success_url = reverse_lazy("seguridad:home")

    @method_decorator(csrf_protect)
    @method_decorator(never_cache)
    @method_decorator(login_not_required)
    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return HttpResponseRedirect(self.get_success_url())
        else:
            return super(Login, self).dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        login(self.request, form.get_user())
        return super(Login, self).form_valid(form)


class PasswordUpdate(FormView):
    template_name = 'seguridad/change_password.html'
    form_class = PasswordChangeForm
    success_url = reverse_lazy("seguridad:login")

    def get_form_kwargs(self):
        kwargs = super(PasswordUpdate, self).get_form_kwargs()
        kwargs['request'] = self.request
        return kwargs


class PermissionDeniedView(TemplateView):
    template_name = 'seguridad/permission_denied.html'


def permission_denied(request, exception=None):
    """Handler 403 del proyecto.

    Renderiza la misma pagina que la vista PermissionDeniedView, pero con el estado
    HTTP correcto: cuando la denegacion era un redirect a esa vista, la respuesta
    final era un 200 y ni un monitor ni un test podian distinguirla de un exito.
    """
    return render(request, 'seguridad/permission_denied.html', status=403)
