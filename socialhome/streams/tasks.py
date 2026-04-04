import logging
from datetime import datetime, timedelta
from typing import List

from django.conf import settings
from django.utils.timezone import now

from socialhome.utils import get_redis_connection

logger = logging.getLogger("socialhome")


def delete_redis_keys(patterns: List[str], only_without_expiry: bool = True):
    """
    Delete any keys matching pattern. Defaults to only those without expiry.
    """
    r = get_redis_connection()
    for pattern in patterns:
        keys = r.scan_iter(pattern)
        to_delete = []
        logger.info("delete_redis_keys - Looking for keys matching %s", pattern)
        for key in keys:
            if only_without_expiry:
                delete = r.ttl(key) == -1
            else:
                delete = True
            if delete:
                logger.debug("delete_redis_keys - Queuing deletion of %s", key)
                to_delete.append(key)
            if len(to_delete) > 1000:
                logger.info("delete_redis_keys - Deleting %s keys from pattern %s", len(to_delete), pattern)
                r.delete(*to_delete)
                to_delete = []

        if to_delete:
            logger.info("delete_redis_keys - Deleting %s keys", len(to_delete))
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
    logger.debug("get_precache_trim_size - User ID: %s", user_id)
    if not user_id:
        # Anonymous, trim as inactive
        logger.debug("get_precache_trim_size - No User ID, trimming to %s", settings.SOCIALHOME_STREAMS_PRECACHE_INACTIVE_SIZE)
        return settings.SOCIALHOME_STREAMS_PRECACHE_INACTIVE_SIZE
    user_active = user_activities.get(user_id)
    if user_active is not None:
        # Trim according to activity
        size = settings.SOCIALHOME_STREAMS_PRECACHE_SIZE if user_active else settings.SOCIALHOME_STREAMS_PRECACHE_INACTIVE_SIZE
        logger.debug("get_precache_trim_size - first user activities check, User ID: %s, user_active %s, trimming to %s", user_id, user_active, size)
        return size
    # Get user
    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        # Trim all
        logger.debug("get_precache_trim_size - User ID: %s can't be found, trimming to zero", user_id)
        return 0
    check_time = user.last_login if user.last_login else user.date_joined
    user_active = check_time >= now() - timedelta(days=settings.SOCIALHOME_STREAMS_PRECACHE_INACTIVE_DAYS)
    user_activities[user_id] = user_active
    # Trim according to activity
    size = settings.SOCIALHOME_STREAMS_PRECACHE_SIZE if user_active else settings.SOCIALHOME_STREAMS_PRECACHE_INACTIVE_SIZE
    logger.debug("get_precache_trim_size - second user activities check, User ID: %s, user_active %s, trimming to %s", user_id, user_active, size)
    return size


def groom_redis_precaches():
    """Groom the Redis data for streams precaching."""
    r = get_redis_connection()
    user_activities = {}
    keys = r.scan_iter("sh:streams:[a-z0-9_\\-:]*")
    logger.info("groom_redis_precaches - Looking for stream keys to groom")
    deleted_keys = deleted_throughs = trimmed = 0
    for key in keys:
        decoded_key = key.decode("utf-8")
        if decoded_key.endswith(':throughs'):
            # Skip throughs, we handle those separately below
            continue
        trim_size = get_precache_trim_size(user_activities, decoded_key)
        # Make the ordered set X items length at most
        r.zremrangebyrank(key, 0, -trim_size-1)
        trimmed += 1
        logger.debug("groom_redis_precaches - Trimmed key %s to %s", key, trim_size)
        # Remove now obsolete throughs ID's from the throughs hash
        throughs_key = f"{decoded_key}:throughs"
        if not r.zcount(key, '-inf', '+inf'):
            # No need to loop, we've removed everything
            logger.debug("groom_redis_precaches - No throughs found for %s, deleting key", throughs_key)
            r.delete(throughs_key)
            deleted_keys += 1
            continue
        delkeys = []
        for content_id, _through_id in r.hgetall(throughs_key).items():
            if r.zrank(key, int(content_id)) is None:
                logger.debug("groom_redis_precaches - Adding %s to be deleted throughs key %s", content_id, throughs_key )
                delkeys.append(int(content_id))
        if delkeys:
            logger.debug("groom_redis_precaches - Deleting thoughs key %s total %s items", throughs_key, len(delkeys))
            r.hdel(throughs_key, *delkeys)
            deleted_throughs += len(delkeys)
    logger.info("groom_redis_precaches - Trimmed %s keys, deleted %s keys and %s related throughs", trimmed, deleted_keys, deleted_throughs)

def streams_tasks(scheduler):
    # Clean up RQ jobs without expiry
    logger.info("streams_tasks - Scheduling streams task: delete_redis_keys")
    scheduler.schedule(
        scheduled_time=datetime.utcnow(),
        func=delete_redis_keys,
        args=[["rq:job:*", "rq:results:*", "fed_cache:*"]],
        interval=60*60*24,  # every 24 hours
        timeout=60*60*2,  # 2 hours
    )
    # Groom redis precaches
    logger.info("streams_tasks - Scheduling streams task: groom_redis_precaches")
    scheduler.schedule(
        scheduled_time=datetime.utcnow(),
        func=groom_redis_precaches,
        interval=60*60*3,  # every 3 hours
        timeout=60*60*2,  # 2 hours
    )
