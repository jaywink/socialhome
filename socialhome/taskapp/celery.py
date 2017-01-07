# -*- coding: utf-8 -*-
from __future__ import absolute_import

import os

from celery import Celery
from django.apps import AppConfig
from django.conf import settings


if not settings.configured:
    # set the default Django settings module for the 'celery' program.
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.local")  # pragma: no cover


tasks = Celery('socialhome')


class CeleryConfig(AppConfig):
    name = 'socialhome.taskapp'
    verbose_name = 'Celery Config'

    def ready(self):
        # Using a string here means the worker will not have to
        # pickle the object when using Windows.
        tasks.config_from_object('django.conf:settings', namespace='CELERY')
        tasks.autodiscover_tasks()

        if hasattr(settings, 'OPBEAT'):
            from opbeat.contrib.django.models import client as opbeat_client
            from opbeat.contrib.django.models import logger as opbeat_logger
            from opbeat.contrib.django.models import register_handlers as opbeat_register_handlers
            from opbeat.contrib.celery import register_signal as opbeat_register_signal

            try:
                opbeat_register_signal(opbeat_client)
            except Exception as e:
                opbeat_logger.exception('Failed installing celery hook: %s' % e)

            if 'opbeat.contrib.django' in settings.INSTALLED_APPS:
                opbeat_register_handlers()


@tasks.task(bind=True)
def debug_task(self):
    print('Request: {0!r}'.format(self.request))  # pragma: no cover
