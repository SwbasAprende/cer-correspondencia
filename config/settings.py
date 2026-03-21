"""
Configuración del Sistema de Correspondencia Institucional - CER
"""
import os
from dotenv import load_dotenv
load_dotenv()
from pathlib import Path
from decouple import config, Csv
import dj_database_url

BASE_DIR = Path(__file__).resolve().parent.parent

# ── Seguridad ────────────────────────────────────────────────────────────────
SECRET_KEY = config('SECRET_KEY')
DEBUG      = config('DEBUG', default=False, cast=bool)
ALLOWED_HOSTS = config('ALLOWED_HOSTS', default='*', cast=Csv())

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "usuarios",
    "correspondencia",
    "plantillas",
    "reportes",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "config.context_processors.cer_contexto",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"

# ── Base de datos ────────────────────────────────────────────────────────────
# En Railway usa PostgreSQL automáticamente, en local usa SQLite
DATABASE_URL = config('DATABASE_URL', default='')

if DATABASE_URL:
    DATABASES = {
        'default': dj_database_url.parse(DATABASE_URL, conn_max_age=600)
    }
else:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

AUTH_USER_MODEL       = "usuarios.Usuario"
LOGIN_URL             = "/login/"
LOGIN_REDIRECT_URL    = "/dashboard/"
LOGOUT_REDIRECT_URL   = "/login/"

LANGUAGE_CODE = "es-co"
TIME_ZONE     = "America/Bogota"
USE_I18N      = True
USE_TZ        = True

# ── Archivos estáticos ───────────────────────────────────────────────────────
STATIC_URL       = "/static/"
STATICFILES_DIRS = [BASE_DIR / "static"]
STATIC_ROOT      = BASE_DIR / "staticfiles"
STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"

MEDIA_URL  = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

# ── Seguridad en producción ──────────────────────────────────────────────────
if not DEBUG:
    SECURE_SSL_REDIRECT        = True
    SESSION_COOKIE_SECURE      = True
    CSRF_COOKIE_SECURE         = True
    SECURE_BROWSER_XSS_FILTER  = True
    SECURE_CONTENT_TYPE_NOSNIFF = True

# ── Configuración institucional CER ─────────────────────────────────────────
CER_CONFIG = {
    "nombre": "Centro de Estudios Regionales",
    "sigla": "CER",
    "nit": "000.000.000-0",
    "direccion": "Direccion del CER",
    "ciudad": "Colombia",
    "telefono": "",
    "email": "",
    "web": "",
    "version_sistema": "1.0.0",
    "tipos_documento": {
        "OF": "Oficio",
        "MM": "Memorando",
        "CR": "Circular",
        "RS": "Resolución",
        "AC": "Acta",
    },
    "dias_respuesta": {
        "normal": 15,
        "urgente": 5,
        "confidencial": 3,
    },
}

DATA_UPLOAD_MAX_MEMORY_SIZE    = 10485760
FILE_UPLOAD_MAX_MEMORY_SIZE    = 10485760

# ── Tipos de archivos permitidos en documentos (validación en validators.py) ──
# Validación por MIME type real + magic numbers, no solo extensión
ALLOWED_DOCUMENT_TYPES = [
    "application/pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",  # DOCX
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",  # XLSX
    "image/jpeg",
    "image/png",
]
ALLOWED_DOCUMENT_EXTENSIONS = [".pdf", ".docx", ".xlsx", ".jpg", ".jpeg", ".png"]

DEFAULT_AUTO_FIELD             = "django.db.models.BigAutoField"

# ─── CONFIGURACIÓN DE EMAIL ───────────────────────────────────────────────────
EMAIL_BACKEND       = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST          = 'smtp.gmail.com'
EMAIL_PORT          = 587
EMAIL_USE_TLS       = True
EMAIL_HOST_USER     = os.getenv('EMAIL_HOST_USER', '')
EMAIL_HOST_PASSWORD = os.getenv('EMAIL_HOST_PASSWORD', '')
DEFAULT_FROM_EMAIL  = f'Sistema CER <{os.getenv("EMAIL_HOST_USER", "")}>'