from datetime import datetime, timedelta

from django.conf import settings
from django.utils.timezone import now

from socialhome.utils import get_redis_connection


def delete_redis_keys(pattern: str, only_without_expiry: bool = True):
    """
    Delete any keys matching pattern. Defaults to only those without expiry.
    """
    r = get_redis_connection()
    keys = r.keys(pattern)
    to_delete = []

    for key in keys:
        if only_without_expiry:
            delete = r.ttl(key) == -1
        else:
            delete = True
        if delete:
            to_delete.append(key)
        if len(to_delete) > 1000:
            r.delete(*to_delete)

    if to_delete:
        r.delete(*to_delete)


def get_precache_trim_size(user_activities, key):
    """
    Get user activity to decide what kind of trimming we need.

    :return: int
    """
    # Local imports since we load tasks before apps are loaded fully
    from socialhome.streams.streams import BaseStream
    from socialhome.users.models import User
    user_id = BaseStream.get_key_user_id(key)
    if not user_id:
        # Anonymous, trim as inactive
        return settings.SOCIALHOME_STREAMS_PRECACHE_INACTIVE_SIZE
    user_active = user_activities.get(user_id)
    if user_active is not None:
        # Trim according to activity
        return (
            settings.SOCIALHOME_STREAMS_PRECACHE_SIZE
            if user_active else settings.SOCIALHOME_STREAMS_PRECACHE_INACTIVE_SIZE
        )
    # Get user
    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        # Trim all
        return 0
    check_time = user.last_login if user.last_login else user.date_joined
    user_active = check_time >= now() - timedelta(days=settings.SOCIALHOME_STREAMS_PRECACHE_INACTIVE_DAYS)
    user_activities[user_id] = user_active
    # Trim according to activity
    return (
        settings.SOCIALHOME_STREAMS_PRECACHE_SIZE
        if user_active else settings.SOCIALHOME_STREAMS_PRECACHE_INACTIVE_SIZE
    )


def groom_redis_precaches():
    """Groom the Redis data for streams precaching."""
    r = get_redis_connection()
    user_activities = {}
    keys = r.keys("sh:streams:[a-z0-9_\-:]*")
    for key in keys:
        decoded_key = key.decode("utf-8")
        if decoded_key.endswith(':throughs'):
            # Skip throughs, we handle those separately below
            continue
        trim_size = get_precache_trim_size(user_activities, decoded_key)
        # Make the ordered set X items length at most
        r.zremrangebyrank(key, 0, -trim_size-1)
        # Remove now obsolete throughs ID's from the throughs hash
        throughs_key = "%s:throughs" % decoded_key
        if not r.zcount(key, '-inf', '+inf'):
            # No need to loop, we've removed everything
            r.delete(throughs_key)
            continue
        delkeys = []
        for content_id, _through_id in r.hgetall(throughs_key).items():
            if r.zrank(key, int(content_id)) is None:
                delkeys.append(int(content_id))
        if delkeys:
            r.hdel(throughs_key, *delkeys)


def streams_tasks(scheduler):
    # Clean up RQ jobs without expiry
    scheduler.schedule(
        scheduled_time=datetime.utcnow(),
        func=delete_redis_keys,
        args=["rq:job:*"],
        interval=60*60*24,  # every 24 hours
        timeout=60*60*2,  # 2 hours
    )
    # Groom redis precaches
    scheduler.schedule(
        scheduled_time=datetime.utcnow(),
        func=groom_redis_precaches,
        interval=60*60*3,  # every 3 hours
        timeout=60*60*2,  # 2 hours
    )
