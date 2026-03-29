"""
Notificaciones por email del Sistema de Correspondencia CER
Se envían automáticamente en eventos clave del sistema
"""
import logging
from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone

logger = logging.getLogger(__name__)


def _enviar(asunto, mensaje, destinatarios):
    """Función base para enviar emails — captura errores sin romper el sistema"""
    if not destinatarios:
        return
    try:
        send_mail(
            subject      = f'[CER] {asunto}',
            message      = mensaje,
            from_email   = settings.DEFAULT_FROM_EMAIL,
            recipient_list = [d for d in destinatarios if d],
            fail_silently = False,
        )
    except Exception as e:
        logger.exception('[CER Email Error] No se pudo enviar el mensaje')


def notificar_nuevo_documento(documento):
    """
    Notifica cuando se radica un documento nuevo.
    Se envía al responsable asignado y al administrador.
    """
    from usuarios.models import Usuario

    # Obtener emails
    destinatarios = []

    if documento.responsable and documento.responsable.email:
        destinatarios.append(documento.responsable.email)

    # Notificar también a administradores
    admins = Usuario.objects.filter(
        rol='administrador', activo_sistema=True
    ).exclude(pk=documento.responsable.pk if documento.responsable else None)

    for admin in admins:
        if admin.email:
            destinatarios.append(admin.email)

    if not destinatarios:
        return

    config   = settings.CER_CONFIG
    fecha    = documento.fecha_radicacion.strftime('%d/%m/%Y')
    hora     = documento.hora_radicacion.strftime('%H:%M:%S')

    asunto  = f'Nuevo documento radicado: {documento.radicado}'
    mensaje = f"""
Centro de Estudios Regionales — CER
Sistema de Correspondencia Institucional
{'='*50}

Se ha radicado un nuevo documento en el sistema.

NÚMERO DE RADICADO:  {documento.radicado}
TIPO:                {documento.get_tipo_display()}
FLUJO:               {documento.get_flujo_display()}
ASUNTO:              {documento.asunto}
REMITENTE:           {documento.remitente}
DESTINATARIO:        {documento.destinatario}
PRIORIDAD:           {documento.get_prioridad_display()}
FECHA DE RADICACIÓN: {fecha}
HORA DE RADICACIÓN:  {hora}
FECHA LÍMITE:        {documento.fecha_limite.strftime('%d/%m/%Y') if documento.fecha_limite else 'N/A'}

{'⚠️  DOCUMENTO URGENTE — Requiere atención en 5 días hábiles' if documento.prioridad == 'urgente' else ''}
{'🔒  DOCUMENTO CONFIDENCIAL — Acceso restringido' if documento.prioridad == 'confidencial' else ''}

Ingresa al sistema para ver el detalle completo.

{'='*50}
{config.get('nombre', 'CER')} | Ley 594 de 2000
Este es un mensaje automático, no responder.
    """.strip()

    _enviar(asunto, mensaje, destinatarios)


def notificar_cambio_estado(documento, estado_anterior, estado_nuevo, usuario, nota=''):
    """Notifica cuando cambia el estado de un documento"""
    from usuarios.models import Usuario

    destinatarios = []

    if documento.responsable and documento.responsable.email:
        destinatarios.append(documento.responsable.email)
    if documento.radicado_por and documento.radicado_por.email:
        destinatarios.append(documento.radicado_por.email)

    if not destinatarios:
        return

    estados = {
        'recibido':   'Recibido',
        'en_tramite': 'En Trámite',
        'respondido': 'Respondido',
        'archivado':  'Archivado',
    }

    asunto  = f'Cambio de estado: {documento.radicado}'
    mensaje = f"""
Centro de Estudios Regionales — CER
Sistema de Correspondencia Institucional
{'='*50}

El documento {documento.radicado} ha cambiado de estado.

RADICADO:       {documento.radicado}
ASUNTO:         {documento.asunto}
ESTADO ANTERIOR: {estados.get(estado_anterior, estado_anterior)}
NUEVO ESTADO:   {estados.get(estado_nuevo, estado_nuevo)}
ACTUALIZADO POR: {usuario.get_full_name() or usuario.username}
FECHA:          {timezone.now().strftime('%d/%m/%Y %H:%M')}
{'OBSERVACIÓN:    ' + nota if nota else ''}

{'='*50}
{settings.CER_CONFIG.get('nombre', 'CER')} | Ley 594 de 2000
Este es un mensaje automático, no responder.
    """.strip()

    _enviar(asunto, mensaje, list(set(destinatarios)))


def notificar_documento_vencido(documento):
    """Notifica cuando un documento está próximo a vencer (1 día)"""
    from usuarios.models import Usuario

    destinatarios = []

    if documento.responsable and documento.responsable.email:
        destinatarios.append(documento.responsable.email)

    admins = Usuario.objects.filter(rol='administrador', activo_sistema=True)
    for admin in admins:
        if admin.email:
            destinatarios.append(admin.email)

    if not destinatarios:
        return

    asunto  = f'⚠️ Documento próximo a vencer: {documento.radicado}'
    mensaje = f"""
Centro de Estudios Regionales — CER
Sistema de Correspondencia Institucional
{'='*50}

⚠️  ALERTA: El siguiente documento vence MAÑANA

RADICADO:     {documento.radicado}
ASUNTO:       {documento.asunto}
REMITENTE:    {documento.remitente}
PRIORIDAD:    {documento.get_prioridad_display()}
FECHA LÍMITE: {documento.fecha_limite.strftime('%d/%m/%Y')}
ESTADO ACTUAL: {documento.get_estado_display()}

Por favor gestione este documento a la brevedad.

{'='*50}
{settings.CER_CONFIG.get('nombre', 'CER')} | Ley 594 de 2000
Este es un mensaje automático, no responder.
    """.strip()

    _enviar(asunto, mensaje, list(set(destinatarios)))