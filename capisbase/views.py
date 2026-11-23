import uuid
from django.contrib.auth.models import User
from django.db import transaction
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from .models import Perfil, Vehiculo, Documento, Reserva, Pago, AlertaSOS
from .serializers import PerfilSerializer, VehiculoSerializer, VehiculoPubSerializer, ReservaSerializer, DocumentoSerializer


@api_view(['POST'])
@permission_classes([AllowAny])
def registro(request):
    nombre = request.data.get('nombre', '').strip()
    email = request.data.get('email', '').strip().lower()
    password = request.data.get('password', '')
    rol = request.data.get('rol', 'PASAJERO').upper()

    if not nombre or not email or len(password) < 10:
        return Response({'detail': 'Datos inválidos o clave menor a 10 caracteres'}, status=status.HTTP_400_BAD_REQUEST)

    if User.objects.filter(username=email).exists():
        return Response({'detail': 'El correo ya está registrado'}, status=status.HTTP_409_CONFLICT)

    user = User.objects.create_user(username=email, email=email, password=password)
    estado = 'PENDIENTE' if rol == 'CONDUCTOR' else None
    Perfil.objects.create(user=user, nombre=nombre, rol=rol, estado_validacion=estado)
    return Response(status=status.HTTP_201_CREATED)


@api_view(['GET'])
def yo(request):
    perfil = get_object_or_404(Perfil, user=request.user)
    return Response(PerfilSerializer(perfil).data)


@api_view(['GET', 'PUT'])
def conductor_vehiculo(request):
    perfil = get_object_or_404(Perfil, user=request.user)
    if perfil.rol != 'CONDUCTOR':
        return Response({'detail': 'Solo conductores'}, status=status.HTTP_403_FORBIDDEN)

    if request.method == 'GET':
        vehiculo = Vehiculo.objects.filter(conductor=perfil).first()
        if not vehiculo:
            return Response({
                'id': 0, 'patente': None, 'modelo': None, 'capacidad': None,
                'cupos_libres': 0, 'maletero': False, 'en_linea': False
            })
        return Response(VehiculoSerializer(vehiculo).data)

    patente = request.data.get('patente', '').strip().upper()
    modelo = request.data.get('modelo', '').strip()
    capacidad = int(request.data.get('capacidad', 4))

    vehiculo, _ = Vehiculo.objects.update_or_create(
        conductor=perfil,
        defaults={'patente': patente, 'modelo': modelo, 'capacidad': capacidad}
    )
    return Response(VehiculoSerializer(vehiculo).data)



@api_view(['GET', 'POST'])
def subir_documento(request):
    perfil = get_object_or_404(Perfil, user=request.user)
    if perfil.rol != 'CONDUCTOR':
        return Response({'detail': 'Solo conductores'}, status=status.HTTP_403_FORBIDDEN)

    if request.method == 'GET':
        docs = Documento.objects.filter(conductor=perfil).order_by('-subido_en')
        return Response(DocumentoSerializer(docs, many=True).data)

    tipo = request.data.get('tipo', 'DOCUMENTO')
    archivo = request.FILES.get('archivo')
    if not archivo:
        return Response({'detail': 'Falta archivo'}, status=status.HTTP_400_BAD_REQUEST)

    doc = Documento.objects.create(conductor=perfil, tipo=tipo, archivo=archivo)
    return Response(DocumentoSerializer(doc).data, status=status.HTTP_201_CREATED)


@api_view(['PATCH'])
def conductor_estado(request):
    perfil = get_object_or_404(Perfil, user=request.user)
    if perfil.rol != 'CONDUCTOR' or perfil.estado_validacion != 'VALIDADO':
        return Response({'detail': 'Conductor no validado'}, status=status.HTTP_403_FORBIDDEN)

    vehiculo = get_object_or_404(Vehiculo, conductor=perfil)

    if 'en_linea' in request.data and request.data['en_linea'] is not None:
        vehiculo.en_linea = bool(request.data['en_linea'])
    if 'cupos_libres' in request.data and request.data['cupos_libres'] is not None:
        cupos = int(request.data['cupos_libres'])
        vehiculo.cupos_libres = max(0, min(cupos, vehiculo.capacidad))
    if 'maletero' in request.data and request.data['maletero'] is not None:
        vehiculo.maletero = bool(request.data['maletero'])
    if 'lat' in request.data and request.data['lat'] is not None:
        vehiculo.lat = float(request.data['lat'])
    if 'lon' in request.data and request.data['lon'] is not None:
        vehiculo.lon = float(request.data['lon'])

    vehiculo.save()
    return Response({
        'en_linea': vehiculo.en_linea,
        'cupos_libres': vehiculo.cupos_libres,
        'maletero': vehiculo.maletero,
        'lat': vehiculo.lat,
        'lon': vehiculo.lon,
    })


