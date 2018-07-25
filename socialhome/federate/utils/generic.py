import datetime

from django.conf import settings
from django.contrib.sites.models import Site
from django.utils.timezone import now

from socialhome import __version__ as version
from socialhome.content.enums import ContentType


def get_nodeinfo2_data():
    """
    Return data set for a NodeInfo2 document.
    """
    from socialhome.content.models import Content  # Circulars
    from socialhome.users.models import User  # Circulars
    site = Site.objects.get_current()
    data = {
        "server": {
            "baseUrl": settings.SOCIALHOME_URL,
            "name": site.name,
            "software": "socialhome",
            "version": version,
        },
        # TODO fix when relay is configurable
        "relay": "all",
        "openRegistrations": settings.ACCOUNT_ALLOW_REGISTRATION,
    }
    if settings.SOCIALHOME_STATISTICS:
        data.update({"usage": {
            "users": {
                "total": User.objects.count(),
                "activeHalfyear": User.objects.filter(last_login__gte=now() - datetime.timedelta(days=180)).count(),
                "activeMonth": User.objects.filter(last_login__gte=now() - datetime.timedelta(days=30)).count(),
                "activeWeek": User.objects.filter(last_login__gte=now() - datetime.timedelta(days=7)).count(),
            },
            "localPosts": Content.objects.filter(author__user__isnull=False, content_type=ContentType.CONTENT).count(),
            "localComments": Content.objects.filter(author__user__isnull=False, content_type=ContentType.REPLY).count(),
        }})
    if settings.SOCIALHOME_SHOW_ADMINS:
        data.update({"organization": {
            "contact": settings.ADMINS[0][1],
            "name": settings.ADMINS[0][0],
        }})
    return data
