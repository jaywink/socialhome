import logging

import django_rq
from django.conf import settings
from django.contrib.sites.models import Site
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils.timezone import now
from django.utils.translation import ugettext_lazy as _

from socialhome.content.enums import ContentType
from socialhome.content.models import Content
from socialhome.users.models import User, Profile

logger = logging.getLogger("socialhome")


def get_common_context():
    site = Site.objects.get_current()
    return {"site_name": site.name, "site_url": settings.SOCIALHOME_URL}


def get_root_content_participants(content, exclude_user=None):
    """Get participants in a root content.

    :param content: The root Content object
    :param exclude: A User object to exclude
    :returns: Set of User objects
    """
    # Author of parent content
    participants = User.objects.filter(profile__content__id=content.id)
    # Other replies
    participants = participants | User.objects.filter(profile__content__parent_id=content.id)
    # Shares
    participants = participants | User.objects.filter(profile__content__share_of_id=content.id)
    # Replies on shares
    participants = participants | User.objects.filter(profile__content__parent__share_of_id=content.id)
    if exclude_user:
        participants = participants.exclude(id=exclude_user.id)
    return set(participants)


def send_follow_notification(follower_id, followed_id):
    """Super simple you've been followed notification to a user."""
    if settings.DEBUG:
        return
    try:
        user = User.objects.get(profile__id=followed_id, is_active=True)
    except User.DoesNotExist:
        logger.warning("No active user with profile %s found for follow notification", followed_id)
        return
    try:
        follower = Profile.objects.get(id=follower_id)
    except Profile.DoesNotExist:
        logger.warning("No follower profile %s found for follow notifications", follower_id)
        return
    logger.info("send_follow_notification - Sending mail to %s", user.email)
    subject = _("New follower: %s" % follower.name_or_handle)
    context = get_common_context()
    context.update({
        "subject": subject, "actor_name": follower.name_or_handle,
        "actor_url": "%s%s" % (settings.SOCIALHOME_URL, follower.get_absolute_url()),
        "name": user.profile.name_or_handle,
    })
    send_mail(
        "%s%s" % (settings.EMAIL_SUBJECT_PREFIX, subject),
        render_to_string("notifications/follow.txt", context=context),
        settings.DEFAULT_FROM_EMAIL,
        [user.email],
        fail_silently=False,
        html_message=render_to_string("notifications/follow.html", context=context),
    )


def send_mention_notification(user_id, mention_profile_id, content_id):
    """Super simple you've been mentioned notification email."""
    if settings.DEBUG:
        return
    try:
        user = User.objects.get(id=user_id, is_active=True)
    except User.DoesNotExist:
        logger.warning("No active user %s found for mention notification", user_id)
        return
    try:
        content = Content.objects.get(id=content_id)
    except Content.DoesNotExist:
        logger.warning("No content found with id %s", content_id)
        return
    try:
        mention_profile = Profile.objects.get(id=mention_profile_id)
    except Profile.DoesNotExist:
        logger.warning("No profile found with id %s", mention_profile_id)
        return
    content_url = "%s%s" % (settings.SOCIALHOME_URL, content.get_absolute_url())
    subject = _("You have been mentioned")
    context = get_common_context()
    context.update({
        "subject": subject, "actor_name": mention_profile.name_or_handle,
        "actor_url": "%s%s" % (settings.SOCIALHOME_URL, mention_profile.get_absolute_url()),
        "content_url": content_url, "name": user.profile.name_or_handle,
    })
    send_mail(
        "%s%s" % (settings.EMAIL_SUBJECT_PREFIX, subject),
        render_to_string("notifications/mention.txt", context=context),
        settings.DEFAULT_FROM_EMAIL,
        [user.email],
        fail_silently=False,
        html_message=render_to_string("notifications/mention.html", context=context),
    )


