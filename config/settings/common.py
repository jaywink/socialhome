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
import os
import warnings

ROOT_DIR = environ.Path(__file__) - 3  # (/a/b/myfile.py - 3 = /)
APPS_DIR = ROOT_DIR.path("socialhome")

# Local environment
# -----------------
env = environ.Env()

if os.path.isfile(".env"):
    env.read_env(".env")
else:
    if os.path.isfile("env.local"):
        warnings.warn("!!! 'env.local' file has been replaced by '.env'. Please rename the file!")
        env.read_env("env.local")
    else:
        warnings.warn("!!! No .env file found!")

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
    "django.forms",  # Required by FORM_RENDERER = TemplatesSetting
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
    "rest_framework_swagger",
    "dynamic_preferences",
    "dynamic_preferences.users.apps.UserPreferencesConfig",
    "django_tables2",
    "haystack",
    "versatileimagefield",
    "django_js_reverse",
    "memoize",
    "robots",
    "reversion",
)
LOCAL_APPS = (
    "socialhome",
    "socialhome.users",
    "socialhome.federate",
    "socialhome.content",
    "socialhome.notifications",
    "socialhome.streams",
    "socialhome.search",
    "socialhome.tasks",
)

INSTALLED_APPS = DJANGO_APPS + THIRD_PARTY_APPS + LOCAL_APPS

# MIDDLEWARE CONFIGURATION
# ------------------------------------------------------------------------------
MIDDLEWARE = (
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
TIME_ZONE = env("DJANGO_TIMEZONE", default="UTC")

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
                "socialhome.context_processors.policy_documents",
            ],
        },
    },
]

# Required by django-markdownx
FORM_RENDERER = "django.forms.renderers.TemplatesSetting"

# Settings export
SETTINGS_EXPORT = [
    "ACCOUNT_ALLOW_REGISTRATION",
    "SOCIALHOME_NODE_LIST_URL",
]

# See: http://django-crispy-forms.readthedocs.org/en/latest/install.html#template-packs
CRISPY_TEMPLATE_PACK = "bootstrap4"

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
ACCOUNT_AUTHENTICATION_METHOD = "username_email"
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
LOGOUT_URL = "account_logout"

# SLUGLIFIER
AUTOSLUG_SLUGIFY_FUNCTION = "slugify.slugify"

# REDIS
# -----
REDIS_HOST = env("REDIS_HOST", default="localhost")
REDIS_PORT = env("REDIS_PORT", default=6379)
REDIS_DB = env("REDIS_DB", default=0)
REDIS_PASSWORD = env("REDIS_PASSWORD", default=None)
REDIS_DEFAULT_EXPIRY = 60*60*24*30

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
SOCIALHOME_RELAY_ID = env("SOCIALHOME_RELAY_ID", default="diaspora://relay@relay.iliketoast.net/profile/")
# Admins
# Boolean whether to show admin contact information to users and in server metadata
# Uses `settings.ADMINS`.
SOCIALHOME_SHOW_ADMINS = env.bool("SOCIALHOME_SHOW_ADMINS", default=False)
# Statistics
# Controls whether to expose some generic statistics about the node. This includes local user, content and reply counts
# User counts include 30 day and 6 month active users
SOCIALHOME_STATISTICS = env.bool("SOCIALHOME_STATISTICS", default=False)
# Allow to use additional third-party apps
SOCIALHOME_ADDITIONAL_APPS = env("SOCIALHOME_ADDITIONAL_APPS", default=None)
if SOCIALHOME_ADDITIONAL_APPS:
    INSTALLED_APPS += tuple(SOCIALHOME_ADDITIONAL_APPS.split(','))
SOCIALHOME_ADDITIONAL_APPS_URLS = env("SOCIALHOME_ADDITIONAL_APPS_URLS", default=None)
# Allow to use on main page custom view from third-party app
SOCIALHOME_HOME_VIEW = env("SOCIALHOME_HOME_VIEW", default=None)
# If signups are closed, make signup link point here
SOCIALHOME_NODE_LIST_URL = env("SOCIALHOME_NODE_LIST_URL", default="https://the-federation.info/socialhome")
# Contact email
SOCIALHOME_CONTACT_EMAIL = env("DJANGO_ADMIN_MAIL", default="webmaster@%s" % SOCIALHOME_DOMAIN)
# Maintainer
SOCIALHOME_MAINTAINER = env("DJANGO_ADMIN_NAME", default="Private individual")
# Jurisdiction for terms of service
SOCIALHOME_TOS_JURISDICTION = env("SOCIALHOME_TOS_JURISDICTION", default=None)

