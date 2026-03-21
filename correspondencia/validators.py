"""
Validadores personalizados para el Sistema de Correspondencia CER
Validación de archivos, formularios y datos sensibles
"""
from django.core.exceptions import ValidationError


def validar_archivo_documento(archivo):
    """
    Valida que el archivo subido sea de un tipo permitido.
    Verifica: extensión, tamaño y magic numbers (contenido real del archivo).
    
    Tipos permitidos: PDF, DOCX, XLSX, JPG, PNG
    Tamaño máximo: 10 MB
    
    Args:
        archivo: UploadedFile desde Django forms
        
    Raises:
        ValidationError: Si el archivo no cumple los requisitos
    """
    
    # ── Definir tipos permitidos ─────────────────────────────────────────────
    # Magic numbers: primeros bytes específicos de cada formato
    MAGIC_NUMBERS = {
        b'\x25\x50\x44\x46': ('application/pdf', 'PDF'),  # %PDF
        b'\x50\x4b\x03\x04': ('application/vnd.openxmlformats-officedocument', 'DOCX/XLSX'),  # ZIP (DOCX, XLSX)
        b'\xff\xd8\xff': ('image/jpeg', 'JPG'),  # JPG/JPEG
        b'\x89\x50\x4e\x47': ('image/png', 'PNG'),  # PNG
    }
    
    EXTENSIONES_PERMITIDAS = {'.pdf', '.docx', '.xlsx', '.jpg', '.jpeg', '.png'}
    TAMANIO_MAXIMO = 10 * 1024 * 1024  # 10 MB
    
    if not archivo:
        return  # Campo es opcional
    
    # ── 1. Validar extensión del archivo ─────────────────────────────────────
    nombre_archivo = archivo.name.lower()
    extension_encontrada = None
    
    for ext in EXTENSIONES_PERMITIDAS:
        if nombre_archivo.endswith(ext):
            extension_encontrada = ext
            break
    
    if not extension_encontrada:
        tipos_como_texto = ', '.join([ext[1:].upper() for ext in sorted(EXTENSIONES_PERMITIDAS)])
        raise ValidationError(
            f'❌ Extensión no permitida. Archivo: "{nombre_archivo}". '
            f'Solo se aceptan: {tipos_como_texto}.'
        )
    
    # ── 2. Validar tamaño del archivo ────────────────────────────────────────
    if archivo.size > TAMANIO_MAXIMO:
        tamanio_mb = archivo.size / (1024 * 1024)
        raise ValidationError(
            f'❌ El archivo es demasiado grande ({tamanio_mb:.1f} MB). '
            f'Máximo permitido: 10 MB.'
        )
    
    # ── 3. Validar contenido real (magic numbers) ────────────────────────────
    # Esto previene que alguien renombre un .exe a .pdf
    archivo.seek(0)
    primeros_bytes = archivo.read(4)
    archivo.seek(0)  # Resetear puntero para lectura posterior
    
    tipo_detectado = None
    encontrado = False
    
    for magic_number, (mime_type, tipo_nombre) in MAGIC_NUMBERS.items():
        if primeros_bytes.startswith(magic_number):
            tipo_detectado = tipo_nombre
            encontrado = True
            
            # Validación adicional para DOCX/XLSX
            if magic_number == b'\x50\x4b\x03\x04':
                # Los archivos DOCX/XLSX son zips, pero necesitamos diferenciarlos
                # por ahora aceptamos ambos
                pass
            break
    
    if not encontrado:
        # Error: el contenido del archivo no coincide con los tipos permitidos
        primeros_bytes_hex = primeros_bytes.hex() if primeros_bytes else 'vacío'
        raise ValidationError(
            f'❌ El contenido del archivo no es válido o no es soportado. '
            f'Por favor, verifica que sea un archivo genuino de tipo: '
            f'PDF, DOCX, XLSX, JPG o PNG. '
            f'(Detectado: {primeros_bytes_hex})'
        )
