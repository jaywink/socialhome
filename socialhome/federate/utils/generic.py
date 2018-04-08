import datetime

import pytz
from Crypto import Random
from Crypto.PublicKey import RSA
from django.conf import settings
from django.contrib.sites.models import Site
from django.urls import reverse
from django.utils.timezone import make_aware, now
from federation.utils.diaspora import generate_diaspora_profile_id

from socialhome import __version__ as version
from socialhome.content.enums import ContentType


def generate_rsa_private_key():
    """Generate a new RSA private key."""
    rand = Random.new().read
    return RSA.generate(4096, rand)


def get_diaspora_profile_by_handle(handle):
    """
    Return a local Profile suitable for the federation library profile using Diaspora handle.
    """
    from socialhome.users.models import Profile  # Circulars
    profile = Profile.objects.select_related('user').only('guid', 'user__username').get(handle=handle)
    profile_path = reverse("users:detail", kwargs={"username": profile.user.username})
    return {
        "id": generate_diaspora_profile_id(handle, profile.guid),
        "profile_path": profile_path,
        # We don't support atom feeds yet, but since diaspora has a bug currently (0.7.3.x),
        # we need to specify something here. Let's use the profile url here too.
        # TODO remove this once diaspora releases the bug fix
        "atom_path": profile_path,
    }


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


def is_dst(zonename):
    """Check if current time in a time zone is in dst.

    From: http://stackoverflow.com/a/19778845/1489738
    """
    tz = pytz.timezone(zonename)
    now = pytz.utc.localize(datetime.datetime.utcnow())
    return now.astimezone(tz).dst() != datetime.timedelta(0)


def safe_make_aware(value, timezone=None):
    """Safely call Django's make_aware to get aware datetime.

    Makes sure DST doesn't cause problems."""
    if not timezone:
        timezone = settings.TIME_ZONE
    return make_aware(value, is_dst=is_dst(timezone))
