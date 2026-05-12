from typing import Union

import dramatiq
from django.conf import settings

from socialhome.utils import get_redis_connection


class QueueOnceMiddleware(dramatiq.middleware.Middleware):
    """
    Queue once middleware.

    Pass in a `queue_once_id: str` in `kwargs` to ensure if a message has
    already been queued to the queue with the same actor, the enqueue will be skipped.
    """

    @staticmethod
    def key(message: Union[dramatiq.MessageProxy, dramatiq.Message]) -> str:
        return f"sh:tasks:queue_once:{message.actor_name}:{message.kwargs.get('queue_once_id')}"

    def before_enqueue(self, broker, message, delay):
        if not message.kwargs.get("queue_once_id"):
            return
        r = get_redis_connection()
        key = self.key(message)
        if r.exists(key):
            raise dramatiq.errors.SkipMessage(f"Queue already has {message.actor_name} unique ID {message.kwargs.get('queue_once_id')} queued")
        r.set(key, message.kwargs.get('queue_once_id'))
        r.expire(key, settings.REDIS_DEFAULT_EXPIRY)

    def after_process_message(self, broker, message, *, result=None, exception=None):
        if not message.kwargs.get("queue_once_id"):
            return
        r = get_redis_connection()
        key = self.key(message)
        if r.exists(key):
            r.delete(key)
