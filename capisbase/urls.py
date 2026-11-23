from django.urls import path
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from . import views

urlpatterns = [
    path('auth/registro/', views.registro),
    path('auth/login/', TokenObtainPairView.as_view()),
    path('auth/refresh/', TokenRefreshView.as_view()),
    path('yo/', views.yo),
    path('conductor/vehiculo/', views.conductor_vehiculo),
    path('conductor/documentos/', views.subir_documento),
    path('conductor/estado/', views.conductor_estado),
    path('conductor/reservas/', views.conductor_reservas),
    path('vehiculos/disponibles/', views.vehiculos_disponibles),
    path('reservas/', views.crear_reserva),
    path('reservas/activa/', views.reserva_activa),
    path('reservas/<int:id>/finalizar/', views.finalizar_reserva),
    path('reservas/<int:id>/pagar/', views.pagar_reserva),
    path('sos/', views.alerta_sos),
]