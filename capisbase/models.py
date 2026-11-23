from django.db import models
from django.contrib.auth.models import User


class Perfil(models.Model):
    ROLES = [
        ('PASAJERO', 'Pasajero'),
        ('CONDUCTOR', 'Conductor'),
    ]
    ESTADOS_VALIDACION = [
        ('PENDIENTE', 'Pendiente'),
        ('VALIDADO', 'Validado'),
        ('RECHAZADO', 'Rechazado'),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='perfil')
    nombre = models.CharField(max_length=120)
    rol = models.CharField(max_length=20, choices=ROLES, default='PASAJERO')
    estado_validacion = models.CharField(
        max_length=20, choices=ESTADOS_VALIDACION, null=True, blank=True
    )
    motivo_rechazo = models.TextField(null=True, blank=True)

    def __str__(self):
        return f"{self.nombre} ({self.rol})"


class Vehiculo(models.Model):
    conductor = models.OneToOneField(Perfil, on_delete=models.CASCADE, related_name='vehiculo')
    patente = models.CharField(max_length=12, unique=True)
    modelo = models.CharField(max_length=80)
    capacidad = models.PositiveIntegerField(default=4)
    cupos_libres = models.PositiveIntegerField(default=0)
    maletero = models.BooleanField(default=False)
    en_linea = models.BooleanField(default=False)
    lat = models.FloatField(null=True, blank=True)
    lon = models.FloatField(null=True, blank=True)

    def __str__(self):
        return f"{self.patente} - {self.modelo}"


class Documento(models.Model):
    conductor = models.ForeignKey(Perfil, on_delete=models.CASCADE, related_name='documentos')
    tipo = models.CharField(max_length=50)
    archivo = models.FileField(upload_to='documentos/')
    subido_en = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.tipo} - {self.conductor.nombre}"


class Reserva(models.Model):
    ESTADOS = [
        ('ACTIVA', 'Activa'),
        ('FINALIZADA', 'Finalizada'),
    ]

    pasajero = models.ForeignKey(Perfil, on_delete=models.CASCADE, related_name='reservas')
    vehiculo = models.ForeignKey(Vehiculo, on_delete=models.CASCADE, related_name='reservas')
    estado = models.CharField(max_length=20, choices=ESTADOS, default='ACTIVA')
    asientos = models.PositiveIntegerField(default=1)
    destino = models.CharField(max_length=200)
    monto = models.PositiveIntegerField(default=1000)
    pagada = models.BooleanField(default=False)
    creada_en = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Reserva #{self.id} - {self.destino} ({self.estado})"


class Pago(models.Model):
    MEDIOS = [
        ('EFECTIVO', 'Efectivo'),
        ('WEBPAY', 'Webpay'),
    ]

    reserva = models.OneToOneField(Reserva, on_delete=models.CASCADE, related_name='pago')
    medio = models.CharField(max_length=20, choices=MEDIOS)
    token = models.CharField(max_length=100, unique=True)
    comprobante = models.CharField(max_length=60, unique=True)
    monto = models.PositiveIntegerField()
    creado_en = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.comprobante} (${self.monto})"


class AlertaSOS(models.Model):
    reserva = models.ForeignKey(Reserva, on_delete=models.CASCADE, related_name='alertas_sos')
    usuario = models.ForeignKey(User, on_delete=models.CASCADE)
    lat = models.FloatField()
    lon = models.FloatField()
    creada_en = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"SOS Reserva #{self.reserva_id}"

