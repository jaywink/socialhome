import logging
import sys

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from django.apps import AppConfig

from socialhome.streams.tasks import delete_redis_keys, groom_redis_precaches

logger = logging.getLogger("socialhome")


class TasksConfig(AppConfig):
    name = "socialhome.tasks"
    verbose_name = "Tasks"

    def ready(self):
        # Only register tasks if running dramatiq
        if "rundramatiq" not in sys.argv:
            return

        scheduler = BackgroundScheduler()

        # Queue tasks
        # Clean up some Redis keys
        logger.info("tasks - Scheduling streams task: delete_redis_keys")
        scheduler.add_job(
            func=delete_redis_keys.send,
            trigger=CronTrigger(hour="*/12", minute=15),
            args=[["rq:job:*", "rq:results:*", "fed_cache:*"]],
        )
        # Groom redis precaches
        logger.info("tasks - Scheduling streams task: groom_redis_precaches")
        scheduler.add_job(
            func=groom_redis_precaches.send,
            trigger=CronTrigger(hour="*/3", minute=30),
        )

        # Start the scheduler
        scheduler.start()
