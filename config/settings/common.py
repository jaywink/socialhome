# -*- coding: utf-8 -*-
"""
Django settings for Socialhome project.

For more information on this file, see
https://docs.djangoproject.com/en/dev/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/dev/ref/settings/
"""
import os
import sys
import warnings
from datetime import datetime, timedelta

import environ

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

testing = env.bool("CI", default=False) or env.bool("TEST", default=False) or "test" in sys.argv

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
    "channels",
    "daphne",
    "corsheaders",
    "crispy_forms",
    "crispy_bootstrap4",
    "allauth",
    "allauth.account",
    "allauth.socialaccount",
    "markdownx",
    "django_extensions",
    "django_rq",
    "rest_framework",
    "rest_framework.authtoken",
    "dynamic_preferences",
    "dynamic_preferences.users.apps.UserPreferencesConfig",
    "haystack",
    "versatileimagefield",
    "django_js_reverse",
    "memoize",
    "redisboard",
    "robots",
    "reversion",
    "drf_yasg",
)
LOCAL_APPS = (
    "socialhome",
    "socialhome.activities",
    "socialhome.users",
    "socialhome.federate",
    "socialhome.content",
    "socialhome.notifications",
    "socialhome.streams",
    "socialhome.search",
    "socialhome.tasks",
)

INSTALLED_APPS = THIRD_PARTY_APPS + DJANGO_APPS + LOCAL_APPS

SILKY_INSTALLED = env.bool("SOCIALHOME_SILKY", False)
if testing:
    SILKY_INSTALLED = False

# MIDDLEWARE CONFIGURATION
# ------------------------------------------------------------------------------
MIDDLEWARE = (
    "corsheaders.middleware.CorsMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.locale.LocaleMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "socialhome.users.middleware.AdminApprovalMiddleware",
    "socialhome.users.middleware.use_new_ui",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "django.contrib.sites.middleware.CurrentSiteMiddleware",
)

# SILK
# ----
def is_silky_request(request):
    path = request.path.strip('/')
    if path.startswith('_') or path.startswith('admin') or path.startswith('static') or path.startswith('jsi18n') or \
            path.startswith('jsreverse'):
        return False
    return True

if SILKY_INSTALLED:
    SILKY_INTERCEPT_FUNC = is_silky_request
    INSTALLED_APPS = INSTALLED_APPS + ("silk",)
    MIDDLEWARE = ("silk.middleware.SilkyMiddleware",) + MIDDLEWARE

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
DISABLE_OUTBOUND_FEDERATION = env.bool("SOCIALHOME_DISABLE_OUTBOUND_FEDERATION", False)

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
    "default": env.db(
        "DATABASE_URL",
        default="postgres://socialhome:socialhome@127.0.0.1:5432/socialhome",
    ),
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
LANGUAGE_CODE = env("SOCIALHOME_LANGUAGE_CODE", default="en-us")

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
    "SOCIALHOME_STREAMS_PUBLIC_STREAM_WITHOUT_AUTH",
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

ACCOUNT_FORMS = {
    "signup": "socialhome.users.forms.UserSignupForm",
}
SOCIALACCOUNT_FORMS = {
    "signup": "socialhome.users.forms.UserSocialAccountSignupForm",
}

ACCOUNT_ALLOW_REGISTRATION = env.bool("DJANGO_ACCOUNT_ALLOW_REGISTRATION", True)
# Require new signups to be approved by an admin
ACCOUNT_SIGNUP_REQUIRE_ADMIN_APPROVAL = env.bool("ACCOUNT_SIGNUP_REQUIRE_ADMIN_APPROVAL", False)
ACCOUNT_ADAPTER = "socialhome.users.adapters.AccountAdapter"
ACCOUNT_PRESERVE_USERNAME_CASING = False
SOCIALACCOUNT_ADAPTER = "socialhome.users.adapters.SocialAccountAdapter"

