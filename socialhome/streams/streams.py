import datetime
import logging
import time
from typing import List, Tuple, Dict

import django_rq
from django.conf import settings
from django.contrib.auth.models import AnonymousUser
from django.db.models import Case, When, Q
from django.utils.functional import cached_property
from django.utils.timezone import now

from socialhome.content.enums import ContentType
from socialhome.content.models import Content
from socialhome.streams.consumers import notify_listeners
from socialhome.streams.enums import StreamType
from socialhome.users.models import User, Profile
from socialhome.users.utils import update_profiles
from socialhome.utils import get_redis_connection

logger = logging.getLogger("socialhome")


def add_to_redis(content, through, keys):
    """Add content to a list of Redis ordered sets.

    :param content: Content object to add
    :param through: Content through object. For example on shares, this is the linked share content object
    :param keys: List of keys to add to
    """
    if not keys:
        return
    r = get_redis_connection()
    for key in keys:
        rank = r.zrank(key, content.id)
        if rank:
            # If through is not content, update
            if content.id != through.id:
                throughs_key = BaseStream.get_throughs_key(key)
                r.hset(throughs_key, content.id, through.id)
        else:
            # Only add if not in the set already
            # This stops shares popping up more than once, for example
            r.zadd(key, {content.id: int(time.time())})
            r.expire(key, settings.REDIS_DEFAULT_EXPIRY)
            throughs_key = BaseStream.get_throughs_key(key)
            r.hset(throughs_key, content.id, through.id)
            r.expire(throughs_key, settings.REDIS_DEFAULT_EXPIRY)


def add_to_streams_for_users(content_id, through_id, acting_profile_id):
    """Add content to all user streams of one type and do notification of streams.

    Excludes author of content.

    This function is designed to be queued to RQ.
    """
    try:
        content = Content.objects.get(id=content_id)
    except Content.DoesNotExist:
        logger.warning("Stream.add_to_streams_for_users - content %s does not exist!", content_id)
        return
    try:
        through = Content.objects.get(id=through_id)
    except Content.DoesNotExist:
        logger.warning("Stream.add_to_streams_for_users - through content %s does not exist!", through_id)
        return
    try:
        acting_profile = Profile.objects.select_related("user").get(id=acting_profile_id)
    except Profile.DoesNotExist:
        logger.warning("Stream.add_to_streams_for_users - acting profile %s does not exist!", acting_profile_id)
        return

    qs = get_precache_users_qs(acting_profile)
    cache_keys = []
    notify_keys = set()
    counter = 0
    for stream_cls in ALL_STREAMS:
        # Cache for each active user`
        for user in qs.iterator():
            counter += 1
            check_and_add_to_keys(stream_cls, user, content, cache_keys, acting_profile, notify_keys,
                              through.content_type == ContentType.SHARE)
    logger.info(
        "Stream.add_to_streams_for_users - checked stream %s for %s users, adding to %s cache keys",
        stream_cls.__name__, counter, len(cache_keys),
    )
    add_to_redis(content, through, cache_keys)
    notify_listeners(content, notify_keys)


def check_and_add_to_keys(stream_cls, user, content, cache_keys, acting_profile, notify_keys, is_share):
    """Check if content should be added to this user stream and add to the keys if so.

    Also collect notify keys.

    :param stream_cls: Stream class to check against.
    :param user: User who to check with. This is the user who we're caching for, ie future stream viewing user.
    :param content: The Content object that we're checking for.
    :param cache_keys: List of existing stream keys to add to.
    :param acting_profile: The Profile object that caused this check. This could be either the one for the Content
        or a Profile doing a share.
    :param notify_keys: List of existing notify keys to add to.
    :param is_share: Boolean whether this is a shared content.
    """
    if stream_cls not in CACHED_STREAM_CLASSES and not user.recently_active:
        # Abort early to avoid unnecessary work if we're not intending to cache for this user
        # and we're also not intending to notify them
        return
    # noinspection PyCallingNonCallable
    streams = stream_cls.get_target_streams(content, user, acting_profile)
    for stream in streams:
        if stream.should_cache_content(content):
            if stream_cls in CACHED_STREAM_CLASSES and settings.SOCIALHOME_STREAMS_PRECACHE_SIZE:
                cache_keys.append(stream.key)
            if is_share and (not stream.notify_for_shares or acting_profile == getattr(user, "profile", None)):
                continue
            if user.recently_active:
                notify_keys.add(stream.notify_key)
        # Dynamic update of the reply_count
        if content.content_type == ContentType.REPLY:
            if stream.should_cache_content(content.root_parent):
                notify_keys.add(stream.notify_key)



def get_precache_users_qs(acting_profile):
    """
    Get User queryset for precaching.

    Users must have either been active or created within amount of days configured.

    :param acting_profile: Profile that caused the precaching ie author normally. Will be excluded if local.
    :return: QuerySet
    """
    check_time = now() - datetime.timedelta(days=settings.SOCIALHOME_STREAMS_PRECACHE_INACTIVE_DAYS)
    qs = User.objects.filter(is_active=True).filter(Q(last_login__gte=check_time) | Q(date_joined__gte=check_time))
    if acting_profile.is_local:
        qs = qs.exclude(id=acting_profile.user_id)
    return qs


