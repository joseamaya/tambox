from .base import *

DEBUG = True
ALLOWED_HOSTS = []

# Database
# https://docs.djangoproject.com/en/1.8/ref/settings/#databases
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': 'tambox',
        'USER': 'oliver',
        'PASSWORD': 'yugiho2000',
        'HOST': 'localhost',
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
