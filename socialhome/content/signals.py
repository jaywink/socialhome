import json
import logging

import django_rq
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver

from socialhome.content.models import Content
from socialhome.content.previews import fetch_content_preview
from socialhome.enums import Visibility
from socialhome.federate.tasks import send_content, send_content_retraction, send_reply
from socialhome.notifications.tasks import send_reply_notifications
from socialhome.streams.consumers import StreamConsumer

logger = logging.getLogger("socialhome")


@receiver(post_save, sender=Content)
def content_post_save(instance, **kwargs):
    fetch_preview(instance)
    render_content(instance)
    if kwargs.get("created"):
        notify_listeners(instance)
    if instance.is_local:
        federate_content(instance)
    if instance.parent:
        django_rq.enqueue(send_reply_notifications, instance.id)


@receiver(post_delete, sender=Content)
def federate_content_retraction(instance, **kwargs):
    """Send out local content retractions to the federation layer."""
    # TODO federate replies also when that is available in federation layer
    if instance.is_local and not instance.parent:
        try:
            django_rq.enqueue(send_content_retraction, instance, instance.author_id)
        except Exception as ex:
            logger.exception("Failed to federate_content_retraction %s: %s", instance, ex)


def fetch_preview(content):
    try:
        fetch_content_preview(content)
    except Exception as ex:
        logger.exception("Failed to fetch content preview for %s: %s", content, ex)


def render_content(content):
    content.refresh_from_db()
    try:
        content.render()
    except Exception as ex:
        logger.exception("Failed to render text for %s: %s", content, ex)


def notify_listeners(content):
    """Send out to listening consumers."""
    # TODO: add sending for tags, content and user profile streams
    if content.visibility == Visibility.PUBLIC and not content.parent:
        StreamConsumer.group_send("streams_public", json.dumps({
            "event": "new",
            "id": content.id,
        }))


def federate_content(content):
    """Send out local content to the federation layer.

    Yes, edits also. The federation layer should decide whether these are really worth sending out.
    """
    try:
        if content.parent:
            django_rq.enqueue(send_reply, content.id)
        else:
            django_rq.enqueue(send_content, content.id)
    except Exception as ex:
        logger.exception("Failed to federate_content %s: %s", content, ex)
