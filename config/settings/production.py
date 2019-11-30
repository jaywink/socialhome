'''
Production Configurations
'''
from django.core.exceptions import ImproperlyConfigured

from .common import *  # noqa


# SECRET CONFIGURATION
# ------------------------------------------------------------------------------
# See: https://docs.djangoproject.com/en/dev/ref/settings/#secret-key
# Raises ImproperlyConfigured exception if DJANGO_SECRET_KEY not in os.environ
SECRET_KEY = env("DJANGO_SECRET_KEY")

# This ensures that Django will be able to detect a secure connection
# properly on Heroku.
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

# Production middleware
# ------------------------------------------------------------------------------
PRODUCTION_MIDDLEWARE = (
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
)

# set this to 60 seconds and then to 518400 when you can prove it works
SECURE_HSTS_SECONDS = 60
SECURE_HSTS_INCLUDE_SUBDOMAINS = env.bool(
    "DJANGO_SECURE_HSTS_INCLUDE_SUBDOMAINS", default=True)
SECURE_FRAME_DENY = env.bool("DJANGO_SECURE_FRAME_DENY", default=True)
SECURE_CONTENT_TYPE_NOSNIFF = env.bool(
    "DJANGO_SECURE_CONTENT_TYPE_NOSNIFF", default=True)
SECURE_BROWSER_XSS_FILTER = True
SESSION_COOKIE_SECURE = False
SESSION_COOKIE_HTTPONLY = True
SECURE_SSL_REDIRECT = env.bool("DJANGO_SECURE_SSL_REDIRECT", default=True)

# Make sure djangosecure.middleware.SecurityMiddleware is listed first
MIDDLEWARE = PRODUCTION_MIDDLEWARE + MIDDLEWARE

# Static Assets
# ------------------------
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'


# EMAIL
# ------------------------------------------------------------------------------
DEFAULT_FROM_EMAIL = env('DJANGO_DEFAULT_FROM_EMAIL',
                         default='Socialhome <noreply@socialhome.local>')
# Set this to "django.core.mail.backends.smtp.EmailBackend" for SMTP email sending
EMAIL_BACKEND = env("DJANGO_EMAIL_BACKEND", default="django.core.mail.backends.console.EmailBackend")
# Define these as necessary if using the SMTP backend
# See https://docs.djangoproject.com/en/1.10/topics/email/#smtp-backend
EMAIL_HOST = env("DJANGO_EMAIL_HOST", default="localhost")
EMAIL_PORT = env("DJANGO_EMAIL_PORT", default=587)
EMAIL_HOST_USER = env("DJANGO_EMAIL_HOST_USER", default="")
EMAIL_HOST_PASSWORD = env("DJANGO_EMAIL_HOST_PASSWORD", default="")
EMAIL_USE_TLS = env.bool("DJANGO_EMAIL_USE_TLS", default=True)
EMAIL_USE_SSL = env.bool("DJANGO_EMAIL_USE_SSL", default=False)
EMAIL_TIMEOUT = env("DJANGO_EMAIL_TIMEOUT", default=None)
EMAIL_SSL_KEYFILE = env("DJANGO_EMAIL_SSL_KEYFILE", default=None)
EMAIL_SSL_CERTFILE = env("DJANGO_EMAIL_SSL_CERTFILE", default=None)
EMAIL_SUBJECT_PREFIX = env("DJANGO_EMAIL_SUBJECT_PREFIX", default='[Socialhome] ')
SERVER_EMAIL = env('DJANGO_SERVER_EMAIL', default=DEFAULT_FROM_EMAIL)


# TEMPLATE CONFIGURATION
# ------------------------------------------------------------------------------
# See:
# https://docs.djangoproject.com/en/dev/ref/templates/api/#django.template.loaders.cached.Loader
TEMPLATES[0]['OPTIONS']['loaders'] = [
    ('django.template.loaders.cached.Loader', [
        'django.template.loaders.filesystem.Loader', 'django.template.loaders.app_directories.Loader', ]),
]

# CACHING
# ------------------------------------------------------------------------------
# Guard against old setting
redis_url = env('REDIS_URL', default=None)
if redis_url:
    raise ImproperlyConfigured("Setting REDIS_URL as an environment variable has been removed. Please define "
                               "REDIS_HOST, REDIS_PORT, REDIS_DB and/or "
                               "REDIS_PASSWORD. See docs for the defaults.")
CACHES = {
    "default": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": "redis://%s:%s/%s" % (REDIS_HOST, REDIS_PORT, REDIS_DB),
        "OPTIONS": {
            "CLIENT_CLASS": "django_redis.client.DefaultClient",
            "IGNORE_EXCEPTIONS": True,  # mimics memcache behavior.
                                        # http://niwinz.github.io/django-redis/latest/#_memcached_exceptions_behavior
            "PASSWORD": REDIS_PASSWORD,
        }
    }
}

# RQ
# --
RQ_QUEUES["default"]["USE_REDIS_CACHE"] = "default"

# VERSATILEIMAGEFIELD
# -------------------
VERSATILEIMAGEFIELD_SETTINGS = {
    "create_images_on_demand": False,
}

# SENTRY
# ------
# If you wish to configure Sentry for error reporting, first create your
# Sentry account and then place the DSN in `.env` as `SENTRY_DSN=dsnhere`.
if env('SENTRY_DSN', default=None):
    import raven
    INSTALLED_APPS += ('raven.contrib.django.raven_compat',)
    RAVEN_CONFIG = {
        'dsn': env('SENTRY_DSN'),
        'release': raven.fetch_git_sha(os.path.abspath(os.curdir)),
        'site': SOCIALHOME_DOMAIN,

    }
    LOGGING['handlers']['sentry'] = {
        'level': env('SENTRY_LEVEL', default='ERROR'),
        'class': 'raven.contrib.django.raven_compat.handlers.SentryHandler',
    }
    LOGGING['loggers']['socialhome']['handlers'].append('sentry')
    LOGGING['loggers']['federation']['handlers'].append('sentry')
    LOGGING['loggers']['rq_scheduler.scheduler']['handlers'].append('sentry')
    LOGGING['root'] = {
        'level': 'WARNING',
        'handlers': ['sentry', log_target],
    }
    LOGGING['loggers']['raven'] = {
        'level': 'DEBUG',
        'handlers': [log_target],
        'propagate': False,
    }
    LOGGING['loggers']['sentry.errors'] = {
        'level': 'DEBUG',
        'handlers': [log_target],
        'propagate': False,
    }

# SILK
# ----
if SILKY_INSTALLED:
    SILKY_AUTHENTICATION = True
    SILKY_AUTHORISATION = True
