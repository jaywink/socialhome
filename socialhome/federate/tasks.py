# -*- coding: utf-8 -*-
from socialhome.taskapp.celery import tasks


@tasks.task()
def receive_public_task(payload):
    """Process payload from /receive/public queue."""
    # TODO implement
    print(payload)
