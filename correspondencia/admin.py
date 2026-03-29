from django.contrib import admin
from .models import Documento, Trazabilidad, TRD, AccesoDocumento, AuditoriaDocumento


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


@admin.register(TRD)
class TRDAdmin(admin.ModelAdmin):
    list_display  = ['serie', 'subserie', 'tipo_documental', 'retencion_gestion', 'retencion_central', 'disposicion_final', 'activo']
    list_filter   = ['tipo_documental', 'disposicion_final', 'activo']
    search_fields = ['serie', 'subserie']
    ordering      = ['serie', 'subserie']


@admin.register(AccesoDocumento)
class AccesoDocumentoAdmin(admin.ModelAdmin):
    list_display  = ['documento', 'usuario', 'accion', 'fecha_hora', 'ip_address']
    list_filter   = ['accion', 'fecha_hora', 'usuario']
    search_fields = ['documento__radicado', 'usuario__username']
    readonly_fields = ['documento', 'usuario', 'accion', 'fecha_hora', 'ip_address', 'user_agent']
    date_hierarchy = 'fecha_hora'


@admin.register(AuditoriaDocumento)
class AuditoriaDocumentoAdmin(admin.ModelAdmin):
    list_display  = ['documento', 'usuario', 'campo_modificado', 'fecha_hora', 'ip_address']
    list_filter   = ['campo_modificado', 'fecha_hora', 'usuario']
    search_fields = ['documento__radicado', 'usuario__username', 'campo_modificado']
    readonly_fields = ['documento', 'usuario', 'campo_modificado', 'valor_anterior', 'valor_nuevo', 'fecha_hora', 'ip_address']
    date_hierarchy = 'fecha_hora'