def update_profile_for_streams(profile, event='profile'):
    redis = get_redis_connection()
    keys = redis.keys('asgi:group:*')
    notify_keys = [key.decode().split(':')[-1] for key in keys]
    notify_listeners(profile, notify_keys, event)



def update_streams_with_content(content, event='new'):
    """Handle content adding to streams.

    First adds to the author streams, then queues the rest of the user streams to a background job.
    """
    # TODO: implement update and delete activities in the UI
    if event != 'new': return
    # Store current acting profile
    acting_profile = content.author if not content.content_type == ContentType.REPLY else content.root_parent.author
    # The original is the "through" always, has importance in shares
    through = content
    if content.content_type == ContentType.SHARE:
        # If this is a share we want to cache the shared content, not the original
        content = content.share_of
    # Do author immediately
    keys = []
    notify_keys = set()
    if acting_profile.is_local:
        for stream_cls in ALL_STREAMS:
            check_and_add_to_keys(stream_cls, acting_profile.user, content, keys, acting_profile, notify_keys,
                                  through.content_type == ContentType.SHARE)
        add_to_redis(content, through, keys)
        notify_listeners(content, notify_keys, event)
    # Queue rest to RQ
    django_rq.enqueue(add_to_streams_for_users, content.id, through.id, acting_profile.id)
    # Notify about reply separately
    if content.content_type == ContentType.REPLY:
        # Content reply
        # TODO notify per user due to visibility
        notify_listeners(content, {"streams_content__%s" % content.root_parent.channel_group_name}, event)


class BaseStream:
    accept_ids = None
    last_id = None
    key_base = ["sh", "streams"]
    notify_for_shares = True
    ordering = "-created"
    paginate_by = 15
    redis = None
    stream_type = None

    def __init__(self, last_id: int = None, user: User = None, accept_ids: List = None, **kwargs):
        self.accept_ids = accept_ids or []
        self.last_id = last_id
        self.user = user

    def __str__(self):
        return "%s (%s)" % (self.__class__.__name__, self.user)

    def get_accept_ids_content_ids(self) -> Tuple[List, Dict]:
        self.init_redis_connection()
        ids = []
        throughs = {}
        qs = self.get_queryset()
        ids_throughs = qs.filter(id__in=self.accept_ids).values("id", "through").order_by(self.ordering)
        for item in ids_throughs:
            ids.append(item["id"])
            throughs[item["id"]] = item["through"]
        return ids, throughs

    def get_cached_content_ids(self):
        self.init_redis_connection()
        index = 0
        if self.last_id:
            last_index = self.redis.zrevrank(self.key, self.last_id)
            if not last_index:
                # This item is outside our cached ids, abort
                return [], {}
            index = last_index + 1
        return self.get_cached_range(index)

    def get_cached_range(self, index):
        self.init_redis_connection()
        raw_ids = self.redis.zrevrange(self.key, index, index + self.paginate_by)
        if not raw_ids:
            return [], {}
        ids = [int(x) for x in raw_ids]
        # Get throughs and make it a dict
        throughs = self.redis.hmget(self.get_throughs_key(self.key), keys=ids)
        throughs = {id: int(through) for id, through in zip(ids, throughs)}
        return ids, throughs

    def init_redis_connection(self):
        if not self.redis:
            self.redis = get_redis_connection()

    def get_content(self):
        """Get queryset of Content objects.

        Keep ordering as returned by the list of content id's.
        """
        if self.accept_ids:
            ids, throughs = self.get_accept_ids_content_ids()
        else:
            ids, throughs = self.get_content_ids()
        # Case/When tip thanks to https://stackoverflow.com/a/37648265/1489738
        preserved = Case(*[When(id=id, then=pos) for pos, id in enumerate(ids)])
        content = Content.objects.filter(id__in=ids)\
            .select_related("author__user", "share_of").prefetch_related("tags").order_by(preserved)
        update_profiles(content)
        return content, throughs

    def get_content_ids(self):
        """Get a list of content ID's."""
        ids = []
        throughs = {}
        if self.__class__ in CACHED_STREAM_CLASSES:
            ids, throughs = self.get_cached_content_ids()
            if len(ids) >= self.paginate_by:
                return ids, throughs
        remaining = self.paginate_by - len(ids)
        qs = self.get_queryset()
        if self.last_id:
            if self.ordering == "-created":
                qs = qs.filter(through__lt=self.last_id)
            else:
                qs = qs.filter(through__gt=self.last_id)
        # Get and fill remaining items
        ids_throughs = qs.values("id", "through").order_by(self.ordering)[:remaining]
        for item in ids_throughs:
            ids.append(item["id"])
            throughs[item["id"]] = item["through"]
        return ids, throughs

    def get_queryset(self, *args, **kwars):
        raise NotImplemented

    @classmethod
    def get_target_streams(cls, content, user, acting_profile):
        """Get a list of target instances of this class.

        Given a Content and User, this method defines the stream instances that this content should be
        cached for. Some streams have multiple versions, for example a Content can have many tags which all have
        their own stream instance of TagStream.
        """
        return [cls(user=user)]

    @staticmethod
    def get_throughs_key(key):
        return "%s:throughs" % key

    @cached_property
    def key(self):
        """
        Get stream instance key.

        Format: ``<keybase>:<streamtype>:<keyextra>:<user_id>|anonymous``

        :return: str
        """
        parts = self.key_base + [self.stream_type.value]
        if self.key_extra:
            # noinspection PyTypeChecker
            parts.append(self.key_extra)
        if isinstance(self.user, AnonymousUser):
            return ":".join(parts + ["anonymous"])
        return ":".join(parts + [str(self.user.id)])

    @staticmethod
    def get_key_user_id(key):
        """
        Return the key user ID part.

        This is always the last item in the key parts.

        :return: int or None if anonymous user key
        """
        value = key
        if value.endswith(':throughs'):
            value = value[:-9]
        user_id = value.split(':')[-1]
        if user_id == 'anonymous':
            return None
        return int(user_id)

    @property
    def key_extra(self):
        return None

    @property
    def notify_key(self) -> str:
        """
        Get stream notify key.

        Format: ``streams_<streamtype>__<notifykeyextra>``
        """
        key = f"streams_{self.stream_type.value}"
        if self.notify_key_extra:
            key = f"{key}__{self.notify_key_extra}"
        return key

    @property
    def notify_key_extra(self):
        return None

    def should_cache_content(self, content):
        return self.get_queryset(single_id=content.id)


