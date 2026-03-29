"""
Sistema de grupos y permisos para el CER
Define los 4 grupos con sus permisos asociados
"""
import logging
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from correspondencia.models import Documento, Trazabilidad
from plantillas.models import PlantillaDocumento, DocumentoGenerado
from usuarios.models import Usuario

logger = logging.getLogger(__name__)


def crear_grupos_sistema():
    """
    Crea los 4 grupos del sistema con sus permisos.
    Se ejecuta al hacer python manage.py crear_grupos
    
    Grupos:
    1. Administrador - Acceso total al sistema
    2. Radicador - Puede crear, editar, cambiar estado de documentos
    3. Consultor - Puede ver documentos y generar reportes
    4. Solo lectura - Solo visualización, sin acciones
    """
    
    # Obtener content types
    ct_documento = ContentType.objects.get_for_model(Documento)
    ct_usuario = ContentType.objects.get_for_model(Usuario)
    ct_plantilla = ContentType.objects.get_for_model(PlantillaDocumento)
    ct_doc_generado = ContentType.objects.get_for_model(DocumentoGenerado)
    
    # ── Obtener o crear permisos personalizados ──────────────────────────────
    perm_ver_confidenciales, _ = Permission.objects.get_or_create(
        codename='view_confidenciales',
        content_type=ct_documento,
        defaults={'name': 'Puede ver documentos confidenciales'}
    )
    
    # ────────────────────────────────────────────────────────────────────────────
    # GRUPO 1: ADMINISTRADOR - Acceso total
    # ────────────────────────────────────────────────────────────────────────────
    grupo_admin, creado = Group.objects.get_or_create(name='Administrador')
    if creado:
        logger.warning('✅ Grupo "Administrador" creado')

    permisos_admin = Permission.objects.filter(
        content_type__in=[ct_documento, ct_usuario, ct_plantilla, ct_doc_generado]
    )
    grupo_admin.permissions.set(permisos_admin)
    
    # ────────────────────────────────────────────────────────────────────────────
    # GRUPO 2: RADICADOR - Crear, editar, cambiar estado
    # ────────────────────────────────────────────────────────────────────────────
    grupo_radicador, creado = Group.objects.get_or_create(name='Radicador')
    if creado:
        logger.warning('✅ Grupo "Radicador" creado')

    permisos_radicador = Permission.objects.filter(
        codename__in=[
            'add_documento',           # Radicar (crear documento)
            'change_documento',        # Cambiar estado
            'view_documento',          # Ver documentos
            'view_confidenciales',     # Ver documentos confidenciales
            'add_documentogenerado',   # Generar PDF
            'change_plantilladocumento',  # Editar plantillas
        ]
    )
    grupo_radicador.permissions.set(permisos_radicador)
    
    # ────────────────────────────────────────────────────────────────────────────
    # GRUPO 3: CONSULTOR - Solo ver y reportes
    # ────────────────────────────────────────────────────────────────────────────
    grupo_consultor, creado = Group.objects.get_or_create(name='Consultor')
    if creado:
        logger.warning('✅ Grupo "Consultor" creado')

    permisos_consultor = Permission.objects.filter(
        codename__in=[
            'view_documento',         # Ver documentos
            'view_trazabilidad',      # Ver historial
        ]
    )
    grupo_consultor.permissions.set(permisos_consultor)
    
    # ────────────────────────────────────────────────────────────────────────────
    # GRUPO 4: SOLO LECTURA - Visualización sin acciones
    # ────────────────────────────────────────────────────────────────────────────
    grupo_lectura, creado = Group.objects.get_or_create(name='Solo lectura')
    if creado:
        logger.warning('✅ Grupo "Solo lectura" creado')

    permisos_lectura = Permission.objects.filter(
        codename__in=[
            'view_documento',         # Solo ver
        ]
    )
    grupo_lectura.permissions.set(permisos_lectura)
    
    logger.warning("""
════════════════════════════════════════════════════════════════════════════════
✅ SISTEMA DE GRUPOS CREADO EXITOSAMENTE

GRUPOS DISPONIBLES:
───────────────────────────────────────────────────────────────────────────────
1. Administrador    → Acceso total al sistema
2. Radicador        → Crear, editar y cambiar estado de documentos
3. Consultor        → Ver documentos y generar reportes
4. Solo lectura     → Visualización sin acciones

PRÓXIMOS PASOS:
───────────────────────────────────────────────────────────────────────────────
1. En Django Admin: Ir a Usuarios > Usuarios
2. Editar un usuario
3. En "Grupos", seleccionar el grupo apropiado
4. Guardar

Los permisos se asignan automáticamente según el grupo.
════════════════════════════════════════════════════════════════════════════════
    """)
