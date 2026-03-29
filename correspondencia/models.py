"""
Modelos del Sistema de Correspondencia Institucional CER
Cumple con Ley 594 de 2000 - Archivo General de la Nación
"""
from django.db import models
from django.conf import settings
from django.utils import timezone
import datetime


def ruta_documento(instance, filename):
    """Organiza los archivos por año/tipo/flujo — cumple TRD Ley 594"""
    anio = timezone.now().year
    return f"documentos/{anio}/{instance.flujo}/{instance.tipo}/{filename}"


class Documento(models.Model):
    """
    Documento de correspondencia institucional del CER.
    Cada instancia representa un documento radicado (entrada o salida).
    """

    # ── Tipos de documento ───────────────────────────────────────────────────
    class Tipo(models.TextChoices):
        OFICIO      = 'OF', 'Oficio'
        MEMORANDO   = 'MM', 'Memorando'
        CIRCULAR    = 'CR', 'Circular'
        RESOLUCION  = 'RS', 'Resolución'
        ACTA        = 'AC', 'Acta'

    # ── Flujo del documento ──────────────────────────────────────────────────
    class Flujo(models.TextChoices):
        ENTRADA = 'entrada', 'Entrada'
        SALIDA  = 'salida',  'Salida'

    # ── Prioridad ────────────────────────────────────────────────────────────
    class Prioridad(models.TextChoices):
        NORMAL        = 'normal',        'Normal'
        URGENTE       = 'urgente',       'Urgente'
        CONFIDENCIAL  = 'confidencial',  'Confidencial'

    # ── Estado de trámite ────────────────────────────────────────────────────
    class Estado(models.TextChoices):
        RECIBIDO    = 'recibido',    'Recibido'
        EN_TRAMITE  = 'en_tramite',  'En Trámite'
        RESPONDIDO  = 'respondido',  'Respondido'
        ARCHIVADO   = 'archivado',   'Archivado'

    # ── Actor del ecosistema CER ─────────────────────────────────────────────
    class Actor(models.TextChoices):
        GREMIO          = 'gremio',          'Gremio'
        AGROINDUSTRIA   = 'agroindustria',   'Agroindustria'
        COOPERATIVA     = 'cooperativa',     'Cooperativa'
        EDUCACION       = 'educacion',       'Institución Educativa'
        CAMARA          = 'camara',          'Cámara de Comercio'
        DIAN            = 'dian',            'DIAN'
        ENTIDAD_PUBLICA = 'entidad_publica', 'Entidad Pública'
        SECTOR_PRIVADO  = 'sector_privado',  'Sector Privado'
        INTERNO         = 'interno',         'Interno CER'
        OTRO            = 'otro',            'Otro'

    # ════════════════════════════════════════════════════════════════════════
    # CAMPOS DEL DOCUMENTO
    # ════════════════════════════════════════════════════════════════════════

    # Radicado — se genera automáticamente (ej: CER-OF-2025-001)
    radicado = models.CharField(
        max_length=30,
        unique=True,
        editable=False,
        verbose_name='Número de radicado'
    )
    consecutivo_anio = models.PositiveIntegerField(
        editable=False,
        verbose_name='Consecutivo del año'
    )

    # Clasificación
    tipo      = models.CharField(max_length=2,  choices=Tipo.choices,      db_index=True, verbose_name='Tipo de documento')
    flujo     = models.CharField(max_length=10, choices=Flujo.choices,     db_index=True, verbose_name='Flujo')
    prioridad = models.CharField(max_length=15, choices=Prioridad.choices, default=Prioridad.NORMAL, db_index=True, verbose_name='Prioridad')
    estado    = models.CharField(max_length=15, choices=Estado.choices,    default=Estado.RECIBIDO, db_index=True, verbose_name='Estado')
    actor     = models.CharField(max_length=20, choices=Actor.choices,     default=Actor.OTRO,       db_index=True, verbose_name='Actor del ecosistema')

    # Partes
    remitente   = models.CharField(max_length=200, verbose_name='Remitente')
    destinatario = models.CharField(max_length=200, verbose_name='Destinatario')
    entidad     = models.CharField(max_length=200, blank=True, verbose_name='Entidad / Organización')

    # Contenido
    asunto       = models.CharField(max_length=500, verbose_name='Asunto')
    descripcion  = models.TextField(blank=True, verbose_name='Descripción / Observaciones')

    # Archivo digital
    archivo = models.FileField(
        upload_to=ruta_documento,
        blank=True,
        null=True,
        verbose_name='Archivo digital'
    )

    # Fechas
    
    fecha_radicacion = models.DateField(default=timezone.now, verbose_name='Fecha de radicación')
    hora_radicacion = models.TimeField(default=timezone.now, verbose_name='Hora de radicación')
    fecha_documento  = models.DateField(blank=True, null=True, verbose_name='Fecha del documento')
    fecha_limite     = models.DateField(blank=True, null=True, db_index=True, verbose_name='Fecha límite de respuesta')
    fecha_respuesta  = models.DateField(blank=True, null=True, verbose_name='Fecha de respuesta')

    # Responsable asignado
    responsable = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='documentos_asignados',
        verbose_name='Responsable'
    )

    # Quién radicó el documento
    radicado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='documentos_radicados',
        verbose_name='Radicado por'
    )

    # Referencia a otro documento (para respuestas)
    documento_referencia = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='respuestas',
        verbose_name='En respuesta a'
    )

    class Meta:
        verbose_name = 'Documento'
        verbose_name_plural = 'Documentos'
        ordering = ['-fecha_radicacion', '-consecutivo_anio']
        permissions = [
            ('view_confidenciales', 'Puede ver documentos confidenciales'),
        ]
        indexes = [
            models.Index(fields=['radicado']),
            models.Index(fields=['fecha_radicacion']),
            models.Index(fields=['estado']),
            models.Index(fields=['remitente']),
            models.Index(fields=['tipo']),
            models.Index(fields=['flujo']),
            models.Index(fields=['prioridad']),
            models.Index(fields=['fecha_limite']),
        ]

    def __str__(self):
        return f"{self.radicado} — {self.asunto[:60]}"

    # ── Generar radicado automático ──────────────────────────────────────────
    def _generar_consecutivo(self):
        """Obtiene el siguiente consecutivo para este tipo y año"""
        anio = self.fecha_radicacion.year if self.fecha_radicacion else timezone.now().year
        ultimo = Documento.objects.filter(
            tipo=self.tipo,
            fecha_radicacion__year=anio
        ).order_by('-consecutivo_anio').first()
        return (ultimo.consecutivo_anio + 1) if ultimo else 1

    def save(self, *args, **kwargs):
        # Solo genera el radicado la primera vez (documentos nuevos)
        if not self.pk:
            self.consecutivo_anio = self._generar_consecutivo()
            anio = self.fecha_radicacion.year if self.fecha_radicacion else timezone.now().year
            self.radicado = f"CER-{self.tipo}-{anio}-{str(self.consecutivo_anio).zfill(3)}"

            # Calcular fecha límite según prioridad
            dias = {
                self.Prioridad.NORMAL: 15,
                self.Prioridad.URGENTE: 5,
                self.Prioridad.CONFIDENCIAL: 3,
            }
            self.fecha_limite = self.fecha_radicacion + datetime.timedelta(
                days=dias.get(self.prioridad, 15)
            )

        super().save(*args, **kwargs)

    # ── Propiedades útiles ───────────────────────────────────────────────────
    @property
    def esta_vencido(self):
        """True si pasó la fecha límite y no está respondido/archivado"""
        if self.fecha_limite and self.estado not in [self.Estado.RESPONDIDO, self.Estado.ARCHIVADO]:
            return timezone.now().date() > self.fecha_limite
        return False

    @property
    def dias_restantes(self):
        """Días que quedan antes del vencimiento"""
        if self.fecha_limite:
            delta = self.fecha_limite - timezone.now().date()
            return delta.days
        return None
    
    @property
    def fecha_hora_radicacion(self):
        """Retorna fecha y hora formateadas para el sticker"""
        fecha = self.fecha_radicacion.strftime('%d/%m/%Y')
        hora  = self.hora_radicacion.strftime('%H:%M:%S')
        return fecha, hora


class Trazabilidad(models.Model):
    """
    Historial de cambios de estado de cada documento.
    Requerido por Ley 594 de 2000 para auditoría.
    """
    documento       = models.ForeignKey(Documento, on_delete=models.CASCADE, related_name='trazabilidad')
    estado_anterior = models.CharField(max_length=15, choices=Documento.Estado.choices, blank=True)
    estado_nuevo    = models.CharField(max_length=15, choices=Documento.Estado.choices)
    usuario         = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    fecha           = models.DateTimeField(auto_now_add=True)
    nota            = models.TextField(blank=True, verbose_name='Observación del cambio')

    class Meta:
        verbose_name = 'Trazabilidad'
        verbose_name_plural = 'Trazabilidad'
        ordering = ['-fecha']

    def __str__(self):
        return f"{self.documento.radicado} | {self.estado_anterior} → {self.estado_nuevo}"