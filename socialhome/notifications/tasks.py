import logging

from django.conf import settings
from django.core.mail import send_mail
from django.urls import reverse

from socialhome.content.models import Content

logger = logging.getLogger("socialhome")


def send_reply_notification(content_id):
    """Super simple reply notification to content author.
    
    Until proper notifications is supported, just pop out an email.
    """
    if settings.DEBUG:
        # Don't send in development mode
        return
    try:
        content = Content.objects.get(id=content_id)
    except Content.DoesNotExist:
        logger.warning("No content found with id %s", content_id)
        return
    if not content.is_local:
        return
    content_url = "%s%s" % (
        settings.SOCIALHOME_URL,
        reverse("content:view-by-slug", kwargs={"pk": content.id, "slug": content.slug}),
    )
    send_mail(
        "New reply to your content",
        "There is a new reply to your content, see it here: %s" % content_url,
        settings.DEFAULT_FROM_EMAIL,
        [content.author.user.email],
        fail_silently=False,
    )
