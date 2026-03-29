"""
Utilidades para gestión documental según Ley 594 de 2000.
Funciones de auditoría y trazabilidad.
"""
from .models import AccesoDocumento


def registrar_acceso(request, documento, accion):
    """
    Registra un acceso a un documento para auditoría.
    Requerido por Ley 594 para trazabilidad completa.

    Args:
        request: HttpRequest con información del usuario
        documento: Instancia del modelo Documento
        accion: Una de las acciones definidas en AccesoDocumento.Accion
    """
    try:
        # Obtener IP del cliente
        ip_address = None
        if hasattr(request, 'META'):
            x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
            if x_forwarded_for:
                ip_address = x_forwarded_for.split(',')[0].strip()
            else:
                ip_address = request.META.get('REMOTE_ADDR')

        # Obtener User Agent
        user_agent = request.META.get('HTTP_USER_AGENT', '')[:500]  # Limitar a 500 chars

        # Crear registro de acceso
        AccesoDocumento.objects.create(
            documento=documento,
            usuario=request.user if request.user.is_authenticated else None,
            accion=accion,
            ip_address=ip_address,
            user_agent=user_agent,
        )
    except Exception as e:
        # No fallar la funcionalidad principal por error en auditoría
        # En producción esto debería loguearse
        pass