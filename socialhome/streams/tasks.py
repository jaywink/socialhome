from datetime import datetime

from django.conf import settings

from socialhome.utils import get_redis_connection


def groom_redis_precaches():
    """Groom the Redis data for streams precaching."""
    r = get_redis_connection()
    keys = r.keys("sh:streams:*[^:throughs]")
    for key in keys:
        # Make the ordered set X items length at most
        r.zremrangebyrank(key, 0, -settings.SOCIALHOME_STREAMS_PRECACHE_SIZE)
        # Remove now obsolete throughs ID's from the throughs hash
        delkeys = []
        throughs_key = "%s:throughs" % key.decode("utf-8")
        for content_id, _through_id in r.hgetall(throughs_key).items():
            if r.zrank(key, int(content_id)) is None:
                delkeys.append(int(content_id))
        if delkeys:
            r.hdel(throughs_key, *delkeys)


def streams_tasks(scheduler):
    scheduler.schedule(
        scheduled_time=datetime.utcnow(),
        func=groom_redis_precaches,
        interval=60*60*24,  # a day
    )
