import json

from django.db.models.signals import post_save
from django.dispatch import receiver

from socialhome.content.models import Content
from socialhome.enums import Visibility
from socialhome.streams.consumers import StreamConsumer


@receiver(post_save, sender=Content)
def notify_listeners(sender, **kwargs):
    if kwargs.get("created"):
        content = kwargs.get("instance")
        if content.visibility == Visibility.PUBLIC:
            StreamConsumer.group_send("streams_public", json.dumps({
                "event": "new",
                "id": content.id,
            }))
