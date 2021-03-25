from django.shortcuts import render
from django.core.urlresolvers import reverse, reverse_lazy
from django.http.response import HttpResponseRedirect
from django.contrib.auth import login
from seguridad.forms import FormularioCambioPassword, FormularioLogin
from django.views.generic import View
from django.views.generic.edit import FormView
from django.views.generic.base import TemplateView
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.cache import never_cache
from django.utils.decorators import method_decorator


class Inicio(View):

    def get(self, request, *args, **kwargs):
        return render(request, 'seguridad/bienvenida.html')


class Login(FormView):
    template_name = 'seguridad/login.html'
    form_class = FormularioLogin
    success_url = reverse_lazy("seguridad:inicio")

    @method_decorator(csrf_protect)
    @method_decorator(never_cache)
    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated():
            return HttpResponseRedirect(self.get_success_url())
        else:
            return super(Login, self).dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        login(self.request, form.get_user())
        return super(Login, self).form_valid(form)


class ModificarPassword(FormView):
    template_name = 'seguridad/cambiar_password.html'
    form_class = FormularioCambioPassword
    success_url = reverse_lazy("seguridad:login")

    def get_form_kwargs(self):
        kwargs = super(ModificarPassword, self).get_form_kwargs()
        kwargs['request'] = self.request
        return kwargs


class PermisoDenegado(TemplateView):
    template_name = 'seguridad/permiso_denegado.html'