# Select the correct user model
AUTH_USER_MODEL = "users.User"
LOGIN_REDIRECT_URL = "home"
LOGIN_URL = "account_login"
LOGOUT_URL = "account_logout"

# REDIS
# -----
REDIS_HOST = env("REDIS_HOST", default="localhost")
REDIS_PORT = env("REDIS_PORT", default=6379)
REDIS_DB = env("REDIS_DB", default=0)
REDIS_PASSWORD = env("REDIS_PASSWORD", default=None)
REDIS_DEFAULT_EXPIRY = 60*60*24*30

# RQ
# --
rq_queue_config = {
    "HOST": REDIS_HOST,
    "PORT": REDIS_PORT,
    "DB": REDIS_DB,
    "PASSWORD": REDIS_PASSWORD,
    "DEFAULT_TIMEOUT": 600,
}
RQ_QUEUES = {
    "highest": rq_queue_config,
    "high": rq_queue_config,
    "default": rq_queue_config,
    "low": rq_queue_config,
    "lowest": rq_queue_config,
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
# Defaults to DJANGO_ADMIN_MAIL for backwards compatibility, TODO remove sometime after v0.17.0
SOCIALHOME_CONTACT_EMAIL = env(
    "SOCIALHOME_CONTACT_EMAIL",
    default=env("DJANGO_ADMIN_MAIL", default="info@%s" % SOCIALHOME_DOMAIN),
)
# Maintainer
# Defaults to DJANGO_ADMIN_NAME for backwards compatibility, TODO remove sometime after v0.17.0
SOCIALHOME_MAINTAINER = env(
    "SOCIALHOME_MAINTAINER",
    default=env("DJANGO_ADMIN_NAME", default="Private individual"),
)
# Jurisdiction for terms of service
SOCIALHOME_TOS_JURISDICTION = env("SOCIALHOME_TOS_JURISDICTION", default=None)

# Streams
# Trim precached streams to this maximum size
SOCIALHOME_STREAMS_PRECACHE_SIZE = env.int("SOCIALHOME_STREAMS_PRECACHE_SIZE", default=100)
SOCIALHOME_STREAMS_PRECACHE_INACTIVE_DAYS = env.int("SOCIALHOME_STREAMS_PRECACHE_INACTIVE_DAYS", default=90)
SOCIALHOME_STREAMS_PRECACHE_INACTIVE_SIZE = env.int("SOCIALHOME_STREAMS_PRECACHE_INACTIVE_SIZE", default=0)
# Should the public stream be shown for anonymous users. This defaults as follows:
# - if this is likely a single user instance, ie SOCIALHOME_ROOT_PROFILE is set, do not show a public stream
# - otherwise, show a public stream by default, unless disabled
SOCIALHOME_STREAMS_PUBLIC_STREAM_WITHOUT_AUTH = env.bool(
    "SOCIALHOME_STREAMS_PUBLIC_STREAM_WITHOUT_AUTH", default=False if SOCIALHOME_ROOT_PROFILE else True,
)

# Content
# These attributes on tags are kept on save for untrusted users
SOCIALHOME_CONTENT_SAFE_ATTRS = {
    'a': ['class', 'href', 'title', 'target', 'data-mention', 'data-hashtag'],
    'abbr': ['title'],
    'acronym': ['title'],
    'audio': ['controls', 'src'],
    'canvas': ['class', 'width', 'height'],
    'div': ['class', 'role', 'tabindex', 'style'],
    'i': ['class', 'role'],
    'img': ['src', 'title', 'class', 'alt', 'style'],
    'source': ['src', 'type'],
    'span': ['class'],
    'table': ['class'],
    'td': ['class'],
    'th': ['class'],
    'tr': ['class'],
    'video': ['class', 'role', 'src', 'loop', 'controls', 'poster'],
}
# These tags are kept on save for untrusted users
SOCIALHOME_CONTENT_SAFE_TAGS = [
    'a',
    'abbr',
    'audio',
    'b',
    'bdi',
    'blockquote',
    'br',
    'button',
    'canvas',
    'code',
    'dd',
    'div',
    'dl',
    'dt',
    'em',
    'h1',
    'h2',
    'h3',
    'h4',
    'h5',
    'h6',
    'hr',
    'i',
    'img',
    'li',
    'ol',
    'p',
    'pre',
    'q',
    'small',
    'source',
    'span',
    'strong',
    'sub',
    'table',
    'tbody',
    'td',
    'tfoot',
    'th',
    'thead',
    'tr',
    'ul',
    'video',
]

# Exports
SOCIALHOME_EXPORTS_PATH = str(ROOT_DIR("var", "exports"))

# How many seconds since we saw user activity do we consider the user have been recently active?
SOCIALHOME_USER_ACTIVITY_SECONDS = 130

# How many days from now before a remote profile will be updated
SOCIALHOME_PROFILE_UPDATE_FREQ = timedelta(days = int(env("SOCIALHOME_PROFILE_UPDATE_FREQ", default="7")))

# Matrix support
# NOTE! Incomplete, alpha, here be dragons, requires Dendrite, etc
SOCIALHOME_MATRIX_ENABLED = env.bool("SOCIALHOME_MATRIX_ENABLED", default=False)
# **REQUIRED** if Matrix support is enabled:
# This is a secret token to communicate with the Matrix homeserver. Never give it to anyone!
SOCIALHOME_MATRIX_APPSERVICE_TOKEN = env("SOCIALHOME_MATRIX_APPSERVICE_TOKEN", default=None)
# An ID for the appservice, **should never change after creating**.
SOCIALHOME_MATRIX_APPSERVICE_ID = env("SOCIALHOME_MATRIX_APPSERVICE_ID", default=None)
# **OPTIONAL** to change from defaults:
# Shortcode for the socialhome instance. Only a-z, used for namespacing things.
SOCIALHOME_MATRIX_APPSERVICE_SHORTCODE = env("SOCIALHOME_MATRIX_APPSERVICE_SHORTCODE", default="socialhome")
# **NOT TO BE MODIFIED**
SOCIALHOME_MATRIX_HOMESERVER = f"matrix.{SOCIALHOME_DOMAIN}"
SOCIALHOME_MATRIX_APPSERVICE_BASE_URL = f"https://{SOCIALHOME_MATRIX_HOMESERVER}"
SOCIALHOME_MATRIX_APPSERVICE_DOMAIN_WITH_PORT = f"{SOCIALHOME_MATRIX_HOMESERVER}:443"
# Valid user name required for get requests signature by federation
FEDERATION_USER = env("FEDERATION_USER", default=None)

# MANAGER CONFIGURATION
# ------------------------------------------------------------------------------
# See: https://docs.djangoproject.com/en/dev/ref/settings/#admins
ADMINS = [(SOCIALHOME_MAINTAINER, SOCIALHOME_CONTACT_EMAIL)]

# See: https://docs.djangoproject.com/en/dev/ref/settings/#managers
MANAGERS = ADMINS

# CHANNELS
# --------
# http://channels.readthedocs.org/en/latest/deploying.html#setting-up-a-channel-backend
CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels_redis.core.RedisChannelLayer",
        "CONFIG": {
            "hosts": [
                "redis://%s:%s/%s" % (REDIS_HOST, REDIS_PORT, REDIS_DB)
            ],
        },
    },
}
ASGI_APPLICATION = "config.asgi.application"

