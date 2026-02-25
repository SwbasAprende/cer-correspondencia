"""
Modelo de Usuario personalizado para el Sistema CER
Extiende el usuario base de Django agregando roles institucionales
"""
from django.contrib.auth.models import AbstractUser
from django.db import models


class Usuario(AbstractUser):
    """
    Usuario del sistema con roles institucionales del CER.
    Extiende AbstractUser para conservar login, password, etc.
    """

    class Rol(models.TextChoices):
        ADMINISTRADOR = 'administrador', 'Administrador'
        DIRECTOR      = 'director',      'Director'
        CONSULTA      = 'consulta',      'Consulta'

    rol = models.CharField(
        max_length=20,
        choices=Rol.choices,
        default=Rol.CONSULTA,
        verbose_name='Rol en el sistema'
    )
    cargo = models.CharField(
        max_length=100,
        blank=True,
        verbose_name='Cargo institucional'
    )
    telefono = models.CharField(
        max_length=20,
        blank=True,
        verbose_name='Teléfono'
    )
    firma = models.ImageField(
        upload_to='firmas/',
        blank=True,
        null=True,
        verbose_name='Firma digital'
    )
    activo_sistema = models.BooleanField(
        default=True,
        verbose_name='Activo en el sistema'
    )
    fecha_creacion = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Fecha de creación'
    )

    class Meta:
        verbose_name = 'Usuario'
        verbose_name_plural = 'Usuarios'
        ordering = ['last_name', 'first_name']

    def __str__(self):
        return f"{self.get_full_name() or self.username} ({self.get_rol_display()})"

    # ── Helpers de permisos por rol ──────────────────────────────────────────
    @property
    def es_administrador(self):
        return self.rol == self.Rol.ADMINISTRADOR

    @property
    def es_director(self):
        return self.rol == self.Rol.DIRECTOR

    @property
    def es_consulta(self):
        return self.rol == self.Rol.CONSULTA

    @property
    def puede_radicar(self):
        """Administrador y Director pueden radicar documentos"""
        return self.rol in [self.Rol.ADMINISTRADOR, self.Rol.DIRECTOR]

    @property
    def puede_gestionar_usuarios(self):
        """Solo el Administrador gestiona usuarios"""
        return self.rol == self.Rol.ADMINISTRADOR

    @property
    def puede_ver_confidenciales(self):
        """Solo Administrador y Director ven documentos confidenciales"""
        return self.rol in [self.Rol.ADMINISTRADOR, self.Rol.DIRECTOR]