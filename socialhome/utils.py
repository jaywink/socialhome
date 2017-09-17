import redis
from django.conf import settings


def get_full_media_url(path):
    return "{url}{media}{path}".format(
        url=settings.SOCIALHOME_URL, media=settings.MEDIA_URL, path=path,
    )


def get_redis_connection():
    return redis.StrictRedis(
        host=settings.REDIS_HOST, port=settings.REDIS_PORT, db=settings.REDIS_DB, password=settings.REDIS_PASSWORD,
    )
