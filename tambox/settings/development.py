from .base import *

DEBUG = True

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
