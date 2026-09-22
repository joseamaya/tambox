import os

import dj_database_url

from .base import *

DEBUG = False

ALLOWED_HOSTS = [host.strip() for host in os.environ.get('ALLOWED_HOSTS', '').split(',') if host.strip()]

CSRF_TRUSTED_ORIGINS = [origen.strip() for origen in os.environ.get('CSRF_TRUSTED_ORIGINS', '').split(',')
                        if origen.strip()]

if os.environ.get('DATABASE_URL'):
    DATABASES = {
        'default': dj_database_url.config(conn_max_age=600, ssl_require=True),
    }
else:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': os.environ.get('DB_NAME', 'tambox'),
            'USER': os.environ.get('DB_USER', 'tambox'),
            'PASSWORD': os.environ.get('DB_PASSWORD', ''),
            'HOST': os.environ.get('DB_HOST', 'localhost'),
            'PORT': os.environ.get('DB_PORT', '5432'),
            'CHARSET': 'UTF8',
        },
    }

SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

# El sitio va detras de un proxy que termina el TLS (ver SECURE_PROXY_SSL_HEADER),
# asi que la app siempre ve HTTPS y puede forzar cookies seguras. HSTS se activa
# aparte, con `SECURE_HSTS_SECONDS`, porque es dificil de revertir.
SECURE_SSL_REDIRECT = os.environ.get('SECURE_SSL_REDIRECT', 'true').lower() == 'true'

SESSION_COOKIE_SECURE = True

CSRF_COOKIE_SECURE = True

SECURE_HSTS_SECONDS = int(os.environ.get('SECURE_HSTS_SECONDS', '0'))

SECURE_HSTS_INCLUDE_SUBDOMAINS = SECURE_HSTS_SECONDS > 0

SECURE_HSTS_PRELOAD = SECURE_HSTS_SECONDS > 0

MIDDLEWARE = MIDDLEWARE + (
    'whitenoise.middleware.WhiteNoiseMiddleware',
)

STATIC_ROOT = BASE_DIR / 'staticfiles'

STORAGES = {
    'default': {
        'BACKEND': 'django.core.files.storage.FileSystemStorage',
    },
    'staticfiles': {
        'BACKEND': 'whitenoise.storage.CompressedManifestStaticFilesStorage',
    },
}
