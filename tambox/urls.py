from django.conf.urls import include
from django.urls import re_path
from django.contrib import admin
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
                  re_path(r'^admin/', admin.site.urls),
                  re_path(r'^almacen/', include('almacen.urls', namespace='almacen')),
                  re_path(r'^', include('seguridad.urls', namespace='seguridad')),
                  re_path(r'^compras/', include('compras.urls', namespace='compras')),
                  re_path(r'^contabilidad/', include('contabilidad.urls', namespace='contabilidad')),
                  re_path(r'^administracion/', include('administracion.urls', namespace='administracion')),
                  re_path(r'^requerimientos/', include('requerimientos.urls', namespace='requerimientos')),
                  re_path(r'^productos/', include('productos.urls', namespace='productos'))
                  # url(r'^media/(?P<path>.*)$', 'django.views.static.serve', {'document_root': settings.MEDIA_ROOT})
              ] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

handler403 = 'seguridad.views.permiso_denegado'
