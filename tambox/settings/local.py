from .base import *

DEBUG = True
ALLOWED_HOSTS = []

# Database
# https://docs.djangoproject.com/en/1.8/ref/settings/#databases
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': 'tamboxd',
        'USER': 'tambox',
        'PASSWORD': 's0p0rt3ccpp',
        'HOST': '192.168.70.229',
        'PORT': '5432',
        'CHARSET': 'UTF8',
    },
}

STATIC_URL = '/static/'
STATICFILES_DIRS = (
    os.path.join(BASE_DIR, 'static'),
)

LOGIN_URL = '/'
MEDIA_URL = '/media/'