from django.contrib import admin
from .models import Documento, Trazabilidad


class TrazabilidadInline(admin.TabularInline):
    model = Trazabilidad
    extra = 0
    readonly_fields = ['estado_anterior', 'estado_nuevo', 'usuario', 'fecha', 'nota']
    can_delete = False


@admin.register(Documento)
class DocumentoAdmin(admin.ModelAdmin):
    list_display  = ['radicado', 'tipo', 'flujo', 'asunto', 'remitente', 'estado', 'prioridad', 'fecha_radicacion']
    list_filter   = ['tipo', 'flujo', 'estado', 'prioridad', 'actor', 'fecha_radicacion']
    search_fields = ['radicado', 'asunto', 'remitente', 'destinatario']
    readonly_fields = ['radicado', 'consecutivo_anio', 'fecha_limite']
    inlines       = [TrazabilidadInline]
    date_hierarchy = 'fecha_radicacion'


@admin.register(Trazabilidad)
class TrazabilidadAdmin(admin.ModelAdmin):
    list_display  = ['documento', 'estado_anterior', 'estado_nuevo', 'usuario', 'fecha']
    readonly_fields = ['documento', 'estado_anterior', 'estado_nuevo', 'usuario', 'fecha']