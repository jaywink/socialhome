# -*- coding: utf-8 -*-
"""
Django settings for Socialhome project.

For more information on this file, see
https://docs.djangoproject.com/en/dev/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/dev/ref/settings/
"""
from datetime import datetime

import environ

ROOT_DIR = environ.Path(__file__) - 3  # (/a/b/myfile.py - 3 = /)
APPS_DIR = ROOT_DIR.path("socialhome")

# Local environment
# -----------------
env = environ.Env()
env.read_env("env.local")

# APP CONFIGURATION
# ------------------------------------------------------------------------------
DJANGO_APPS = (
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.sites",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.admin",
    "django.contrib.postgres",
)
THIRD_PARTY_APPS = (
    "crispy_forms",
    "allauth",
    "allauth.account",
    "allauth.socialaccount",
    "markdownx",
    "django_extensions",
    "channels",
    "django_rq",
    "rest_framework",
    "rest_framework.authtoken",
    "dynamic_preferences",
    "dynamic_preferences.users.apps.UserPreferencesConfig",
    "django_tables2",
)
LOCAL_APPS = (
    "socialhome",
    "socialhome.users",
    "socialhome.federate",
    "socialhome.content",
    "socialhome.streams",
    "socialhome.search",
)

INSTALLED_APPS = DJANGO_APPS + THIRD_PARTY_APPS + LOCAL_APPS

# MIDDLEWARE CONFIGURATION
# ------------------------------------------------------------------------------
MIDDLEWARE_CLASSES = (
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.middleware.locale.LocaleMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "django.contrib.sites.middleware.CurrentSiteMiddleware",
)

# MIGRATIONS CONFIGURATION
# ------------------------------------------------------------------------------
MIGRATION_MODULES = {
    "sites": "socialhome.contrib.sites.migrations"
}

# DEBUG
# ------------------------------------------------------------------------------
# See: https://docs.djangoproject.com/en/dev/ref/settings/#debug
DEBUG = env.bool("DJANGO_DEBUG", False)
DEBUG_TOOLBAR_ENABLED = False

# FIXTURE CONFIGURATION
# ------------------------------------------------------------------------------
# See: https://docs.djangoproject.com/en/dev/ref/settings/#std:setting-FIXTURE_DIRS
FIXTURE_DIRS = (
    str(APPS_DIR.path("fixtures")),
)

# MANAGER CONFIGURATION
# ------------------------------------------------------------------------------
# See: https://docs.djangoproject.com/en/dev/ref/settings/#admins
ADMINS = (
    (env("DJANGO_ADMIN_NAME", default="Socialhome Admin"),
     env("DJANGO_ADMIN_MAIL", default="info@socialhome.local")),
)

# See: https://docs.djangoproject.com/en/dev/ref/settings/#managers
MANAGERS = ADMINS

# DATABASE CONFIGURATION
# ------------------------------------------------------------------------------
# See: https://docs.djangoproject.com/en/dev/ref/settings/#databases
DATABASES = {
    "default": env.db("DATABASE_URL", default="postgres:///socialhome"),
}
DATABASES["default"]["ATOMIC_REQUESTS"] = True


# GENERAL CONFIGURATION
# ------------------------------------------------------------------------------
# Local time zone for this installation. Choices can be found here:
# http://en.wikipedia.org/wiki/List_of_tz_zones_by_name
# although not all choices may be available on all operating systems.
# In a Windows environment this must be set to your system time zone.
TIME_ZONE = "UTC"

# See: https://docs.djangoproject.com/en/dev/ref/settings/#language-code
LANGUAGE_CODE = "en-us"

# See: https://docs.djangoproject.com/en/dev/ref/settings/#site-id
SITE_ID = 1

# See: https://docs.djangoproject.com/en/dev/ref/settings/#use-i18n
USE_I18N = True

# See: https://docs.djangoproject.com/en/dev/ref/settings/#use-l10n
USE_L10N = True

# See: https://docs.djangoproject.com/en/dev/ref/settings/#use-tz
USE_TZ = True

# TEMPLATE CONFIGURATION
# ------------------------------------------------------------------------------
# See: https://docs.djangoproject.com/en/dev/ref/settings/#templates
TEMPLATES = [
    {
        # See: https://docs.djangoproject.com/en/dev/ref/settings/#std:setting-TEMPLATES-BACKEND
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        # See: https://docs.djangoproject.com/en/dev/ref/settings/#template-dirs
        "DIRS": [
            str(APPS_DIR.path("templates")),
        ],
        "OPTIONS": {
            # See: https://docs.djangoproject.com/en/dev/ref/settings/#template-debug
            "debug": DEBUG,
            # See: https://docs.djangoproject.com/en/dev/ref/settings/#template-loaders
            # https://docs.djangoproject.com/en/dev/ref/templates/api/#loader-types
            "loaders": [
                "django.template.loaders.filesystem.Loader",
                "django.template.loaders.app_directories.Loader",
            ],
            # See: https://docs.djangoproject.com/en/dev/ref/settings/#template-context-processors
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.template.context_processors.i18n",
                "django.template.context_processors.media",
                "django.template.context_processors.static",
                "django.template.context_processors.tz",
                "django.contrib.messages.context_processors.messages",
                "django_settings_export.settings_export",
            ],
        },
    },
]

