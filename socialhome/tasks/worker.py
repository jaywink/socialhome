import logging
import os

import prometheus_client
from rq import Worker

logger = logging.getLogger("socialhome")


class SocialhomeWorker(Worker):
    """Custom RQ Worker class to override where necessary.

    See https://python-rq.org/docs/workers/#custom-worker-classes
    """
    def main_work_horse(self, *args, **kwargs):
        """This is the entry point of the newly spawned work horse.

        Ensure our Prometheus client PID is set to the main worker pid.
        """
        prometheus_client.values.ValueClass = prometheus_client.values.MultiProcessValue(
            process_identifier=os.getppid,
        )
        logger.warning(f"***** WORKER JOB worker pid {os.getppid()} ({self.pid}) my pid {os.getpid()}")

        super().main_work_horse(*args, **kwargs)
