import logging

from django.conf import settings
from django.contrib.sites.models import Site
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.translation import ugettext_lazy as _

from socialhome.content.enums import ContentType
from socialhome.content.models import Content
from socialhome.users.models import User, Profile

logger = logging.getLogger("socialhome")


def get_common_context():
    site = Site.objects.get_current()
    return {"site_name": site.name, "site_url": settings.SOCIALHOME_URL}


def get_reply_participants(content):
    # Author of parent content
    participants = User.objects.filter(profile__content__id=content.parent.id)
    # Other replies
    participants = participants | User.objects.filter(profile__content__parent_id=content.parent.id)
    if content.parent.content_type == ContentType.SHARE:
        # Share replies too
        participants = participants | User.objects.filter(
            profile__content__parent__share_of_id=content.parent.share_of.id)
    # Exclude actual reply author
    participants = set(participants.exclude(profile=content.author))
    return participants


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
    subject = _("New follower: %s" % follower.handle)
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
    participants = get_reply_participants(content)
    if not participants:
        return
    if content.parent.content_type == ContentType.SHARE:
        parent = content.parent.share_of
    else:
        parent = content.parent
    subject = _("New reply to: %s" % parent.short_text_inline)
    # TODO use fragment url to reply directly when available
    content_url = "%s%s" % (settings.SOCIALHOME_URL, parent.get_absolute_url())
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
