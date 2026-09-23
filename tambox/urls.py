from django.conf.urls import include
from django.urls import re_path
from django.contrib import admin
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
                  re_path(r'^admin/', admin.site.urls),
                  re_path(r'^almacen/', include('warehouse.urls', namespace='warehouse')),
                  re_path(r'^', include('security.urls', namespace='security')),
                  re_path(r'^compras/', include('purchases.urls', namespace='purchases')),
                  re_path(r'^contabilidad/', include('accounting.urls', namespace='accounting')),
                  re_path(r'^administracion/', include('administration.urls', namespace='administration')),
                  re_path(r'^requerimientos/', include('requirements.urls', namespace='requirements')),
                  re_path(r'^productos/', include('products.urls', namespace='products'))
                  # url(r'^media/(?P<path>.*)$', 'django.views.static.serve', {'document_root': settings.MEDIA_ROOT})
              ] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

handler403 = 'security.views.permission_denied'
