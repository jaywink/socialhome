import logging

from django.conf import settings
from django.core.mail import send_mail
from django.urls import reverse

from socialhome.content.models import Content
from socialhome.users.models import User

logger = logging.getLogger("socialhome")


def send_reply_notifications(content_id):
    """Super simple reply notification to content local participants.
    
    Until proper notifications is supported, just pop out an email.
    """
    if settings.DEBUG:
        # Don't send in development mode
        return
    try:
        content = Content.objects.get(id=content_id, parent__isnull=False)
    except Content.DoesNotExist:
        logger.warning("No reply content found with id %s", content_id)
        return
    parent = content.parent
    # Author of parent content
    participants = User.objects.filter(profile__content__id=parent.id)
    # Other replies
    participants = participants | User.objects.filter(profile__content__parent_id=parent.id)
    # Exclude actual reply author and make a set of emails
    participants = set(participants.exclude(profile=content.author).values_list("email", flat=True))
    if not participants:
        return
    parent_url = "%s%s" % (
        settings.SOCIALHOME_URL,
        reverse("content:view-by-slug", kwargs={"pk": parent.id, "slug": parent.slug}),
    )
    send_mail(
        "%sNew reply to content you have participated in" % settings.EMAIL_SUBJECT_PREFIX,
        "There is a new reply to content you have participated in, see it here: %s" % parent_url,
        settings.DEFAULT_FROM_EMAIL,
        participants,
        fail_silently=False,
    )
