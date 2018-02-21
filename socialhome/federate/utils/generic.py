import datetime

import pytz
from Crypto import Random
from Crypto.PublicKey import RSA
from django.conf import settings
from django.urls import reverse
from django.utils.timezone import make_aware
from federation.utils.diaspora import generate_diaspora_profile_id


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
