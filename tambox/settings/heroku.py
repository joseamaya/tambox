from .base import *
import dj_database_url

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEBUG = False
# TODO: Replace '*' with the actual Heroku domain(s) for security.
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

db_from_env = dj_database_url.config(conn_max_age=500)
DATABASES['default'].update(db_from_env)

# Honor the 'X-Forwarded-Proto' header for request.is_secure()
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/1.8/howto/static-files/

STATIC_ROOT = os.path.join(PROJECT_ROOT, 'staticfiles')

STATIC_URL = '/static/'

# Extra places for collectstatic to find static files.
STATICFILES_DIRS = (
    os.path.join(BASE_DIR, 'static'),
)

# TODO: Fill in your actual domain(s).
CSRF_TRUSTED_ORIGINS = ['https://your_heroku_app_name.herokuapp.com']

STORAGES["staticfiles"]["BACKEND"] = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

LOGIN_URL = '/tambox'
MEDIA_URL = '/tambox/media/'