# MARKDOWN
# --------
MARKDOWNX_MARKDOWNIFY_FUNCTION = "commonmark.commonmark"
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
if log_target not in ("file", "syslog", "console"):
    raise environ.ImproperlyConfigured("If set, SOCIALHOME_LOG_TARGET must be either 'file', 'syslog' or 'console'.")

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "filters": {
        "require_debug_false": {
            "()": "django.utils.log.RequireDebugFalse",
        },
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
            "level": env("SOCIALHOME_LOG_LEVEL", default="INFO"),
            "class": "logging.StreamHandler",
            "formatter": "verbose",
        },
        "file": {
            "filename": env("SOCIALHOME_LOGFILE", default="/tmp/socialhome.log"),
            "level": env("SOCIALHOME_LOG_LEVEL", default="INFO"),
            "class": "logging.handlers.RotatingFileHandler",
            "formatter": "verbose",
            "maxBytes": 10485760,  # 10mb
            "backupCount": 10,
        },
    },
    "loggers": {
        "django.request": {
            "handlers": [log_target],
            "level": env("SOCIALHOME_LOG_LEVEL", default="INFO"),
            "propagate": True,
        },
        "django.security.DisallowedHost": {
            "level": env("SOCIALHOME_LOG_LEVEL", default="INFO"),
            "handlers": [log_target],
            "propagate": True,
        },
        "django": {
            "level": env("SOCIALHOME_LOG_LEVEL", default="INFO"),
            "handlers": [log_target, "mail_admins"],
        },
        "socialhome": {
            "level": env("SOCIALHOME_LOG_LEVEL", default="INFO"),
            "handlers": [log_target],
            "propagate": False,
        },
        "federation": {
            "level": env("SOCIALHOME_LOG_LEVEL", default="INFO"),
            "handlers": [log_target],
            "propagate": False,
        },
        "rq_scheduler.scheduler": {
            "level": env("SOCIALHOME_LOG_LEVEL", default="INFO"),
            "handlers": [log_target],
            "propagate": False,
        },
    }
}

