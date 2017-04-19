from django.conf.urls import include, url
from django.contrib import admin
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
                  url(r'^admin/', include(admin.site.urls)),
                      url(r'^almacen/', include('almacen.urls', namespace='almacen')),
                  url(r'^', include('seguridad.urls', namespace='seguridad')),
                  url(r'^compras/', include('compras.urls', namespace='compras')),
                  url(r'^contabilidad/', include('contabilidad.urls', namespace='contabilidad')),
                  url(r'^administracion/', include('administracion.urls', namespace='administracion')),
                  url(r'^requerimientos/', include('requerimientos.urls', namespace='requerimientos')),
                  url(r'^productos/', include('productos.urls', namespace='productos'))
                  # url(r'^media/(?P<path>.*)$', 'django.views.static.serve', {'document_root': settings.MEDIA_ROOT})
              ] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