SETTINGS_EXPORT = [
    "ACCOUNT_ALLOW_REGISTRATION",
]

# See: http://django-crispy-forms.readthedocs.org/en/latest/install.html#template-packs
CRISPY_TEMPLATE_PACK = "bootstrap3"

# STATIC FILE CONFIGURATION
# ------------------------------------------------------------------------------
# See: https://docs.djangoproject.com/en/dev/ref/settings/#static-root
STATIC_ROOT = str(ROOT_DIR("staticfiles"))

# See: https://docs.djangoproject.com/en/dev/ref/settings/#static-url
STATIC_URL = "/static/"

# See: https://docs.djangoproject.com/en/dev/ref/contrib/staticfiles/#std:setting-STATICFILES_DIRS
STATICFILES_DIRS = (
    str(APPS_DIR.path("static")),
)

# See: https://docs.djangoproject.com/en/dev/ref/contrib/staticfiles/#staticfiles-finders
STATICFILES_FINDERS = (
    "django.contrib.staticfiles.finders.FileSystemFinder",
    "django.contrib.staticfiles.finders.AppDirectoriesFinder",
)

# MEDIA CONFIGURATION
# ------------------------------------------------------------------------------
# See: https://docs.djangoproject.com/en/dev/ref/settings/#media-root
MEDIA_ROOT = str(APPS_DIR("media"))

# See: https://docs.djangoproject.com/en/dev/ref/settings/#media-url
MEDIA_URL = "/media/"

# URL Configuration
# ------------------------------------------------------------------------------
ROOT_URLCONF = "config.urls"

# See: https://docs.djangoproject.com/en/dev/ref/settings/#wsgi-application
WSGI_APPLICATION = "config.wsgi.application"

# AUTHENTICATION CONFIGURATION
# ------------------------------------------------------------------------------
AUTHENTICATION_BACKENDS = (
    "django.contrib.auth.backends.ModelBackend",
    "allauth.account.auth_backends.AuthenticationBackend",
)

# Some really nice defaults
ACCOUNT_AUTHENTICATION_METHOD = "username"
ACCOUNT_EMAIL_REQUIRED = True
ACCOUNT_EMAIL_VERIFICATION = "mandatory"

ACCOUNT_ALLOW_REGISTRATION = env.bool("DJANGO_ACCOUNT_ALLOW_REGISTRATION", True)
ACCOUNT_ADAPTER = "socialhome.users.adapters.AccountAdapter"
ACCOUNT_PRESERVE_USERNAME_CASING = False
SOCIALACCOUNT_ADAPTER = "socialhome.users.adapters.SocialAccountAdapter"

# Select the correct user model
AUTH_USER_MODEL = "users.User"
LOGIN_REDIRECT_URL = "home"
LOGIN_URL = "account_login"

# SLUGLIFIER
AUTOSLUG_SLUGIFY_FUNCTION = "slugify.slugify"

# REDIS
# -----
REDIS_HOST = env("REDIS_HOST", default="localhost")
REDIS_PORT = env("REDIS_PORT", default=6379)
REDIS_DB = env("REDIS_DB", default=0)
REDIS_PASSWORD = env("REDIS_PASSWORD", default="")

# RQ
# --
RQ_QUEUES = {
    "default": {
        "HOST": REDIS_HOST,
        "PORT": REDIS_PORT,
        "DB": REDIS_DB,
        "PASSWORD": REDIS_PASSWORD,
        "DEFAULT_TIMEOUT": 360,
    },
}
RQ_SHOW_ADMIN_LINK = True

# Location of root django.contrib.admin URL, use {% url "admin:index" %}
ADMIN_URL = r"^admin/"

# SITE CONFIGURATION
# ------------------------------------------------------------------------------
# Hosts/domain names that are valid for this site
# See https://docs.djangoproject.com/en/1.6/ref/settings/#allowed-hosts
ALLOWED_HOSTS = env.list("DJANGO_ALLOWED_HOSTS", default=["socialhome.local"])

