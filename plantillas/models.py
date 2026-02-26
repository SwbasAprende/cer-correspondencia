from django.db import models
from django.conf import settings


class PlantillaDocumento(models.Model):
    """
    Almacena el contenido editable de cada tipo de documento institucional.
    El PDF se genera combinando esta plantilla con los datos del documento radicado.
    """

    class Tipo(models.TextChoices):
        OFICIO     = 'OF', 'Oficio'
        MEMORANDO  = 'MM', 'Memorando'
        CIRCULAR   = 'CR', 'Circular'
        RESOLUCION = 'RS', 'Resolución'
        ACTA       = 'AC', 'Acta'

    tipo        = models.CharField(max_length=2, choices=Tipo.choices, unique=True, verbose_name='Tipo de documento')
    nombre      = models.CharField(max_length=100, verbose_name='Nombre de la plantilla')
    encabezado  = models.TextField(blank=True, verbose_name='Texto de encabezado / considerandos')
    cuerpo      = models.TextField(verbose_name='Cuerpo del documento (plantilla base)')
    pie         = models.TextField(blank=True, verbose_name='Texto de cierre / pie')
    activa      = models.BooleanField(default=True, verbose_name='Plantilla activa')
    actualizado = models.DateTimeField(auto_now=True)
    actualizado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, blank=True, verbose_name='Actualizado por'
    )

    class Meta:
        verbose_name = 'Plantilla'
        verbose_name_plural = 'Plantillas'

    def __str__(self):
        return f"{self.get_tipo_display()} — {self.nombre}"


class DocumentoGenerado(models.Model):
    """
    Registro de cada PDF generado desde una plantilla.
    Requerido por Ley 594 de 2000 para trazabilidad documental.
    """
    from correspondencia.models import Documento as Doc

    documento   = models.ForeignKey(
        'correspondencia.Documento', on_delete=models.CASCADE,
        related_name='pdfs_generados', verbose_name='Documento radicado'
    )
    plantilla   = models.ForeignKey(
        PlantillaDocumento, on_delete=models.SET_NULL,
        null=True, verbose_name='Plantilla usada'
    )
    contenido   = models.TextField(verbose_name='Contenido final del documento')
    archivo_pdf = models.FileField(
        upload_to='plantillas/generados/', blank=True, null=True,
        verbose_name='Archivo PDF generado'
    )
    generado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, verbose_name='Generado por'
    )
    fecha = models.DateTimeField(auto_now_add=True, verbose_name='Fecha de generación')

    class Meta:
        verbose_name = 'Documento generado'
        verbose_name_plural = 'Documentos generados'
        ordering = ['-fecha']

    def __str__(self):
        return f"PDF {self.documento.radicado} — {self.fecha.strftime('%d/%m/%Y %H:%M')}"