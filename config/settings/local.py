# -*- coding: utf-8 -*-
'''
Local settings

- Run in Debug mode
- Use console backend for emails
- Add Django Debug Toolbar
- Add django-extensions as app
'''

from .common import *  # noqa

# DEBUG
# ------------------------------------------------------------------------------
DEBUG = env.bool('DJANGO_DEBUG', default=True)
if env.bool('CI', default=False):
    # Required by django_coverage_plugin
    TEMPLATES[0]['OPTIONS']['debug'] = True
else:
    TEMPLATES[0]['OPTIONS']['debug'] = DEBUG

# SECRET CONFIGURATION
# ------------------------------------------------------------------------------
# See: https://docs.djangoproject.com/en/dev/ref/settings/#secret-key
# Note: This key only used for development and testing.
SECRET_KEY = env("DJANGO_SECRET_KEY", default='((5)iob@s%#(3=@le*xd^hu^)4_btrz7zpq-e1=@wruddsl9+h')

# Mail settings
# ------------------------------------------------------------------------------
EMAIL_HOST = 'localhost'
EMAIL_PORT = 1025
EMAIL_BACKEND = env('DJANGO_EMAIL_BACKEND',
                    default='django.core.mail.backends.console.EmailBackend')

# CACHING
# ------------------------------------------------------------------------------
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': ''
    }
}

# django-debug-toolbar
# ------------------------------------------------------------------------------
if env.bool("DJANGO_DEBUG_TOOLBAR", default=True):
    DEBUG_TOOLBAR_ENABLED = True
    MIDDLEWARE_CLASSES += ('debug_toolbar.middleware.DebugToolbarMiddleware',)
    INSTALLED_APPS += ('debug_toolbar', )

    INTERNAL_IPS = ('127.0.0.1', '10.0.2.2',)

    DEBUG_TOOLBAR_CONFIG = {
        'DISABLE_PANELS': [
            'debug_toolbar.panels.redirects.RedirectsPanel',
        ],
        'SHOW_TEMPLATE_CONTEXT': True,
    }

# TESTING
# ------------------------------------------------------------------------------
TEST_RUNNER = 'django.test.runner.DiscoverRunner'

# Mocha JS testing
# ------------------------------------------------------------------------------
MOCHA_TESTS = env.bool('MOCHA_TESTS', default=False)
if MOCHA_TESTS:
    INSTALLED_APPS += ("mocha",)
    MIDDLEWARE_CLASSES += ('whitenoise.middleware.WhiteNoiseMiddleware',)
    MOCHA_RUNSERVER_PORT = env.int("MOCHA_RUNSERVER_PORT", default=8000)

# RQ
# --
RQ_QUEUES["default"]["ASYNC"] = False

# Your local stuff: Below this line define 3rd party library settings

# SOCIALHOME
# ------------------------------------------------------------------------------
# Disable generating RSA keys automatically, otherwise tests become slow
SOCIALHOME_GENERATE_USER_RSA_KEYS_ON_SAVE = False
SOCIALHOME_HTTPS = False
