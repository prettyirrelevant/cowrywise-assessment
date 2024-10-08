"""
Django settings for librarian project.

Generated by 'django-admin startproject' using Django 5.1.1.

For more information on this file, see
https://docs.djangoproject.com/en/5.1/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/5.1/ref/settings/
"""

from pathlib import Path

from environs import Env

from bookcourier import BookCourier

BASE_DIR = Path(__file__).resolve().parent.parent

env = Env()

# ==============================================================================
# CORE SETTINGS
# See https://docs.djangoproject.com/en/4.2/howto/deployment/checklist/
# ==============================================================================
DEBUG = env.bool('DEBUG', True)
if DEBUG:
    env.read_env(BASE_DIR / '.env')

SECRET_KEY = env.str('LIBRARIAN_SECRET_KEY')

ALLOWED_HOSTS = env.list('LIBRARIAN_ALLOWED_HOSTS', default=[]) if DEBUG else env.list('LIBRARIAN_ALLOWED_HOSTS')

DJANGO_APPS = [
    'django.contrib.auth',
    'django.contrib.admin',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.contenttypes',
]
if DEBUG:
    DJANGO_APPS.insert(5, 'whitenoise.runserver_nostatic')

THIRD_PARTY_APPS = [
    'drf_yasg',
    'rest_framework',
]

LOCAL_APPS = ['librarian.apps.books', 'librarian.apps.users']

INSTALLED_APPS = DJANGO_APPS + THIRD_PARTY_APPS + LOCAL_APPS

WSGI_APPLICATION = 'conf.wsgi.application'

ROOT_URLCONF = 'conf.urls'

# ==============================================================================
# MIDDLEWARE SETTINGS
# https://docs.djangoproject.com/en/4.2/topics/http/middleware/
# https://docs.djangoproject.com/en/4.2/ref/middleware/
# ==============================================================================
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

# ==============================================================================
# TEMPLATES SETTINGS
# ==============================================================================
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

# ==============================================================================
# STORAGES SETTINGS
# ==============================================================================
STORAGES = {'staticfiles': {'BACKEND': 'whitenoise.storage.CompressedManifestStaticFilesStorage'}}

# ==============================================================================
# DATABASES SETTINGS
# https://docs.djangoproject.com/en/4.2/ref/settings/#databases
# https://docs.djangoproject.com/en/4.2/ref/settings/#default-auto-field
# ==============================================================================
DATABASES = {'default': env.dj_db_url('LIBRARIAN_DATABASE_URL')}

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# ==============================================================================
# PASSWORD VALIDATION SETTINGS
# https://docs.djangoproject.com/en/4.2/ref/settings/#auth-password-validators
# ==============================================================================
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# ==============================================================================
# I18N AND L10N SETTINGS
# https://docs.djangoproject.com/en/4.2/topics/i18n/
# ==============================================================================
LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_TZ = True

# ==============================================================================
# STATIC FILES SETTINGS
# https://docs.djangoproject.com/en/4.2/howto/static-files/
# ==============================================================================
STATIC_URL = 'static/'

STATIC_ROOT = BASE_DIR / 'staticfiles'

# ==============================================================================
# SECURITY
# ==============================================================================
SESSION_COOKIE_HTTPONLY = True

SESSION_COOKIE_SECURE = not DEBUG

CSRF_COOKIE_HTTPONLY = True

CSRF_COOKIE_SECURE = not DEBUG

SECURE_BROWSER_XSS_FILTER = True

X_FRAME_OPTIONS = 'DENY'

# ==============================================================================
# CACHING
# ==============================================================================
# CACHES = {'default': env.dj_cache_url('CACHE_URL')}

# ==============================================================================
# DRF-YASG SETTINGS
# ==============================================================================
SWAGGER_SETTINGS = {'SECURITY_DEFINITIONS': {'Bearer': {'type': 'apiKey', 'name': 'Authorization', 'in': 'header'}}}

# ==============================================================================
# DJANGO REST FRAMEWORK SETTINGS
# ==============================================================================
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': ['librarian.common.authentication.JWTAuthentication'],
    'EXCEPTION_HANDLER': 'librarian.common.exceptions.custom_exception_handler',
    'DEFAULT_PERMISSION_CLASSES': ['librarian.apps.books.permissions.IsAdmin'],
    'DEFAULT_RENDERER_CLASSES': ['rest_framework.renderers.JSONRenderer'],
    # 'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    # 'PAGE_SIZE': 50,
}
if DEBUG:
    REST_FRAMEWORK['DEFAULT_RENDERER_CLASSES'].append('rest_framework.renderers.BrowsableAPIRenderer')

# ==============================================================================
# DJANGO CORS HEADERS SETTINGS
# ==============================================================================
CORS_ALLOW_ALL_ORIGINS = True

# ==============================================================================
# PAGEKEEPER SETTINGS
# ==============================================================================
AUTHENTICATION_SERVER_URL = env.str('LIBRARIAN_AUTHENTICATION_SERVER_URL')

# ==============================================================================
# BOOKCOURIER SETTINGS
# ==============================================================================
BOOKCOURIER = BookCourier(env.str('LIBRARIAN_RABBITMQ_URL'))

# ==============================================================================
# LOGGING SETTINGS
# ==============================================================================
if not DEBUG:
    LOGGING = {
        'version': 1,
        'disable_existing_loggers': False,
        'formatters': {
            'verbose': {'format': '[%(asctime)s] %(levelname)s:%(name)s:%(process)d:%(threadName)s: %(message)s'},
        },
        'handlers': {
            'console': {
                'level': 'INFO',
                'class': 'logging.StreamHandler',
                'formatter': 'verbose',
            }
        },
        'root': {'level': 'INFO', 'handlers': ['console']},
        'loggers': {
            'django.request': {
                'handlers': ['console'],
                'level': 'ERROR',
                'propagate': False,
            },
            'django.security.DisallowedHost': {
                'level': 'ERROR',
                'handlers': ['console'],
                'propagate': False,
            },
        },
    }