if log_target == "syslog":
    if env("SOCIALHOME_SYSLOG_LEVEL", default=None):
        syslog_log_level = env("SOCIALHOME_SYSLOG_LEVEL", default=None)
    else:
        syslog_log_level = env("SOCIALHOME_LOG_LEVEL", default=None)
    LOGGING["handlers"]["syslog"] = {
        "level": syslog_log_level,
        "class": "logging.handlers.SysLogHandler",
        "facility": env("SOCIALHOME_SYSLOG_FACILITY", default="local7"),
        "formatter": "verbose",
        "address": "/dev/log",
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
    "DEFAULT_SCHEMA_CLASS": "rest_framework.schemas.coreapi.AutoSchema",
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
    'DEFAULT_VERSIONING_CLASS': 'rest_framework.versioning.AcceptHeaderVersioning',
}

# See https://docs.djangoproject.com/en/3.2/releases/3.2/#models
DEFAULT_AUTO_FIELD = 'django.db.models.AutoField'

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
        "ENGINE": "xapian_backend.XapianEngine",
        "PATH": str(ROOT_DIR("var", "xapian-index")),
        "BATCH_SIZE": 100,
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
    "disable_outbound_federation": DISABLE_OUTBOUND_FEDERATION,
    "federation_id": f'{SOCIALHOME_URL}/u/{FEDERATION_USER}/',
    "get_object_function": "socialhome.federate.utils.entities.get_federable_object",
    "get_private_key_function": "socialhome.federate.utils.entities.get_user_private_key",
    "get_profile_function": "socialhome.federate.utils.entities.get_profile",
    "get_public_key_function": "socialhome.federate.utils.tasks.sender_key_fetcher",
    "get_receivers_function": "socialhome.federate.utils.entities.get_receivers_for_content",
    "nodeinfo2_function": "socialhome.federate.utils.generic.get_nodeinfo2_data",
    "process_payload_function": "socialhome.federate.utils.generic.queue_payload",
    "redis": {"host": REDIS_HOST, "port": REDIS_PORT, "db": REDIS_DB, "password": REDIS_PASSWORD},
    "search_path": "/search/?q=",
    "tags_path": "/streams/tag/:tag:/",
}
if SOCIALHOME_MATRIX_ENABLED:
    FEDERATION["matrix_config_function"] = "socialhome.federate.utils.generic.get_matrix_config"
