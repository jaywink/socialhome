import datetime

import redis
import zoneinfo
from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import URLValidator
from django.utils.timezone import make_aware

redis_connection = None


def get_full_url(path):
    return "%s%s" % (settings.SOCIALHOME_URL, path)


def get_full_media_url(path):
    return "{url}{media}{path}".format(
        url=settings.SOCIALHOME_URL, media=settings.MEDIA_URL, path=path,
    )


def get_redis_connection():
    global redis_connection
    if redis_connection:
        return redis_connection
    redis_connection = redis.StrictRedis(
        host=settings.REDIS_HOST, port=settings.REDIS_PORT, db=settings.REDIS_DB, password=settings.REDIS_PASSWORD,
    )
    return redis_connection


def is_url(url):
    val = URLValidator()
    try:
        val(url)
    except ValidationError:
        return False
    return True


def safe_make_aware(value, timezone=None):
    """Set/replace the timezone, making naive
    datetime aware.
    """

    timezone = zoneinfo.ZoneInfo(timezone) if timezone else zoneinfo.ZoneInfo(settings.TIME_ZONE)
    return value.replace(tzinfo=timezone)
