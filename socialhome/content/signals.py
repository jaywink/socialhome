import json
import logging

from django.db.models.signals import post_save
from django.dispatch import receiver

from socialhome.content.models import Content
from socialhome.enums import Visibility
from socialhome.federate.tasks import send_content
from socialhome.streams.consumers import StreamConsumer

logger = logging.getLogger("socialhome")


@receiver(post_save, sender=Content)
def notify_listeners(sender, **kwargs):
    if kwargs.get("created"):
        content = kwargs.get("instance")
        if content.visibility == Visibility.PUBLIC:
            StreamConsumer.group_send("streams_public", json.dumps({
                "event": "new",
                "id": content.id,
            }))


@receiver(post_save, sender=Content)
def federate_content(sender, **kwargs):
    """Send out local content to the federation layer.

    Yes, edits also. The federation layer should decide whether these are really worth sending out.
    """
    content = kwargs.get("instance")
    if content.is_local:
        try:
            send_content.delay(content)
        except Exception as ex:
            logger.exception("Failed to federate_content %s: %s", content, ex)
