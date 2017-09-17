import logging
import time

import django_rq
from django.contrib.auth.models import AnonymousUser
from django.db.models import Case, When

from socialhome.content.enums import ContentType
from socialhome.content.models import Content
from socialhome.streams.enums import StreamType
from socialhome.users.models import User
from socialhome.utils import get_redis_connection

logger = logging.getLogger("socialhome")


def add_to_redis(content, keys):
    """Add content to a list of Redis ordered sets.

    :param content: Content object to add
    :param keys: List of keys to add to
    """
    if not keys:
        return
    r = get_redis_connection()
    content_id = str(content.id)
    for key in keys:
        # Only add if not in the set already
        # This stops shares popping up more than once, for example
        if not r.zrank(key, content_id):
            r.zadd(key, int(time.time()), content_id)


def add_to_stream_for_users(content_id, stream_cls_name):
    """Add content to all user streams of one type.

    Excludes author of content.

    This function is designed to be queued to RQ.
    """
    stream_cls = globals().get(stream_cls_name)
    if stream_cls not in CACHED_STREAM_CLASSES:
        return
    try:
        content = Content.objects.exclude(content_type=ContentType.REPLY).get(id=content_id)
    except Content.DoesNotExist:
        logger.warning("Stream.add_to_stream_for_users - content %s does not exist!", content_id)
        return
    qs = User.objects.filter(is_active=True)
    if content.author.is_local:
        qs = qs.exclude(id=content.author.user.id)
    keys = []
    # Cache for each active user
    for user in qs.iterator():
        keys = check_and_add_to_keys(stream_cls, user, content, keys)
    # Cache also as anonymous user
    if stream_cls in CACHED_ANONYMOUS_STREAM_CLASSES:
        keys = check_and_add_to_keys(stream_cls, AnonymousUser(), content, keys)
    add_to_redis(content, keys)


def check_and_add_to_keys(stream_cls, user, content, keys):
    """Check if content should be added to this user stream and add to the keys if so.

    :returns: Existing keys with key added
    """
    # noinspection PyCallingNonCallable
    stream = stream_cls(user=user)
    if stream.should_cache_content(content):
        keys.append(stream.get_key())
    return keys


def update_streams_with_content(content):
    """Handle content adding to streams.

    First adds to the author streams, then queues the rest of the user streams to a background job.
    """
    if content.content_type == ContentType.REPLY:
        # No need to do these just now
        return
    # Store author here just in case we switch content to the shared content
    author = content.author
    if content.content_type == ContentType.SHARE:
        # If this is a share we want to cache the shared content, not the original
        content = content.share_of
    # Do author immediately
    if author.is_local:
        keys = []
        for stream_cls in CACHED_STREAM_CLASSES:
            keys = check_and_add_to_keys(stream_cls, author.user, content, keys)
        add_to_redis(content, keys)
    # Queue rest to RQ
    for stream_cls in CACHED_STREAM_CLASSES:
        django_rq.enqueue(add_to_stream_for_users, content.id, stream_cls.__name__)


class BaseStream:
    last_id = None
    ordering = "-created"
    paginate_by = 15
    stream_type = None

    def __init__(self, last_id=None, user=None, **kwargs):
        self.last_id = last_id
        self.user = user

    def __str__(self):
        return "%s (%s)" % (self.__class__.__name__, self.user)

    def get_cached_content_ids(self):
        key = self.get_key()
        r = get_redis_connection()
        index = 0
        if self.last_id:
            last_index = r.zrevrank(key, self.last_id)
            if not last_index:
                # This item is outside our cached ids, abort
                return []
            index = last_index + 1
        return r.zrevrange(key, index, index + self.paginate_by)

    def get_content(self):
        """Get queryset of Content objects.

        Keep ordering as returned by the list of content id's.
        """
        content_ids = self.get_content_ids()
        # Case/When tip thanks to https://stackoverflow.com/a/37648265/1489738
        preserved = Case(*[When(id=id, then=pos) for pos, id in enumerate(content_ids)])
        return Content.objects.filter(id__in=content_ids)\
            .select_related("author__user", "share_of").prefetch_related("tags").order_by(preserved)

    def get_content_ids(self):
        """Get a list of content ID's."""
        ids = []
        if self.__class__ in CACHED_STREAM_CLASSES:
            ids = self.get_cached_content_ids()
            if len(ids) >= self.paginate_by:
                return ids
        remaining = self.paginate_by - len(ids)
        qs = self.get_queryset()
        if self.last_id:
            if self.ordering == "-created":
                qs = qs.filter(id__lt=self.last_id)
            else:
                qs = qs.filter(id__gt=self.last_id)
        ids.extend(qs.values_list("id", flat=True).order_by(self.ordering)[:remaining])
        return ids

    def get_queryset(self):
        raise NotImplemented

    def get_key(self):
        if isinstance(self.user, AnonymousUser):
            return "socialhome:streams:%s:anonymous" % self.stream_type.value
        return "socialhome:streams:%s:%s" % (self.stream_type.value, self.user.id)

    def should_cache_content(self, content):
        return self.get_queryset().filter(id=content.id).exists()


class FollowedStream(BaseStream):
    stream_type = StreamType.FOLLOWED

    def get_queryset(self):
        return Content.objects.followed(self.user)


class PublicStream(BaseStream):
    stream_type = StreamType.PUBLIC

    def get_queryset(self):
        return Content.objects.public()


class TagStream(BaseStream):
    stream_type = StreamType.TAG

    def __init__(self, tag, **kwargs):
        super().__init__(**kwargs)
        self.tag = tag

    def get_queryset(self):
        if not self.tag:
            raise AttributeError("TagStream is missing tag.")
        return Content.objects.tag(self.tag, self.user)


CACHED_STREAM_CLASSES = (
    FollowedStream,
    # TODO
    # ProfileAllStream,
)

CACHED_ANONYMOUS_STREAM_CLASSES = (
    # TODO
    # ProfileAllStream,
)