# Streams
# Trim precached streams to this maximum size
SOCIALHOME_STREAMS_PRECACHE_SIZE = env.int("SOCIALHOME_STREAMS_PRECACHE_SIZE", default=100)
SOCIALHOME_STREAMS_PRECACHE_INACTIVE_DAYS = env.int("SOCIALHOME_STREAMS_PRECACHE_INACTIVE_DAYS", default=90)
SOCIALHOME_STREAMS_PRECACHE_INACTIVE_SIZE = env.int("SOCIALHOME_STREAMS_PRECACHE_INACTIVE_SIZE", default=0)

# Exports
SOCIALHOME_EXPORTS_PATH = str(ROOT_DIR("var", "exports"))

# MANAGER CONFIGURATION
# ------------------------------------------------------------------------------
# See: https://docs.djangoproject.com/en/dev/ref/settings/#admins
ADMINS = (
    (env("DJANGO_ADMIN_NAME", default="Socialhome Admin"),
     env("DJANGO_ADMIN_MAIL", default="webmaster@%s" % SOCIALHOME_DOMAIN)),
)

# See: https://docs.djangoproject.com/en/dev/ref/settings/#managers
MANAGERS = ADMINS

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

# MARKDOWN
# --------
MARKDOWNX_MARKDOWNIFY_FUNCTION = "CommonMark.commonmark"
MARKDOWNX_MEDIA_PATH = datetime.now().strftime("uploads/%Y/%m/%d")
MARKDOWNX_IMAGE_MAX_SIZE = {
    "size": (2048, 0),
    "quality": 90,
}
MARKDOWNX_UPLOAD_MAX_SIZE = 20 * 1024 * 1024

# LOGGING CONFIGURATION
# ------------------------------------------------------------------------------
# See: https://docs.djangoproject.com/en/dev/ref/settings/#logging
log_target = env("SOCIALHOME_LOG_TARGET", default="file")
if log_target not in ("file", "syslog"):
    raise environ.ImproperlyConfigured("If set, SOCIALHOME_LOG_TARGET must be either 'file' or 'syslog'.")

LOGGING = {
    "version": 1,
    "disable_existing_loggers": True,
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
        "file": {
            "filename": env("SOCIALHOME_LOGFILE", default="/tmp/socialhome.log"),
            "level": "DEBUG",
            "class": "logging.handlers.RotatingFileHandler",
            "formatter": "verbose",
            "maxBytes": 10485760,  # 10mb
            "backupCount": 10,
        },
    },
    "loggers": {
        "django.request": {
            "handlers": [log_target],
            "level": "ERROR",
            "propagate": True,
        },
        "django.security.DisallowedHost": {
            "level": "ERROR",
            "handlers": ["console", log_target],
            "propagate": True
        },
        "socialhome": {
            "level": "DEBUG",
            "handlers": [log_target],
            "propagate": False,
        },
        "federation": {
            "level": "DEBUG",
            "handlers": [log_target],
            "propagate": False,
        },
        "rq_scheduler.scheduler": {
            "level": "ERROR",
            "handlers": [log_target],
            "propagate": False,
        },
    }
}

if log_target == "syslog":
    LOGGING["handlers"]["syslog"] = {
        "level": env("SOCIALHOME_SYSLOG_LEVEL", default="INFO"),
        "class": "logging.handlers.SysLogHandler",
        "facility": env("SOCIALHOME_SYSLOG_FACILITY", default="local7"),
        "formatter": "verbose",
        "address" : "/dev/log",
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
        "anon": "300/minute",
        "user": "300/minute",
        "image_upload": "50/day",
        "content_create": "100/day",
    },
    "DEFAULT_VERSION": "0.1",
}

# REST SWAGGER
# ------------
SWAGGER_SETTINGS = {
    "APIS_SORTER": "alpha",
    "DOC_EXPANSION": "list",
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

# HAYSTACK
# ------
HAYSTACK_CONNECTIONS = {
    "default": {
        "ENGINE": "haystack.backends.whoosh_backend.WhooshEngine",
        "PATH": str(ROOT_DIR("var", "whoosh")),
    },
}
HAYSTACK_SIGNAL_PROCESSOR = "haystack.signals.RealtimeSignalProcessor"

# VERSATILEIMAGEFILED
# -------------------
VERSATILEIMAGEFIELD_RENDITION_KEY_SETS = {
    "profile_picture": [
        ("small", "crop__50x50"),
        ("medium", "crop__100x100"),
        ("large", "crop__300x300"),
    ],
}

# FEDERATION
# ----------
FEDERATION = {
    "base_url": SOCIALHOME_URL,
    "get_profile_function": "socialhome.federate.utils.entities.get_profile",
    "nodeinfo2_function": "socialhome.federate.utils.generic.get_nodeinfo2_data",
    "search_path": "/search/?q=",
}
