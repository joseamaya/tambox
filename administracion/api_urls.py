from django.conf.urls import url, include
from rest_framework.routers import DefaultRouter
from administracion.api import AdministracionOficinaViewSet

#APIRouter
router=DefaultRouter()
router.register(r'oficinas',AdministracionOficinaViewSet)

urlpatterns = [
    #API URLs
    url(r'1.0/',include(router.urls)),
 ]