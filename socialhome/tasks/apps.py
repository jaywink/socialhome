import sys

import django_rq
from django.apps import AppConfig

from socialhome.streams.tasks import streams_tasks


class TasksConfig(AppConfig):
    name = "socialhome.tasks"
    verbose_name = "Tasks"

    def ready(self):
        # Only register tasks if RQ Scheduler process
        if "rqscheduler" not in sys.argv:
            return

        scheduler = django_rq.get_scheduler("default")

        # Delete any existing jobs in the scheduler when the app starts up
        for job in scheduler.get_jobs():
            job.delete()

        # Queue tasks
        streams_tasks(scheduler)
