import os
from rest_framework import serializers
from .models import Perfil, Vehiculo, Reserva, Documento


class PerfilSerializer(serializers.ModelSerializer):
    class Meta:
        model = Perfil
        fields = ['id', 'nombre', 'rol', 'estado_validacion', 'motivo_rechazo']


class VehiculoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Vehiculo
        fields = ['id', 'patente', 'modelo', 'capacidad', 'cupos_libres', 'maletero', 'en_linea']


class VehiculoPubSerializer(serializers.ModelSerializer):
    conductor = serializers.CharField(source='conductor.nombre', read_only=True)

    class Meta:
        model = Vehiculo
        fields = ['id', 'patente', 'modelo', 'cupos_libres', 'maletero', 'lat', 'lon', 'conductor']


class ReservaSerializer(serializers.ModelSerializer):
    patente = serializers.CharField(source='vehiculo.patente', read_only=True)
    modelo = serializers.CharField(source='vehiculo.modelo', read_only=True)
    conductor = serializers.CharField(source='vehiculo.conductor.nombre', read_only=True)

    class Meta:
        model = Reserva
        fields = ['id', 'estado', 'asientos', 'destino', 'patente', 'modelo', 'conductor', 'monto', 'pagada']

class DocumentoSerializer(serializers.ModelSerializer):
    nombre_archivo = serializers.SerializerMethodField()

    class Meta:
        model = Documento
        fields = ['id', 'tipo', 'nombre_archivo', 'subido_en']

    def get_nombre_archivo(self, obj):
        return os.path.basename(obj.archivo.name)