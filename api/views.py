from rest_framework import generics, filters
from rest_framework.permissions import IsAuthenticated
from ..models import Despacho, MovimientoDespacho, Localfarmacia, Motorista, Moto
from .serializers import DespachoSerializer, MovimientoDespachoSerializer, LocalfarmaciaSerializer, MotoristaSerializer, MotoSerializer

class DespachoList(generics.ListAPIView):
    queryset = Despacho.objects.all().order_by('-fecha_registro')
    serializer_class = DespachoSerializer
    filter_backends = [filters.SearchFilter]
    search_fields = ['codigo_despacho','cliente_nombre','farmacia_origen_local_id']
    permission_classes = [IsAuthenticated]

class MovimientoList(generics.ListAPIView):
    queryset = MovimientoDespacho.objects.select_related('despacho').order_by('-fecha_movimiento')
    serializer_class = MovimientoDespachoSerializer
    filter_backends = [filters.SearchFilter]
    search_fields = ['despacho__codigo_despacho','estado_nuevo','observacion']
    permission_classes = [IsAuthenticated]

class FarmaciaList(generics.ListAPIView):
    queryset = Localfarmacia.objects.all().order_by('local_nombre')
    serializer_class = LocalfarmaciaSerializer
    filter_backends = [filters.SearchFilter]
    search_fields = ['local_nombre','local_direccion','comuna_nombre']
    permission_classes = [IsAuthenticated]

class MotoristaList(generics.ListAPIView):
    queryset = Motorista.objects.select_related('usuario').all().order_by('usuario__nombre')
    serializer_class = MotoristaSerializer
    filter_backends = [filters.SearchFilter]
    search_fields = ['usuario__nombre','usuario__apellido','licencia_numero']
    permission_classes = [IsAuthenticated]

class MotoList(generics.ListAPIView):
    queryset = Moto.objects.all().order_by('patente')
    serializer_class = MotoSerializer
    filter_backends = [filters.SearchFilter]
    search_fields = ['patente','marca','modelo']
    permission_classes = [IsAuthenticated]
