from django.contrib import admin
from .models import Perfil, Vehiculo, Documento, Reserva, Pago, AlertaSOS


class VehiculoInline(admin.StackedInline):
    model = Vehiculo
    extra = 0


class DocumentoInline(admin.TabularInline):
    model = Documento
    extra = 0
    readonly_fields = ('subido_en',)


@admin.register(Perfil)
class PerfilAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'rol', 'estado_validacion')
    list_filter = ('rol', 'estado_validacion')
    search_fields = ('nombre', 'user__email')
    inlines = [VehiculoInline, DocumentoInline]
    actions = ['aprobar_conductores', 'rechazar_conductores']

    @admin.action(description='Aprobar conductores seleccionados (VALIDADO)')
    def aprobar_conductores(self, request, queryset):
        queryset.filter(rol='CONDUCTOR').update(
            estado_validacion='VALIDADO',
            motivo_rechazo=''
        )

    @admin.action(description='Rechazar conductores seleccionados (RECHAZADO)')
    def rechazar_conductores(self, request, queryset):
        queryset.filter(rol='CONDUCTOR').update(
            estado_validacion='RECHAZADO',
            motivo_rechazo='Documentación incompleta o inválida'
        )


admin.site.register(Vehiculo)
admin.site.register(Documento)
admin.site.register(Reserva)
admin.site.register(Pago)
admin.site.register(AlertaSOS)