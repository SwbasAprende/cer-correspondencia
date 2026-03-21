from django.test import TestCase
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.exceptions import ValidationError
from .validators import validar_archivo_documento


class ValidadorArchivoTest(TestCase):
    """Test de validación de archivos por MIME type"""
    
    def test_pdf_valido(self):
        """Debe aceptar un PDF válido"""
        # Crear un PDF mínimo válido
        contenido_pdf = b'%PDF-1.4\n'
        archivo = SimpleUploadedFile(
            "documento.pdf",
            contenido_pdf,
            content_type="application/pdf"
        )
        # No debe lanzar excepción
        try:
            validar_archivo_documento(archivo)
        except ValidationError:
            self.fail("validar_archivo_documento() lanzó ValidationError inesperado para PDF válido")
    
    def test_png_valido(self):
        """Debe aceptar un PNG válido"""
        # Magic number PNG: \x89PNG
        contenido_png = b'\x89PNG\r\n\x1a\n'
        archivo = SimpleUploadedFile(
            "imagen.png",
            contenido_png,
            content_type="image/png"
        )
        try:
            validar_archivo_documento(archivo)
        except ValidationError:
            self.fail("validar_archivo_documento() lanzó ValidationError inesperado para PNG válido")
    
    def test_jpg_valido(self):
        """Debe aceptar un JPG válido"""
        # Magic number JPG: \xFF\xD8\xFF
        contenido_jpg = b'\xff\xd8\xff\xe0\x00\x10JFIF'
        archivo = SimpleUploadedFile(
            "imagen.jpg",
            contenido_jpg,
            content_type="image/jpeg"
        )
        try:
            validar_archivo_documento(archivo)
        except ValidationError:
            self.fail("validar_archivo_documento() lanzó ValidationError inesperado para JPG válido")
    
    def test_extension_no_permitida(self):
        """Debe rechazar arhivos con extensión no permitida"""
        contenido = b'cualquier contenido'
        archivo = SimpleUploadedFile(
            "malicioso.exe",
            contenido,
            content_type="application/x-msdownload"
        )
        with self.assertRaises(ValidationError) as context:
            validar_archivo_documento(archivo)
        self.assertIn("Extensión no permitida", str(context.exception))
    
    def test_archivo_renombrado_pdf_a_exe(self):
        """Debe rechazar un EXE renombrado como PDF"""
        # Contenido con magic number de EXE
        contenido_exe = b'MZ\x90\x00'  # Magic number de EXE
        archivo = SimpleUploadedFile(
            "falso.pdf",
            contenido_exe,
            content_type="application/pdf"
        )
        with self.assertRaises(ValidationError) as context:
            validar_archivo_documento(archivo)
        self.assertIn("contenido del archivo no es válido", str(context.exception))
    
    def test_archivo_muy_grande(self):
        """Debe rechazar archivos mayores a 10 MB"""
        # Crear un archivo de 11 MB
        contenido = b'%PDF-1.4\n' + (b'x' * (11 * 1024 * 1024))
        archivo = SimpleUploadedFile(
            "grande.pdf",
            contenido,
            content_type="application/pdf"
        )
        with self.assertRaises(ValidationError) as context:
            validar_archivo_documento(archivo)
        self.assertIn("demasiado grande", str(context.exception))
    
    def test_archivo_opcional(self):
        """Debe permitir un archivo vacío/None (campo opcional)"""
        # No debe lanzar excepción
        try:
            validar_archivo_documento(None)
        except ValidationError:
            self.fail("validar_archivo_documento() lanzó ValidationError inesperado para archivo None")

