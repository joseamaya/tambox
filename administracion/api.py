from rest_framework.filters import SearchFilter, OrderingFilter
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from rest_framework.viewsets import ModelViewSet
from administracion.models import Oficina
from administracion.serializers import AdministracionOficinaSerializer


class AdministracionOficinaViewSet(ModelViewSet):
    queryset = Oficina.objects.all()
    permission_classes = (IsAuthenticatedOrReadOnly,)
    serializer_class = AdministracionOficinaSerializer

    filter_backends = (SearchFilter,OrderingFilter)
    search_fields=('codigo','nombre')
    ordering_fields=('codigo','nombre')
