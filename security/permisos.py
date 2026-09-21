"""Punto unico de los permisos de vista.

Django no expone que permiso pide una vista ya decorada (`permission_required`
solo deja `login_url` y `redirect_field_name` en el envoltorio), asi que no hay
forma de auditarlos: un cambio de nombre mal escrito deniega a todo el mundo en
silencio. Este envoltorio anota cada permiso en un registro y el test de
auditoria lo contrasta contra los permisos reales de la base de datos.

Tampoco fija `login_url` a proposito. Ese atributo no significa "a donde mando
al que no tiene permiso", significa "a donde mando al que no esta logueado", y
`LoginRequiredMiddleware` lo lee antes que `settings.LOGIN_URL`. Si aqui se
apuntara a la pagina de denegado, un anonimo que tocara una de estas vistas
acabaria viendo "permiso denegado" en vez del formulario de login. Los dos casos
quedan asi separados:

- anonimo -> lo intercepta el middleware y va al login;
- autenticado sin permiso -> PermissionDenied, que el handler403 renderiza con
  la misma pagina que antes.
"""

from django.contrib.auth.decorators import permission_required

_registro = set()


def requires(permiso):
    """`permission_required` que responde 403 y anota el permiso para auditar."""
    _registro.add(permiso)
    return permission_required(permiso, raise_exception=True)


def declared_permissions():
    """Los permisos que piden las vistas, en orden. Se llena al importarlas."""
    return sorted(_registro)
