"""
Comando de verificación de configuración de producción.
Valida que todas las variables de entorno críticas estén configuradas correctamente.

Uso: python manage.py verificar_produccion
"""
from django.core.management.base import BaseCommand
from django.conf import settings
from django.db import connections
from django.db.utils import OperationalError
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Verifica que la configuración de producción sea segura y completa'

    def add_arguments(self, parser):
        parser.add_argument(
            '--fail-on-error',
            action='store_true',
            help='Termina con código de error si hay problemas',
        )

    def handle(self, *args, **options):
        self.stdout.write('\n' + '='*80)
        self.stdout.write(self.style.SUCCESS('🔍 VERIFICACIÓN DE CONFIGURACIÓN DE PRODUCCIÓN'))
        self.stdout.write('='*80 + '\n')

        checks = [
            ('DEBUG está en False', self._check_debug),
            ('SECRET_KEY es seguro', self._check_secret_key),
            ('DATABASE_URL está configurado', self._check_database_url),
            ('ALLOWED_HOSTS no contiene "*"', self._check_allowed_hosts),
            ('Conexión a BD funciona', self._check_database_connection),
            ('EMAIL configurado', self._check_email),
            ('Grupos base definidos', self._check_grupos_base),
            ('Existe al menos un superusuario', self._check_superuser_exists),
            ('Configuración de sesiones', self._check_session_config),
            ('Sentry configurado', self._check_sentry_config),
            ('HTTPS forzado', self._check_https_forzado),
            ('SECURE_SSL_REDIRECT está activo', self._check_ssl_redirect),
            ('CSRF_COOKIE_SECURE está activo', self._check_csrf_secure),
            ('SESSION_COOKIE_SECURE está activo', self._check_session_secure),
            ('HSTS está configurado', self._check_hsts),
        ]

        results = []
        fail_count = 0

        for check_name, check_func in checks:
            try:
                passed, message = check_func()
                status = '✅ PASS' if passed else '❌ FAIL'
                results.append((check_name, passed, message))
                
                if not passed:
                    fail_count += 1
                    self.stdout.write(
                        f'{status} | {check_name}\n'
                        f'        {message}\n'
                    )
                else:
                    self.stdout.write(
                        f'{status} | {check_name}'
                    )
            except Exception as e:
                results.append((check_name, False, str(e)))
                fail_count += 1
                self.stdout.write(
                    self.style.ERROR(
                        f'❌ ERROR | {check_name}\n'
                        f'         {str(e)}'
                    )
                )

        self.stdout.write('\n' + '='*80)
        passed_count = len([r for r in results if r[1]])
        total_count = len(results)
        
        if fail_count == 0:
            self.stdout.write(
                self.style.SUCCESS(
                    f'✅ TODAS LAS VERIFICACIONES PASARON ({passed_count}/{total_count})'
                )
            )
        else:
            self.stdout.write(
                self.style.ERROR(
                    f'❌ {fail_count} VERIFICACIONES FALLARON ({passed_count}/{total_count})'
                )
            )

        self.stdout.write('='*80 + '\n')

        if fail_count > 0 and options['fail_on_error']:
            raise SystemExit(1)

    def _check_debug(self):
        """Verifica que DEBUG esté en False"""
        if settings.DEBUG:
            return False, 'DEBUG debe estar en False en producción'
        return True, ''

    def _check_secret_key(self):
        """Verifica que SECRET_KEY no sea el default inseguro"""
        secret = settings.SECRET_KEY
        
        insecure_prefixes = [
            'django-insecure',
            'change-me',
            'changeme',
            'secret-key',
            'secretkey',
        ]
        
        if any(secret.lower().startswith(p) for p in insecure_prefixes):
            return False, 'SECRET_KEY tiene valor por defecto inseguro'
        
        if len(secret) < 50:
            return False, f'SECRET_KEY debe tener al menos 50 caracteres (tiene {len(secret)})'
        
        return True, ''

    def _check_database_url(self):
        """Verifica que DATABASE_URL esté configurado"""
        db_url = getattr(settings, 'DATABASE_URL', '')
        
        if not db_url:
            # En desarrollo puede estar vacío (usaría SQLite), pero en producción no
            if not settings.DEBUG:
                return False, 'DATABASE_URL debe estar configurado en producción'
            return True, 'DATABASE_URL no configurado (usando SQLite local)'
        
        return True, ''

    def _check_allowed_hosts(self):
        """Verifica que ALLOWED_HOSTS no contenga '*'"""
        if '*' in settings.ALLOWED_HOSTS:
            return False, 'ALLOWED_HOSTS contiene "*" — especifica los hosts permitidos'
        
        if not settings.ALLOWED_HOSTS:
            return False, 'ALLOWED_HOSTS está vacío'
        
        return True, f'Hosts configurados: {", ".join(settings.ALLOWED_HOSTS[:3])}'

    def _check_database_connection(self):
        """Verifica que la conexión a la BD funcione"""
        try:
            db = connections['default']
            db.ensure_connection()
            return True, 'Conexión establida exitosamente'
        except OperationalError as e:
            return False, f'No se puede conectar a la BD: {str(e)[:80]}'
        except Exception as e:
            return False, f'Error verificando BD: {str(e)[:80]}'

    def _check_email(self):
        """Verifica que EMAIL esté configurado"""
        host_user = settings.EMAIL_HOST_USER
        host_password = settings.EMAIL_HOST_PASSWORD
        
        if not host_user or not host_password:
            if settings.DEBUG:
                return True, 'EMAIL no configurado (modo console en DEBUG)'
            return False, 'EMAIL_HOST_USER y EMAIL_HOST_PASSWORD deben estar configurados'
        
        return True, f'Configurado para {host_user}'

    def _check_ssl_redirect(self):
        """Verifica que SECURE_SSL_REDIRECT esté activo"""
        if settings.DEBUG:
            return True, 'Deshabilitado en DEBUG'
        
        if not getattr(settings, 'SECURE_SSL_REDIRECT', False):
            return False, 'SECURE_SSL_REDIRECT debe estar en True en producción'
        
        return True, ''

    def _check_csrf_secure(self):
        """Verifica que CSRF_COOKIE_SECURE esté activo"""
        if settings.DEBUG:
            return True, 'Deshabilitado en DEBUG'
        
        if not getattr(settings, 'CSRF_COOKIE_SECURE', False):
            return False, 'CSRF_COOKIE_SECURE debe estar en True en producción'
        
        return True, ''

    def _check_session_secure(self):
        """Verifica que SESSION_COOKIE_SECURE esté activo"""
        if settings.DEBUG:
            return True, 'Deshabilitado en DEBUG'
        
        if not getattr(settings, 'SESSION_COOKIE_SECURE', False):
            return False, 'SESSION_COOKIE_SECURE debe estar en True en producción'
        
        return True, ''

    def _check_hsts(self):
        """Verifica que HSTS esté configurado"""
        if settings.DEBUG:
            return True, 'Deshabilitado en DEBUG'
        
        hsts_seconds = getattr(settings, 'SECURE_HSTS_SECONDS', 0)
        
        if hsts_seconds == 0:
            return False, 'SECURE_HSTS_SECONDS debe ser > 0 en producción'
        
        return True, f'HSTS habilitado por {hsts_seconds} segundos'

    def _check_grupos_base(self):
        """Verifica que existan los grupos de rol básicos"""
        target = {'Administrador', 'Radicador', 'Consultor', 'Solo lectura'}
        existing = set(Group.objects.filter(name__in=target).values_list('name', flat=True))
        missing = target - existing
        if missing:
            return False, f'Faltan grupos: {", ".join(sorted(missing))}'
        return True, f'Grupos válidos: {", ".join(sorted(existing))}'

    def _check_superuser_exists(self):
        """Verifica que exista al menos un superusuario"""
        User = get_user_model()
        if not User.objects.filter(is_superuser=True, is_active=True).exists():
            return False, 'No existe un superusuario activo'
        return True, 'Existe al menos un superusuario activo'

    def _check_session_config(self):
        """Verifica configuración de sesiones"""
        if getattr(settings, 'SESSION_COOKIE_AGE', None) != 28800:
            return False, f'SESSION_COOKIE_AGE debe ser 28800, actual {getattr(settings, "SESSION_COOKIE_AGE", None)}'
        if not getattr(settings, 'SESSION_EXPIRE_AT_BROWSER_CLOSE', False):
            return False, 'SESSION_EXPIRE_AT_BROWSER_CLOSE debe estar en True'
        return True, 'Sesiones configuradas correctamente'

    def _check_sentry_config(self):
        """Verifica que Sentry esté configurado"""
        dsn = getattr(settings, 'SENTRY_DSN', '')
        if not dsn:
            return True, 'SENTRY_DSN no configurado (warning, se recomienda establecerlo).'
        return True, 'Sentry configurado'

    def _check_https_forzado(self):
        """Verifica que HTTPS esté forzado"""
        if settings.DEBUG:
            return True, 'Deshabilitado en DEBUG'
        if not getattr(settings, 'SECURE_SSL_REDIRECT', False):
            return False, 'SECURE_SSL_REDIRECT debe ser True en producción'
        if not getattr(settings, 'CSRF_COOKIE_SECURE', False):
            return False, 'CSRF_COOKIE_SECURE debe ser True en producción'
        if not getattr(settings, 'SESSION_COOKIE_SECURE', False):
            return False, 'SESSION_COOKIE_SECURE debe ser True en producción'
        return True, 'HTTPS forzado correctamente'

