from rest_framework import serializers
from ..models import Despacho, MovimientoDespacho, Localfarmacia, Motorista, Moto

class DespachoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Despacho
        fields = ('id','codigo_despacho','estado','tipo_despacho','prioridad','farmacia_origen_local_id','motorista','cliente_nombre','destino_direccion','tiene_receta_retenida','hubo_incidencia','fecha_registro')

class MovimientoDespachoSerializer(serializers.ModelSerializer):
    class Meta:
        model = MovimientoDespacho
        fields = ('id','despacho','estado_anterior','estado_nuevo','fecha_movimiento','observacion')

class LocalfarmaciaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Localfarmacia
        fields = ('id','local_id','local_nombre','local_direccion','comuna_nombre','local_telefono','funcionamiento_hora_apertura','funcionamiento_hora_cierre','funcionamiento_dia','local_lat','local_lng','activo')

class MotoristaSerializer(serializers.ModelSerializer):
    nombre = serializers.SerializerMethodField()
    class Meta:
        model = Motorista
        fields = ('id','nombre','licencia_numero','licencia_clase','emergencia_telefono','disponible_hoy','total_entregas_completadas','total_entregas_fallidas')
    def get_nombre(self, obj):
        return f"{getattr(obj.usuario,'nombre', '')} {getattr(obj.usuario,'apellido','')}".strip()

class MotoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Moto
        fields = ('id','patente','marca','modelo','anio','color','tipo_combustible','cilindrada_cc','estado','kilometraje_actual','propietario_nombre')