# SOCIALHOME
# ------------------------------------------------------------------------------
SOCIALHOME_DOMAIN = env("SOCIALHOME_DOMAIN", default="socialhome.local")
# Whether to automatically generate an RSA key pair for local users on save
# We need this setting so we can turn it off in tests that don"t test this feature
# Otherwise the whole test suite becomes slooooow.
SOCIALHOME_GENERATE_USER_RSA_KEYS_ON_SAVE = True
SOCIALHOME_HTTPS = env.bool("SOCIALHOME_HTTPS", True)
# Username of profile living at root ie "/"
# Instead of normal site landing page, this user profile will be shown.
# This only makes sense on single user sites.
SOCIALHOME_ROOT_PROFILE = env("SOCIALHOME_ROOT_PROFILE", default=None)
# A full url with protocol
SOCIALHOME_URL = "{protocol}://{domain}".format(
    protocol="https" if SOCIALHOME_HTTPS else "http",
    domain=SOCIALHOME_DOMAIN
)
# Relay to send public content to
SOCIALHOME_RELAY_DOMAIN = env("SOCIALHOME_RELAY_DOMAIN", default="relay.iliketoast.net")

# CHANNELS
# --------
# http://channels.readthedocs.org/en/latest/deploying.html#setting-up-a-channel-backend
CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "asgi_redis.RedisChannelLayer",
        "CONFIG": {
            "hosts": [
                "redis://%s:%s/%s" % (REDIS_HOST, REDIS_PORT, REDIS_DB)
            ],
        },
        "ROUTING": "config.routing.channel_routing",
    },
}

# MOCHA
# -----
MOCHA_TESTS = False

# MARKDOWN
# --------
MARKDOWNX_MARKDOWNIFY_FUNCTION = "CommonMark.commonmark"
MARKDOWNX_MEDIA_PATH = datetime.now().strftime("markdownx/%Y/%m/%d")
MARKDOWNX_IMAGE_MAX_SIZE = {
    "size": (2048, 2048),
    "quality": 90,
}

# LOGGING CONFIGURATION
# ------------------------------------------------------------------------------
# See: https://docs.djangoproject.com/en/dev/ref/settings/#logging
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "filters": {
        "require_debug_false": {
            "()": "django.utils.log.RequireDebugFalse"
        }
    },
    "formatters": {
        "verbose": {
            "format": "%(levelname)s %(asctime)s %(module)s "
                      "%(process)d %(thread)d %(message)s"
        },
    },
    "handlers": {
        "mail_admins": {
            "level": "ERROR",
            "filters": ["require_debug_false"],
            "class": "django.utils.log.AdminEmailHandler"
        },
        "console": {
            "level": "DEBUG",
            "class": "logging.StreamHandler",
            "formatter": "verbose",
        },
        "application_file": {
            "filename": env("SOCIALHOME_LOGFILE", default="/tmp/socialhome.log"),
            "level": "DEBUG",
            "class": "logging.handlers.RotatingFileHandler",
            "formatter": "verbose",
            "maxBytes": 10485760,  # 10mb
            "backupCount": 10,
        },
        "federation_file": {
            "filename": env("SOCIALHOME_LOGFILE_FEDERATION", default="/tmp/socialhome-federation.log"),
            "level": "DEBUG",
            "class": "logging.handlers.RotatingFileHandler",
            "formatter": "verbose",
            "maxBytes": 10485760,  # 10mb
            "backupCount": 10,
        },
    },
    "loggers": {
        "django.request": {
            "handlers": ["application_file"],
            "level": "ERROR",
            "propagate": True
        },
        "django.security.DisallowedHost": {
            "level": "ERROR",
            "handlers": ["console", "application_file"],
            "propagate": True
        },
        "socialhome": {
            "level": "DEBUG",
            "handlers": ["application_file"],
            "propagate": True
        },
        "federation": {
            "level": "DEBUG",
            "handlers": ["federation_file"],
            "propagate": False,
        },
    }
}

# REST FRAMEWORK
# --------------
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework.authentication.SessionAuthentication",
        "rest_framework.authentication.TokenAuthentication",
    ),
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    "PAGE_SIZE": 100,
    "DEFAULT_THROTTLE_CLASSES": (
        "rest_framework.throttling.AnonRateThrottle",
        "rest_framework.throttling.UserRateThrottle",
    ),
    "DEFAULT_THROTTLE_RATES": {
        "anon": "30/minute",
        "user": "30/minute",
    },
    "DEFAULT_VERSION": "0.1",
}

# DYNAMIC PREFERENCES
# -------------------
DYNAMIC_PREFERENCES = {
    # The python module in which registered preferences will be searched within each app
    "REGISTRY_MODULE": "preferences",

    # Use this to disable caching of preference. This can be useful to debug things
    "ENABLE_CACHE": True,

    # Use this to disable checking preferences names. This can be useful to debug things
    "VALIDATE_NAMES": True,
}