def send_reply_notifications(content_id):
    """Super simple reply notification to content local participants.

    Until proper notifications is supported, just pop out an email.
    """
    if settings.DEBUG:
        return
    try:
        content = Content.objects.get(id=content_id, content_type=ContentType.REPLY)
    except Content.DoesNotExist:
        logger.warning("No reply content found with id %s", content_id)
        return
    root_content = content.root
    exclude_user = content.author.user if content.local else None
    participants = get_root_content_participants(root_content, exclude_user=exclude_user)
    if not participants:
        return
    subject = _("New reply to: %s" % root_content.short_text_inline)
    # TODO use fragment url to reply directly when available
    content_url = "%s%s" % (settings.SOCIALHOME_URL, root_content.get_absolute_url())
    context = get_common_context()
    context.update({
        "subject": subject, "actor_name": content.author.name_or_handle,
        "actor_url": "%s%s" % (settings.SOCIALHOME_URL, content.author.get_absolute_url()),
        "reply_text": content.text, "reply_rendered": content.rendered, "reply_url": content_url,
    })
    for participant in participants:
        context["name"] = participant.profile.name_or_handle
        logger.info("send_reply_notifications - Sending mail to %s", participant.email)
        send_mail(
            "%s%s" % (settings.EMAIL_SUBJECT_PREFIX, subject),
            render_to_string("notifications/reply.txt", context=context),
            settings.DEFAULT_FROM_EMAIL,
            [participant.email],
            fail_silently=False,
            html_message=render_to_string("notifications/reply.html", context=context),
        )


def send_share_notification(share_id):
    """Super simple you're content has been shared notification to a user."""
    if settings.DEBUG:
        return
    try:
        content = Content.objects.get(id=share_id, content_type=ContentType.SHARE, share_of__local=True)
    except Content.DoesNotExist:
        logger.warning("No share content found with id %s", share_id)
        return
    content_url = "%s%s" % (settings.SOCIALHOME_URL, content.share_of.get_absolute_url())
    subject = _("New share of: %s" % content.share_of.short_text_inline)
    context = get_common_context()
    context.update({
        "subject": subject, "actor_name": content.author.name_or_handle,
        "actor_url": "%s%s" % (settings.SOCIALHOME_URL, content.author.get_absolute_url()),
        "content_url": content_url, "name": content.share_of.author.name_or_handle,
    })
    send_mail(
        "%s%s" % (settings.EMAIL_SUBJECT_PREFIX, subject),
        render_to_string("notifications/share.txt", context=context),
        settings.DEFAULT_FROM_EMAIL,
        [content.share_of.author.user.email],
        fail_silently=False,
        html_message=render_to_string("notifications/share.html", context=context),
    )


def send_data_export_ready_notification(user_id):
    """
    Send notification to user that their data export is ready.
    """
    if settings.DEBUG:
        return
    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        logger.warning("No user found with id %s", user_id)
        return

    subject = _("Data export is ready for download")
    context = get_common_context()
    context.update({
        "download_url": "%s%s" % (settings.SOCIALHOME_URL, reverse("dynamic_preferences.user")),
        "name": user.profile.name_or_handle,
        "subject": subject,
    })
    send_mail(
        "%s%s" % (settings.EMAIL_SUBJECT_PREFIX, subject),
        render_to_string("notifications/data_export.txt", context=context),
        settings.DEFAULT_FROM_EMAIL,
        [user.email],
        fail_silently=False,
        html_message=render_to_string("notifications/data_export.html", context=context),
    )


def send_policy_document_update_notification(user_id, docs):
    """
    Send notification to user that policy documents have updates.
    """
    if settings.DEBUG:
        return
    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        logger.warning("No user found with id %s", user_id)
        return

    if docs == 'both':
        subject = _("Important updates to our Terms of Service and Privacy Policy documents")
    elif docs == 'privacypolicy':
        subject = _("Important updates to our Privacy Policy document")
    elif docs == 'tos':
        subject = _("Important updates to our Terms of Service document")
    else:
        raise ValueError('Invalid docs type')
    context = get_common_context()
    context.update({
        "docs": docs,
        "privacypolicy_url": "%s%s" % (settings.SOCIALHOME_URL, reverse("privacy-policy")),
        "tos_url": "%s%s" % (settings.SOCIALHOME_URL, reverse("terms-of-service")),
        "name": user.profile.name_or_handle,
        "subject": subject,
        "update_time": now(),
    })
    send_mail(
        "%s%s" % (settings.EMAIL_SUBJECT_PREFIX, subject),
        render_to_string("notifications/policy_document_update.txt", context=context),
        settings.DEFAULT_FROM_EMAIL,
        [user.email],
        fail_silently=False,
        html_message=render_to_string("notifications/policy_document_update.html", context=context),
    )


def send_policy_document_update_notifications(docs):
    """
    Queue sending policy document update notifications to users.
    """
    if settings.DEBUG:
        return

    users = User.objects.filter(emailaddress__verified=True).distinct()
    for user in users:
        try:
            django_rq.enqueue(send_policy_document_update_notification, user.id, docs)
        except Exception:
            logger.error("Failed to enqueue policy document update to user %s" % user.id)
