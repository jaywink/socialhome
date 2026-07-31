import logging

import dramatiq
from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger
from django.core.management.base import BaseCommand

from socialhome.streams.tasks import delete_redis_keys, groom_redis_precaches

logger = logging.getLogger("socialhome")


@dramatiq.actor
def dummy_task():
    logger.info("tasks.dummy_task - Running dummy task")


class Command(BaseCommand):
    help = """Run APScheduler.
    
    Note! Only run this once. If using the provided `circus.ini` configuration, or using the
    provided official Docker image, this scheduler will already be running.
    """

    def handle(self, *args, **options):
        scheduler = BlockingScheduler()

        # Queue tasks
        # Clean up some Redis keys
        logger.info("tasks - Scheduling streams task: delete_redis_keys")
        scheduler.add_job(
            func=delete_redis_keys.send,
            trigger=CronTrigger.from_crontab("15 */12 * * *"),
            args=[["rq:job:*", "rq:results:*", "fed_cache:*"]],
            max_instances=1,
        )
        # Groom redis precaches
        logger.info("tasks - Scheduling streams task: groom_redis_precaches")
        scheduler.add_job(
            func=groom_redis_precaches.send,
            trigger=CronTrigger.from_crontab("30 */3 * * *"),
            max_instances=1,
        )

        # Dummy task
        logger.info("tasks - Scheduling dummy task")
        scheduler.add_job(
            func=dummy_task.send,
            trigger=CronTrigger.from_crontab("*/5 * * * *"),
        )

        # Start the scheduler
        try:
            logger.info("tasks - Starting scheduler...")
            scheduler.start()
        except KeyboardInterrupt:
            logger.info("tasks - Stopping scheduler...")
            scheduler.shutdown()
            logger.info("tasks - Scheduler shut down successfully!")
