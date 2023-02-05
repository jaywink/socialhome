import logging

import django_rq
from django.db import transaction
from django.db.models.signals import post_save, m2m_changed, pre_delete, post_delete
from django.dispatch import receiver
from federation.entities.activitypub.enums import ActivityType

from socialhome.activities.models import Activity
from socialhome.content.enums import ContentType
from socialhome.content.models import Content
from socialhome.content.previews import fetch_content_preview
from socialhome.enums import Visibility
from socialhome.federate.tasks import send_content, send_content_retraction, send_reply, send_share
from socialhome.notifications.tasks import send_reply_notifications, send_share_notification, send_mention_notification
from socialhome.streams.streams import update_streams_with_content
from socialhome.users.models import Profile

logger = logging.getLogger("socialhome")


@receiver(post_save, sender=Content)
def content_post_save(instance, **kwargs):
    fetch_preview(instance)
    render_content(instance)
    created = kwargs.get("created")
    if created:
        queue = django_rq.get_queue("low")
        if instance.content_type == ContentType.REPLY:
            transaction.on_commit(lambda: queue.enqueue(send_reply_notifications, instance.id))
        elif instance.content_type == ContentType.SHARE and instance.share_of.local:
            transaction.on_commit(lambda: queue.enqueue(send_share_notification, instance.id))
    transaction.on_commit(lambda: update_streams_with_content(instance, event='new' if created else 'update'))
    if instance.federate and instance.local:
        # Get an activity to be used when federating
        activity_type = ActivityType.CREATE if created else ActivityType.UPDATE
        activity = instance.create_activity(activity_type)
        transaction.on_commit(lambda: federate_content(instance, activity=activity))


@receiver(pre_delete, sender=Content)
def federate_content_retraction(instance, **kwargs):
    """Send out local content retractions to the federation layer."""
    if instance.local:
        logger.debug('federate_content_retraction: Sending out Content retraction: %s', instance)
        try:
            # Process immediately since things wont be in the db otherwise
            send_content_retraction(instance, instance.author_id)
        except Exception as ex:
            logger.exception("Failed to federate_content_retraction %s: %s", instance, ex)


@receiver(post_delete, sender=Content)
def update_counts(instance, **kwargs):
    try:
        parent = Content.objects.get(id=instance.parent_id)
        parent.cache_data(commit=True)
        parent.cache_related_object_data()
    except:
        pass


def fetch_preview(content):
    try:
        fetch_content_preview(content)
    except Exception as ex:
        logger.exception("Failed to fetch content preview for %s: %s", content, ex)


def on_commit_mentioned(action, pks, instance):
    for id in pks:
        # Send out notification only if local mentioned
        if action == "post_add" and Profile.objects.filter(id=id, user__isnull=False).exists():
            queue = django_rq.get_queue("high")
            profile = Profile.objects.values('user_id').get(id=id)
            queue.enqueue(send_mention_notification, profile['user_id'], instance.author.id, instance.id)
    if action == "post_add": render_content(instance)


@receiver(m2m_changed, sender=Content.mentions.through)
def content_mentions_change(sender, instance, action, pk_set, **kwargs):
    """Deliver notification on mentions addition."""
    if action == "post_add":
        transaction.on_commit(lambda: on_commit_mentioned(action, pk_set, instance))


def on_commit_limited_visibilities(action, pks, instance):
    if action not in ("post_add", "post_remove"):
        return

    activity = instance.activities.order_by("-created").first()

    for id in pks:
        # Send out federation only if remote profile
        if not Profile.objects.filter(id=id, user__isnull=True).exists():
            continue
        profile = Profile.objects.get(id=id)

        if action == "post_add":
            try:
                federate_content(instance, recipient=profile, activity=activity)
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


def federate_content(content: Content, recipient: Profile = None, activity: Activity = None):
    """Send out local content to the federation layer.

    Yes, edits also. The federation layer should decide whether these are really worth sending out.
    # TODO also use activity type for federating?
    """
    recipient_id = recipient.id if recipient else None
    queue = django_rq.get_queue("highest")
    try:
        if content.content_type == ContentType.REPLY:
            queue.enqueue(send_reply, content.id, activity.fid)
        elif content.content_type == ContentType.SHARE:
            queue.enqueue(send_share, content.id, activity.fid)
        else:
            if content.visibility == Visibility.LIMITED and not recipient_id:
                return
            queue.enqueue(send_content, content.id, activity.fid, recipient_id=recipient_id)
    except Exception as ex:
        logger.exception("Failed to federate_content %s: %s", content, ex)
