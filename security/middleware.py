"""Bloqueo de la aplicacion mientras la configuracion inicial esta incompleta.

Va despues de `AuthenticationMiddleware` y `LoginRequiredMiddleware`: los
anonimos ya fueron mandados al login, asi que aqui solo se actua sobre usuarios
autenticados. Las rutas permitidas son el login/logout, el wizard, el admin, el
cambio de contrasena y los estaticos.

Se puede desactivar con `SETUP_WIZARD_ENFORCED = False` (los tests lo usan).
"""
from django.conf import settings
from django.shortcuts import redirect
from django.urls import Resolver404, resolve

from tambox.setup import is_configured_cached

ALLOWED_URL_NAMES = {
    'security:login',
    'security:logout',
    'security:setup',
    'security:wizard_step',
    'security:password_change',
}

ALLOWED_PATH_PREFIXES = ('/static/', '/media/')


class SetupWizardMiddleware:

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if (getattr(settings, 'SETUP_WIZARD_ENFORCED', True)
                and request.user.is_authenticated
                and not self._is_allowed(request)
                and not is_configured_cached()):
            return redirect('security:setup')
        return self.get_response(request)

    @staticmethod
    def _is_allowed(request):
        path = request.path
        if path.startswith(ALLOWED_PATH_PREFIXES):
            return True
        try:
            match = resolve(path)
        except Resolver404:
            return False
        if match.namespace == 'admin':
            return True
        return match.view_name in ALLOWED_URL_NAMES
