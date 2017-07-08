import json
import logging

import django_rq
from django.db import transaction
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver

from socialhome.content.models import Content, Tag
from socialhome.content.previews import fetch_content_preview
from socialhome.enums import Visibility
from socialhome.federate.tasks import send_content, send_content_retraction, send_reply
from socialhome.notifications.tasks import send_reply_notifications
from socialhome.streams.consumers import StreamConsumer
from socialhome.users.models import Profile

logger = logging.getLogger("socialhome")


@receiver(post_save, sender=Content)
def content_post_save(instance, **kwargs):
    fetch_preview(instance)
    render_content(instance)
    if kwargs.get("created"):
        notify_listeners(instance)
        if instance.parent:
            transaction.on_commit(lambda: django_rq.enqueue(send_reply_notifications, instance.id))
    if instance.is_local:
        transaction.on_commit(lambda: federate_content(instance))


@receiver(post_delete, sender=Content)
def federate_content_retraction(instance, **kwargs):
    """Send out local content retractions to the federation layer."""
    if instance.is_local:
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
    data = json.dumps({"event": "new", "id": content.id})
    if content.parent:
        # Content comments
        StreamConsumer.group_send("streams_content__%s" % content.parent.channel_group_name, data)
    else:
        # Public stream
        if content.visibility == Visibility.PUBLIC:
            StreamConsumer.group_send("streams_public", data)
        # Tag streams
        for tag in content.tags.all():
            StreamConsumer.group_send("streams_tags__%s" % tag.channel_group_name, data)
        # Profile streams
        StreamConsumer.group_send("streams_profile__%s" % content.author.id, data)
        StreamConsumer.group_send("streams_profile_all__%s" % content.author.id, data)
        # Followed stream
        followed_qs = Profile.objects.followers(content.author).filter(user__isnull=False)
        for username in followed_qs.values_list("user__username", flat=True):
            StreamConsumer.group_send("streams_followed__%s" % username, data)


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
