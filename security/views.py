from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.shortcuts import render
from django.urls import reverse, reverse_lazy
from django.http.response import HttpResponseRedirect
from django.contrib.auth import login
from django.contrib.auth.decorators import login_not_required
from security.forms import PasswordChangeForm, LoginForm
from django.views.generic import View
from django.views.generic.edit import FormView
from django.views.generic.base import TemplateView
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.cache import never_cache
from django.utils.decorators import method_decorator

from security.wizard import (STEPS, build_forms, first_pending_step, get_step,
                             save_forms)
from tambox.setup import clear_setup_cache, is_configured, seed_base_data

# Un usuario puede configurar el sistema si administra algun modulo o es staff.
SETUP_PERMISSIONS = (
    'administration.ver_bienvenida',
    'warehouse.ver_bienvenida',
    'purchases.ver_bienvenida',
    'accounting.ver_bienvenida',
    'requirements.ver_bienvenida',
)


def can_configure(user):
    return user.is_staff or any(user.has_perm(permission) for permission in SETUP_PERMISSIONS)


def wizard_context(request, step, forms, already_done=False):
    stepper = [
        {'key': s.key, 'title': s.title, 'section': s.section, 'done': s.done(),
         'optional': s.optional, 'current': s.key == step.key}
        for s in STEPS
    ]
    previous = None
    for s in STEPS:
        if s.key == step.key:
            break
        if s.done():
            previous = s
    required = [s for s in STEPS if not s.optional]
    total_count = len(required) + 1
    done_count = 1 + sum(1 for s in required if s.done())
    return {
        'step': step,
        'stepper': stepper,
        'forms': forms,
        'already_done': already_done,
        'prev_step': previous,
        'done_count': done_count,
        'total_count': total_count,
        'percent': round(done_count * 100 / total_count) if total_count else 0,
    }


class Home(View):

    def get(self, request, *args, **kwargs):
        if not is_configured():
            return HttpResponseRedirect(reverse('security:setup'))
        return render(request, 'security/welcome.html')


class Setup(View):
    """Entrada del wizard: crea los datos base y va al primer paso pendiente."""

    def get(self, request, *args, **kwargs):
        if not can_configure(request.user):
            return render(request, 'security/setup_blocked.html')
        seed_base_data()
        step = first_pending_step()
        if step is None:
            return HttpResponseRedirect(reverse('security:home'))
        return HttpResponseRedirect(reverse('security:wizard_step', args=[step.key]))


class WizardStepView(View):
    """Un paso del wizard: muestra sus formularios y los guarda."""

    def get(self, request, key):
        if not can_configure(request.user):
            return render(request, 'security/setup_blocked.html')
        step = get_step(key)
        if step is None:
            return HttpResponseRedirect(reverse('security:setup'))
        if step.done():
            return render(request, 'security/wizard.html',
                          wizard_context(request, step, [], already_done=True))
        return render(request, 'security/wizard.html',
                      wizard_context(request, step, build_forms(request, step)))

    def post(self, request, key):
        if not can_configure(request.user):
            raise PermissionDenied
        step = get_step(key)
        if step is None:
            return HttpResponseRedirect(reverse('security:setup'))
        entries = build_forms(request, step, data=request.POST, files=request.FILES)
        if not all(entry['form'].is_valid() for entry in entries):
            return render(request, 'security/wizard.html',
                          wizard_context(request, step, entries))
        save_forms(entries)
        clear_setup_cache()
        messages.success(request, 'Paso guardado.')
        return HttpResponseRedirect(reverse('security:setup'))


class Login(FormView):
    template_name = 'security/login.html'
    form_class = LoginForm
    success_url = reverse_lazy("security:home")

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
    template_name = 'security/change_password.html'
    form_class = PasswordChangeForm
    success_url = reverse_lazy("security:login")

    def get_form_kwargs(self):
        kwargs = super(PasswordUpdate, self).get_form_kwargs()
        kwargs['request'] = self.request
        return kwargs


class PermissionDeniedView(TemplateView):
    template_name = 'security/permission_denied.html'


def permission_denied(request, exception=None):
    """Handler 403 del proyecto.

    Renderiza la misma pagina que la vista PermissionDeniedView, pero con el estado
    HTTP correcto: cuando la denegacion era un redirect a esa vista, la respuesta
    final era un 200 y ni un monitor ni un test podian distinguirla de un exito.
    """
    return render(request, 'security/permission_denied.html', status=403)
