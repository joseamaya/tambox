import sys

from .base import *

DEBUG = True

# Los tests crean datos a medida y no completan el wizard, asi que el bloqueo se
# desactiva al correr la suite. El middleware se prueba aparte, activandolo con
# `override_settings(SETUP_WIZARD_ENFORCED=True)`.
if 'test' in sys.argv:
    SETUP_WIZARD_ENFORCED = False

ALLOWED_HOSTS = ['*']

SECRET_KEY = SECRET_KEY or 'dev-insecure-secret-key'

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
