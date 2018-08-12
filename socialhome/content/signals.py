import json
import logging

import django_rq
from django.db import transaction
from django.db.models.signals import post_save, post_delete, m2m_changed
from django.dispatch import receiver

from socialhome.content.enums import ContentType
from socialhome.content.models import Content
from socialhome.content.previews import fetch_content_preview
from socialhome.enums import Visibility
from socialhome.federate.tasks import send_content, send_content_retraction, send_reply, send_share
from socialhome.notifications.tasks import send_reply_notifications, send_share_notification, send_mention_notification
from socialhome.streams.consumers import StreamConsumer
from socialhome.streams.streams import update_streams_with_content
from socialhome.users.models import Profile

logger = logging.getLogger("socialhome")


@receiver(post_save, sender=Content)
def content_post_save(instance, **kwargs):
    # TODO remove extract mentions from here when we have UI for creating mentions
    if instance.local:
        instance.extract_mentions()
    fetch_preview(instance)
    render_content(instance)
    if kwargs.get("created"):
        notify_listeners(instance)
        if instance.content_type == ContentType.REPLY:
            transaction.on_commit(lambda: django_rq.enqueue(send_reply_notifications, instance.id))
        elif instance.content_type == ContentType.SHARE and instance.share_of.local:
            transaction.on_commit(lambda: django_rq.enqueue(send_share_notification, instance.id))
        transaction.on_commit(lambda: update_streams_with_content(instance))
    if instance.federate and instance.local:
        transaction.on_commit(lambda: federate_content(instance))


@receiver(post_delete, sender=Content)
def federate_content_retraction(instance, **kwargs):
    """Send out local content retractions to the federation layer."""
    if instance.local:
        logger.debug('federate_content_retraction: Sending out Content retraction: %s', instance)
        try:
            django_rq.enqueue(send_content_retraction, instance, instance.author_id)
        except Exception as ex:
            logger.exception("Failed to federate_content_retraction %s: %s", instance, ex)


def fetch_preview(content):
    try:
        fetch_content_preview(content)
    except Exception as ex:
        logger.exception("Failed to fetch content preview for %s: %s", content, ex)


def on_commit_mentioned(action, pks, instance):
    for id in pks:
        # Send out notification only if local mentioned
        if action == "post_add" and Profile.objects.filter(id=id, user__isnull=False).exists():
            profile = Profile.objects.values('user_id').get(id=id)
            django_rq.enqueue(send_mention_notification, profile['user_id'], instance.author.id, instance.id)


@receiver(m2m_changed, sender=Content.mentions.through)
def content_mentions_change(sender, instance, action, pk_set, **kwargs):
    """Deliver notification on mentions addition."""
    if action == "post_add":
        transaction.on_commit(lambda: on_commit_mentioned(action, pk_set, instance))


def on_commit_limited_visibilities(action, pks, instance):
    if action not in ("post_add", "post_remove"):
        return

    for id in pks:
        # Send out federation only if remote profile
        if not Profile.objects.filter(id=id, user__isnull=True).exists():
            continue
        profile = Profile.objects.get(id=id)

        if action == "post_add":
            try:
                federate_content(instance, recipient=profile)
            except Exception:
                logger.exception("Failed to federate limited visibility content %s to %s", instance.uuid, profile.uuid)
        elif action == "post_remove":
            try:
                federate_content_retraction(instance, recipient=profile)
            except Exception:
                logger.exception("Failed to federate limited visibility content %s to %s", instance.uuid, profile.uuid)


@receiver(m2m_changed, sender=Content.limited_visibilities.through)
def content_limited_visibilities_change(sender, instance, action, pk_set, **kwargs):
    """Federate limited visibilities change."""
    if not instance.local or not instance.content_type == ContentType.CONTENT:
        return
    if action in ("post_add", "post_remove"):
        transaction.on_commit(lambda: on_commit_limited_visibilities(action, pk_set, instance))


def render_content(content):
    content.refresh_from_db()
    try:
        content.render()
    except Exception as ex:
        logger.exception("Failed to render text for %s: %s", content, ex)


def notify_listeners(content):
    """Send out to listening consumers."""
    data = json.dumps({"event": "new", "id": content.id})
    if content.content_type == ContentType.REPLY:
        # Content reply
        StreamConsumer.group_send("streams_content__%s" % content.parent.channel_group_name, data)
    elif content.content_type == ContentType.SHARE:
        # Share
        # TODO do we need to do much?
        pass
    else:
        # Public stream
        if content.visibility == Visibility.PUBLIC:
            StreamConsumer.group_send("streams_public", data)
        # Tag streams
        for tag in content.tags.all():
            StreamConsumer.group_send("streams_tag__%s" % tag.channel_group_name, data)
        # Profile streams
        StreamConsumer.group_send("streams_profile__%s" % content.author.id, data)
        StreamConsumer.group_send("streams_profile_all__%s" % content.author.id, data)
        # Followed stream
        followed_qs = Profile.objects.followers(content.author).filter(user__isnull=False)
        for username in followed_qs.values_list("user__username", flat=True):
            StreamConsumer.group_send("streams_followed__%s" % username, data)


def federate_content(content, recipient=None):
    """Send out local content to the federation layer.

    Yes, edits also. The federation layer should decide whether these are really worth sending out.
    """
    recipient_id = recipient.id if recipient else None
    try:
        if content.content_type == ContentType.REPLY:
            django_rq.enqueue(send_reply, content.id)
        elif content.content_type == ContentType.SHARE:
            django_rq.enqueue(send_share, content.id)
        else:
            if content.visibility == Visibility.LIMITED and not recipient_id:
                return
            django_rq.enqueue(send_content, content.id, recipient_id=recipient_id)
    except Exception as ex:
        logger.exception("Failed to federate_content %s: %s", content, ex)
