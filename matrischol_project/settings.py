import os
import dj_database_url

from pathlib import Path

try:
    from dotenv import load_dotenv  # python-dotenv
    load_dotenv()  # carga variables de entorno desde .env si existe
except ImportError:
    load_dotenv = None

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent
if load_dotenv:
    load_dotenv(BASE_DIR / '.env')  # carga variables si existe .env
else:
    # Intentar cargar .env manualmente si python-dotenv no está instalado.
    env_path = BASE_DIR / '.env'
    if env_path.exists():
        try:
            with open(env_path, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith('#'):
                        continue
                    if '=' not in line:
                        continue
                    key, val = line.split('=', 1)
                    key = key.strip()
                    val = val.strip().strip('"').strip("'")
                    # No sobreescribir variables ya definidas en el entorno
                    if key not in os.environ:
                        os.environ[key] = val
        except Exception:
            pass

SECRET_KEY = os.environ.get("SECRET_KEY")

# Permite forzar DEBUG vía variable; en Render se apaga por defecto.
DEBUG = os.environ.get("DEBUG", "False").lower() == "true"

ALLOWED_HOSTS = os.environ.get("ALLOWED_HOSTS", "localhost 127.0.0.1").split(" ")

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'cloudinary_storage',
    'cloudinary',
    'accounts',
    'people',
    'school',
    'communications',
    'adminpanel',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'matrischol_project.middleware.NoCacheForAuthPagesMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'matrischol_project.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'accounts.context_processors.current_registro',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'matrischol_project.wsgi.application'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

DATABASE_URL = os.environ.get('DATABASE_URL')
if DATABASE_URL:
    DATABASES['default'] = dj_database_url.parse(DATABASE_URL, conn_max_age=300)

# 

# Password validation (kept default)
AUTH_PASSWORD_VALIDATORS = []

LANGUAGE_CODE = 'es'

TIME_ZONE = 'UTC'

USE_I18N = True

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

USE_TZ = True

STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'

# Static files (CSS, JavaScript, Images)
STATICFILES_DIRS = [
    BASE_DIR / 'static',
]

# WhiteNoise: servir estáticos comprimidos y con manifest en producción
STORAGES = {
    "default": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
    },
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
    },
}


# Media (uploads)
MEDIA_URL = '/media/'
if ENVIROMENT == "development":
    MEDIA_ROOT = BASE_DIR / 'media'
else:
    DEFAULT_FILE_STORAGE = 'cloudinary_storage.storage.MediaCloudinaryStorage'
    CLOUDINARY_STORAGE = {
        'CLOUDINARY_URL': os.getenv('CLOUDINARY_URL'),
    }    

# =====================
# SITE_URL para enlaces en correos y frontend
SITE_URL = os.getenv('SITE_URL', 'http://127.0.0.1:8000')

# =====================
# Email configuration
# Loaded from environment variables to evitar exponer credenciales.
# En entorno local puedes usar django.core.mail.backends.console.EmailBackend
# En producción define SMTP o proveedor transaccional.
# Variables esperadas:
# EMAIL_BACKEND, EMAIL_HOST, EMAIL_PORT, EMAIL_HOST_USER, EMAIL_HOST_PASSWORD,
# EMAIL_USE_TLS, EMAIL_USE_SSL, DEFAULT_FROM_EMAIL

EMAIL_BACKEND = os.getenv("EMAIL_BACKEND", "django.core.mail.backends.smtp.EmailBackend")
EMAIL_HOST = os.getenv('EMAIL_HOST', '')
EMAIL_PORT = int(os.getenv('EMAIL_PORT', '587'))
EMAIL_HOST_USER = os.getenv('EMAIL_HOST_USER', '')
EMAIL_HOST_PASSWORD = os.getenv('EMAIL_HOST_PASSWORD', '')
EMAIL_USE_TLS = os.getenv('EMAIL_USE_TLS', 'True') == 'True'
EMAIL_USE_SSL = os.getenv('EMAIL_USE_SSL', 'False') == 'True'
DEFAULT_FROM_EMAIL = os.getenv('DEFAULT_FROM_EMAIL', EMAIL_HOST_USER or 'no-reply@example.com')
EMAIL_TIMEOUT = int(os.getenv('EMAIL_TIMEOUT', '10'))

# Evitar configuración inválida (TLS y SSL a la vez)
if EMAIL_USE_TLS and EMAIL_USE_SSL:
    raise ValueError('Config: No puedes habilitar TLS y SSL simultáneamente. Ajusta variables de entorno.')

# Failover simple: si se forzó SMTP pero no hay host, vuelve a consola
if EMAIL_BACKEND == 'django.core.mail.backends.smtp.EmailBackend' and not EMAIL_HOST:
    EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# Respeto a cabeceras de proxy (Render) y cookies seguras en producción
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
USE_X_FORWARDED_HOST = True
if not DEBUG:
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    # Puedes habilitar HSTS cuando confirmes HTTPS estable en tu dominio
    # SECURE_HSTS_SECONDS = 31536000
    # SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    # SECURE_HSTS_PRELOAD = True