class FollowedStream(BaseStream):
    stream_type = StreamType.FOLLOWED

    def get_queryset(self, single_id=None):
        return Content.objects.followed(self.user, single_id=single_id)

    @property
    def notify_key_extra(self):
        return self.user.id


class LimitedStream(BaseStream):
    stream_type = StreamType.LIMITED

    def get_queryset(self, single_id=None):
        return Content.objects.limited(self.user, single_id=single_id)

    @property
    def notify_key_extra(self):
        return self.user.id


class LocalStream(BaseStream):
    notify_for_shares = False
    stream_type = StreamType.LOCAL

    def get_queryset(self, single_id=None):
        return Content.objects.local(self.user, single_id=single_id)

    @property
    def notify_key_extra(self):
        return self.user.id


class ProfileStreamBase(BaseStream):
    def __init__(self, profile, **kwargs):
        super().__init__(**kwargs)
        self.profile = profile

    @classmethod
    def get_target_streams(cls, content, user, acting_profile):
        return [cls(user=user, profile=acting_profile)]

    @property
    def key_extra(self):
        return str(self.profile.id)

    @property
    def notify_key_extra(self):
        return f"{self.key_extra}__{self.user.id or 'anon'}"


class ProfileAllStream(ProfileStreamBase):
    stream_type = StreamType.PROFILE_ALL

    def get_queryset(self, single_id=None):
        return Content.objects.profile(self.profile, self.user, single_id=single_id)


class ProfilePinnedStream(ProfileStreamBase):
    notify_for_shares = False
    ordering = "order"
    paginate_by = 100  # The limit of pinned content visible
    stream_type = StreamType.PROFILE_PINNED

    def get_queryset(self, single_id=None):
        return Content.objects.profile_pinned(self.profile, self.user, single_id=single_id)


class PublicStream(BaseStream):
    notify_for_shares = False
    stream_type = StreamType.PUBLIC

    def get_queryset(self, single_id=None):
        return Content.objects.public(single_id=single_id)

    @property
    def notify_key_extra(self):
        return self.user.id


class TagStream(BaseStream):
    notify_for_shares = False
    stream_type = StreamType.TAG

    def __init__(self, tag, **kwargs):
        super().__init__(**kwargs)
        self.tag = tag

    def get_queryset(self, single_id=None):
        if not self.tag:
            raise AttributeError("TagStream is missing tag.")
        return Content.objects.tag(self.tag, self.user, single_id=single_id)

    @classmethod
    def get_target_streams(cls, content, user, acting_profile):
        return [cls(user=user, tag=tag) for tag in content.tags.all()]

    @property
    def key_extra(self):
        return str(self.tag.id)

    @property
    def notify_key_extra(self):
        return f"{self.key_extra}__{self.user.id or 'anon'}"


class TagsStream(BaseStream):
    notify_for_shares = False
    stream_type = StreamType.TAGS

    def get_queryset(self, single_id=None):
        return Content.objects.tags_followed_by_user(self.user, single_id=single_id)

    @property
    def notify_key_extra(self):
        return self.user.id


CACHED_STREAM_CLASSES = (
    FollowedStream,
    ProfileAllStream,
    TagsStream,
)

NON_CACHED_STREAM_CLASSES = (
    LimitedStream,
    LocalStream,
    ProfilePinnedStream,
    PublicStream,
    TagStream,
)

ALL_STREAMS = CACHED_STREAM_CLASSES + NON_CACHED_STREAM_CLASSES
