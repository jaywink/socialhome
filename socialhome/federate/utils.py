# -*- coding: utf-8 -*-
import datetime

import pytz

from Crypto import Random
from Crypto.PublicKey import RSA
from django.conf import settings
from django.utils.timezone import make_aware


def generate_rsa_private_key():
    """Generate a new RSA private key."""
    rand = Random.new().read
    return RSA.generate(4096, rand)


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
