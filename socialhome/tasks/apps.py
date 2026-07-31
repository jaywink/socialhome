import logging

from django.apps import AppConfig

logger = logging.getLogger("socialhome")


class TasksConfig(AppConfig):
    name = "socialhome.tasks"
    verbose_name = "Tasks"
