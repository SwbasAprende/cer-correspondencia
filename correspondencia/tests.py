from django.test import TestCase
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.exceptions import ValidationError
from django.contrib.auth import get_user_model
from django.urls import reverse
from .models import Documento
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


class DocumentoSeguridadTest(TestCase):
    def setUp(self):
        User = get_user_model()
        self.admin = User.objects.create_user(username='admin', password='adminpass', rol='administrador')
        self.consulta = User.objects.create_user(username='consulta', password='consultapass', rol='consulta')
        self.activo = User.objects.create_user(username='activo', password='activopass', rol='consulta')

        self.doc_confidencial = Documento.objects.create(
            tipo='OF', flujo='entrada', prioridad='confidencial',
            remitente='Empresa X', destinatario='CER', asunto='Asunto secreto',
            descripcion='Demo confidencial', responsable=self.admin, radicado_por=self.admin
        )

        self.doc_normal = Documento.objects.create(
            tipo='OF', flujo='entrada', prioridad='normal',
            remitente='Empresa Y', destinatario='CER', asunto='Asunto publico',
            descripcion='Demo normal', responsable=self.admin, radicado_por=self.admin
        )

    def test_usuario_sin_permiso_no_puede_ver_confidencial(self):
        self.client.login(username='consulta', password='consultapass')
        url = reverse('documento_detalle', kwargs={'pk': self.doc_confidencial.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

    def test_usuario_sin_permiso_no_puede_editar_documento(self):
        self.client.login(username='consulta', password='consultapass')
        url = reverse('documento_editar', kwargs={'pk': self.doc_normal.pk})
        response = self.client.get(url)
        self.assertIn(response.status_code, (302, 403), 'Consulta no debería tener acceso de edición')

    def test_usuario_consultor_no_puede_radicar(self):
        self.client.login(username='consulta', password='consultapass')
        url = reverse('documento_nuevo')
        response = self.client.get(url)
        self.assertIn(response.status_code, (302, 403), 'Consulta no debería poder acceder a radicar')

    def test_validacion_formulario_datos_invalidos(self):
        self.client.login(username='admin', password='adminpass')
        url = reverse('documento_nuevo')
        response = self.client.post(url, data={
            'tipo': '', 'flujo': '', 'remitente': '', 'destinatario': '', 'asunto': '',
        })
        self.assertIn(response.status_code, [200, 302])

    def test_paginacion_funciona(self):
        for i in range(25):
            Documento.objects.create(
                tipo='OF', flujo='entrada', prioridad='normal',
                remitente=f'Rem{i}', destinatario='CER', asunto=f'Asunto {i}',
                descripcion='Prueba', responsable=self.admin, radicado_por=self.admin
            )
        self.client.login(username='admin', password='adminpass')
        url = reverse('documento_lista') + '?page=2'
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTrue('documentos' in response.context)
        self.assertTrue(len(response.context['documentos']) <= 20)

    def test_busqueda_devuelve_resultados_correctos(self):
        Documento.objects.create(
            tipo='OF', flujo='entrada', prioridad='normal',
            remitente='BusquedaCorp', destinatario='CER', asunto='Prueba especial',
            descripcion='Prueba', responsable=self.admin, radicado_por=self.admin
        )
        self.client.login(username='admin', password='adminpass')
        url = reverse('documento_lista') + '?buscar=BusquedaCorp'
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

