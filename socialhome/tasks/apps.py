import logging
import sys

import django_rq
from django.apps import AppConfig
from rq.exceptions import InvalidJobOperation
from rq.job import JobStatus

from socialhome.streams.tasks import streams_tasks

logger = logging.getLogger("socialhome")

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
            try:
                if job.get_status() != JobStatus.SCHEDULED: job.delete()
            except InvalidJobOperation as ex:
               logger.warning("TasksConfig.ready - failed to get scheduled job status: %s", ex)

        # Queue tasks
        streams_tasks(scheduler)