@api_view(['GET'])
def conductor_reservas(request):
    perfil = get_object_or_404(Perfil, user=request.user)
    vehiculo = Vehiculo.objects.filter(conductor=perfil).first()
    if not vehiculo:
        return Response([])

    reservas = Reserva.objects.filter(vehiculo=vehiculo).exclude(estado='FINALIZADA', pagada=True).order_by('-creada_en')
    return Response(ReservaSerializer(reservas, many=True).data)


@api_view(['GET'])
def vehiculos_disponibles(request):
    asientos = int(request.query_params.get('asientos', 1))
    vehiculos = Vehiculo.objects.filter(
        en_linea=True,
        conductor__estado_validacion='VALIDADO',
        cupos_libres__gte=asientos
    ).select_related('conductor')
    return Response(VehiculoPubSerializer(vehiculos, many=True).data)


@api_view(['POST'])
def crear_reserva(request):
    perfil = get_object_or_404(Perfil, user=request.user)
    vehiculo_id = request.data.get('vehiculo')
    asientos = int(request.data.get('asientos', 1))
    destino = request.data.get('destino', '').strip()

    if not destino or asientos < 1:
        return Response({'detail': 'Destino o asientos inválidos'}, status=status.HTTP_400_BAD_REQUEST)

    with transaction.atomic():
        vehiculo = get_object_or_404(Vehiculo.objects.select_for_update(), id=vehiculo_id)
        if not vehiculo.en_linea or vehiculo.cupos_libres < asientos:
            return Response({'detail': 'Sin cupos disponibles'}, status=status.HTTP_409_CONFLICT)

        vehiculo.cupos_libres -= asientos
        vehiculo.save()

        tarifa_por_asiento = 1000
        reserva = Reserva.objects.create(
            pasajero=perfil,
            vehiculo=vehiculo,
            asientos=asientos,
            destino=destino,
            monto=tarifa_por_asiento * asientos,
        )

    return Response(ReservaSerializer(reserva).data, status=status.HTTP_201_CREATED)


@api_view(['GET'])
def reserva_activa(request):
    perfil = get_object_or_404(Perfil, user=request.user)
    reserva = (
        Reserva.objects.filter(pasajero=perfil)
        .exclude(estado='FINALIZADA', pagada=True)
        .order_by('-creada_en')
        .first()
    )
    if not reserva:
        return Response(None)
    return Response(ReservaSerializer(reserva).data)


@api_view(['POST'])
def finalizar_reserva(request, id):
    perfil = get_object_or_404(Perfil, user=request.user)
    reserva = get_object_or_404(Reserva, id=id)

    if reserva.vehiculo.conductor != perfil:
        return Response({'detail': 'Sin permiso'}, status=status.HTTP_403_FORBIDDEN)

    if reserva.estado != 'FINALIZADA':
        reserva.estado = 'FINALIZADA'
        reserva.save()
        vehiculo = reserva.vehiculo
        vehiculo.cupos_libres = min(vehiculo.capacidad, vehiculo.cupos_libres + reserva.asientos)
        vehiculo.save()

    return Response(ReservaSerializer(reserva).data)


@api_view(['POST'])
def pagar_reserva(request, id):
    reserva = get_object_or_404(Reserva, id=id)
    medio = request.data.get('medio', 'WEBPAY').upper()
    token = request.data.get('token', '').strip()

    if not token:
        return Response({'detail': 'Token de pago requerido'}, status=status.HTTP_400_BAD_REQUEST)

    pago_existente = Pago.objects.filter(token=token).first()
    if pago_existente:
        return Response({'comprobante': pago_existente.comprobante, 'monto': pago_existente.monto})

    if reserva.pagada and hasattr(reserva, 'pago'):
        return Response({'comprobante': reserva.pago.comprobante, 'monto': reserva.pago.monto})

    comprobante = f"CONA-{uuid.uuid4().hex[:8].upper()}"
    pago = Pago.objects.create(
        reserva=reserva,
        medio=medio,
        token=token,
        comprobante=comprobante,
        monto=reserva.monto,
    )
    reserva.pagada = True
    reserva.save()

    return Response({'comprobante': pago.comprobante, 'monto': pago.monto})


@api_view(['POST'])
def alerta_sos(request):
    reserva = get_object_or_404(Reserva, id=request.data.get('reserva'))
    lat = float(request.data.get('lat', 0.0))
    lon = float(request.data.get('lon', 0.0))
    AlertaSOS.objects.create(reserva=reserva, usuario=request.user, lat=lat, lon=lon)
    return Response(status=status.HTTP_201_CREATED)