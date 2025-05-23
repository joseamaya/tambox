from .base import *

DEBUG = False
# TODO: Replace '*' with the actual production domain(s) for security.
ALLOWED_HOSTS = ['*']

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'tambox',
        'USER': 'tambox',
        'PASSWORD': 's0p0rt3ccpp',
        'HOST': 'localhost',
        'PORT': '5432',
        'CHARSET': 'UTF8',
    },
}

STATIC_URL = '/static/'
STATICFILES_DIRS = (
    os.path.join(BASE_DIR, 'static'),
)

# TODO: Fill in your actual domain(s).
CSRF_TRUSTED_ORIGINS = ['https://your_production_domain.com']

STATIC_ROOT = os.path.join('/home/inkarri/static')

LOGIN_URL = '/tambox'
MEDIA_URL = '/tambox/media/'
