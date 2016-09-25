from .base import *
DEBUG = False
ALLOWED_HOSTS = ['*']

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': 'tambox',
        'USER': 'tambox',
        'PASSWORD': 's0p0rt3ccpp',
        'HOST': 'localhost',
        'PORT': '5432',
        'CHARSET': 'UTF8',
    },
}

STATIC_ROOT = os.path.join('/home/inkarri/static')

LOGIN_URL = '/tambox'
MEDIA_URL = '/tambox/media/'