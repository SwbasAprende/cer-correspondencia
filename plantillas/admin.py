from django.contrib import admin
from .models import PlantillaDocumento, DocumentoGenerado


@admin.register(PlantillaDocumento)
class PlantillaAdmin(admin.ModelAdmin):
    list_display  = ['get_tipo_display', 'nombre', 'activa', 'actualizado']
    list_filter   = ['tipo', 'activa']


@admin.register(DocumentoGenerado)
class DocumentoGeneradoAdmin(admin.ModelAdmin):
    list_display  = ['documento', 'plantilla', 'generado_por', 'fecha']
    readonly_fields = ['documento', 'plantilla', 'contenido', 'generado_por', 'fecha']