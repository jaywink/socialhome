import random
from unittest import mock
from unittest.mock import patch, Mock, call

from django.contrib.auth.models import AnonymousUser
from django.db.models import Max
from django.test import override_settings
from freezegun import freeze_time

from socialhome.content.models import Content, Tag
from socialhome.content.tests.factories import (
    ContentFactory, PublicContentFactory, SiteContentFactory, SelfContentFactory, LimitedContentFactory)
from socialhome.streams.enums import StreamType
from socialhome.streams.streams import (
    BaseStream, FollowedStream, PublicStream, TagStream, add_to_redis, add_to_streams_for_users,
    update_streams_with_content, check_and_add_to_keys, ProfileAllStream, ProfilePinnedStream, LocalStream, TagsStream,
    CACHED_STREAM_CLASSES, ALL_STREAMS)
from socialhome.tests.utils import SocialhomeTestCase
from socialhome.users.tests.factories import UserFactory, PublicUserFactory


@patch("socialhome.streams.streams.get_redis_connection")
@patch("socialhome.streams.streams.time.time", return_value=123.123)
class TestAddToRedis(SocialhomeTestCase):
    def test_adds_each_key(self, mock_time, mock_get):
        mock_hset = Mock()
        mock_zadd = Mock()
        mock_get.return_value = Mock(hset=mock_hset, zadd=mock_zadd, zrank=Mock(return_value=None))
        add_to_redis(Mock(id=2), Mock(id=1), ["spam", "eggs"])
        calls = [
            call("spam", {2: 123}),
            call("eggs", {2: 123}),
        ]
        self.assertEqual(mock_zadd.call_args_list, calls)
        calls = [
            call("spam:throughs", 2, 1),
            call("eggs:throughs", 2, 1),
        ]
        self.assertEqual(mock_hset.call_args_list, calls)

    def test_returns_on_no_keys(self, mock_time, mock_get):
        mock_zadd = Mock()
        mock_get.return_value = Mock(zadd=mock_zadd, zrank=Mock(return_value=None))
        add_to_redis(Mock(), Mock(), [])


class TestAddToStreamForUsers(SocialhomeTestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.create_local_and_remote_user()
        cls.content = PublicContentFactory()
        cls.profile.following.add(cls.content.author)
        cls.limited_content = LimitedContentFactory()
        cls.reply = PublicContentFactory(parent=cls.content)

    @patch("socialhome.streams.streams.add_to_redis")
    def test_calls_add_to_redis(self, mock_add):
        with patch("socialhome.users.models.User.recently_active", new_callable=mock.PropertyMock, return_value=True):
            add_to_streams_for_users(self.content.id, self.content.id, self.content.author.id)
        stream1 = FollowedStream(user=self.user)
        stream2 = ProfileAllStream(user=self.user, profile=self.content.author)
        mock_add.assert_called_once_with(self.content, self.content, [stream1.key, stream2.key])

    @patch("socialhome.streams.streams.check_and_add_to_keys", autospec=True)
    def test_calls_check_and_add_to_keys_for_each_user(self, mock_check):
        add_to_streams_for_users(self.content.id, self.content.id, self.content.author.id)
        calls = [call(cls, self.user, self.content, [], self.content.author, set(), False) for cls in ALL_STREAMS]
        assert mock_check.call_count == len(ALL_STREAMS)
        mock_check.assert_has_calls(calls, any_order=True)

    @patch("socialhome.streams.streams.check_and_add_to_keys", autospec=True)
    @override_settings(SOCIALHOME_STREAMS_PRECACHE_INACTIVE_DAYS=2)
    @freeze_time('2018-02-01')
    def test_calls_check_and_add_to_keys_for_each_user__skipping_inactives(self, mock_check):
        with freeze_time('2018-01-25'):
            PublicUserFactory()
        add_to_streams_for_users(self.content.id, self.content.id, self.content.author.id)
        # Would be called twice for each stream if inactives were not filtered out
        calls = [call(cls, self.user, self.content, [], self.content.author, set(), False) for cls in ALL_STREAMS]
        assert mock_check.call_count == len(ALL_STREAMS)
        mock_check.assert_has_calls(calls)

    @patch("socialhome.streams.streams.Content.objects.filter")
    def test_returns_on_no_content(self, mock_filter):
        add_to_streams_for_users(
            Content.objects.aggregate(max_id=Max("id")).get("max_id") + 1, Mock(), self.content.author.id,
        )
        self.assertFalse(mock_filter.called)


class TestCheckAndAddToKeys(SocialhomeTestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.create_local_and_remote_user()
        cls.profile.following.add(cls.remote_profile)
        cls.content = PublicContentFactory()
        cls.remote_content = PublicContentFactory(author=cls.remote_profile)
        cls.tagged_content = PublicContentFactory(text="#spam #eggs")
        cls.spam_tag = Tag.objects.get(name="spam")
        cls.eggs_tag = Tag.objects.get(name="eggs")

    def test_adds_if_should_cache(self):
        keys = []
        self.user.mark_recently_active()
        check_and_add_to_keys(
            FollowedStream, self.user, self.remote_content, keys, self.remote_profile, set(), False,
        )
        self.assertEqual(
            keys,
            ["sh:streams:followed:%s" % self.user.id],
        )

    @patch("socialhome.streams.streams.CACHED_STREAM_CLASSES", new=(TagStream,))
    def test_adds_to_multiple_stream_instances(self):
        keys = []
        self.user.mark_recently_active()
        check_and_add_to_keys(
            TagStream, self.user, self.tagged_content, keys, self.tagged_content.author, set(), False,
        )
        self.assertEqual(
            set(keys),
            {
                "sh:streams:tag:%s:%s" % (self.spam_tag.id, self.user.id),
                "sh:streams:tag:%s:%s" % (self.eggs_tag.id, self.user.id),
            },
        )

    def test_does_not_add_if_shouldnt_cache(self):
        keys = []
        check_and_add_to_keys(
            FollowedStream, self.user, self.content, keys, self.content.author, set(), False,
        )
        self.assertEqual(
            keys,
            [],
        )


class TestUpdateStreamsWithContent(SocialhomeTestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.create_local_and_remote_user()
        cls.content = PublicContentFactory(author=cls.profile)
        cls.remote_content = PublicContentFactory()
        cls.share = PublicContentFactory(share_of=cls.content)

    @patch("socialhome.streams.streams.django_rq.queues.DjangoRQ")
    @patch("socialhome.streams.streams.add_to_redis")
    @patch("socialhome.streams.streams.CACHED_STREAM_CLASSES", new=(FollowedStream, PublicStream))
    def test_adds_with_local_user(self, mock_add, mock_enqueue):
        update_streams_with_content(self.remote_content)
        self.assertFalse(mock_add.called)
        self.user.mark_recently_active()
        update_streams_with_content(self.content)
        mock_add.assert_called_once_with(self.content, self.content, ["sh:streams:public:%s" % self.user.id])


@patch("socialhome.streams.streams.BaseStream.get_queryset", return_value=Content.objects.all())
class TestBaseStream(SocialhomeTestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.user = UserFactory()
        cls.content1 = ContentFactory()
        cls.content2 = ContentFactory()

    def setUp(self):
        super().setUp()
        self.stream = BaseStream(user=self.user)

    def test___str__(self, mock_queryset):
        self.assertEqual(str(self.stream), "BaseStream (%s)" % str(self.user))

    @patch("socialhome.streams.streams.get_redis_connection")
    def test_get_cached_content_ids__calls(self, mock_get, mock_queryset):
        mock_redis = Mock(zrevrange=Mock(return_value=[]))
        mock_get.return_value = mock_redis
        self.stream.stream_type = StreamType.PUBLIC
        self.stream.get_cached_content_ids()
        # Skips zrevrank if not last_id
        self.assertFalse(mock_redis.zrevrank.called)
        # Calls zrevrange with correct parameters
        mock_redis.zrevrange.assert_called_once_with(self.stream.key, 0, self.stream.paginate_by)
        mock_redis.reset_mock()
        # Calls zrevrank with last_id
        self.stream.last_id = self.content2.id
        mock_redis.zrevrank.return_value = 3
        self.stream.get_cached_content_ids()
        mock_redis.zrevrank.assert_called_once_with(self.stream.key, self.content2.id)
        mock_redis.zrevrange.assert_called_once_with(self.stream.key, 4, 4 + self.stream.paginate_by)

    @patch("socialhome.streams.streams.get_redis_connection")
    def test_get_cached_content_ids__returns_empty_list_if_outside_cached_ids(self, mock_get, mock_queryset):
        mock_redis = Mock(zrevrank=Mock(return_value=None))
        mock_get.return_value = mock_redis
        self.stream.stream_type = StreamType.PUBLIC
        self.stream.last_id = 123
        self.assertEqual(self.stream.get_cached_content_ids(), ([], {}))
        self.assertFalse(mock_redis.zrevrange.called)

    @patch("socialhome.streams.streams.get_redis_connection")
    def test_get_cached_range(self, mock_get, mock_queryset):
        self.stream.stream_type = StreamType.PUBLIC
        mock_zrevrange = Mock(return_value=[str(self.content2.id), str(self.content1.id)])
        mock_hmget = Mock(return_value=[str(self.content2.id), str(self.content1.id)])
        mock_redis = Mock(zrevrange=mock_zrevrange, hmget=mock_hmget)
        mock_get.return_value = mock_redis
        ids, throughs = self.stream.get_cached_range(0)
        self.assertEqual(ids, [self.content2.id, self.content1.id])
        self.assertEqual(throughs, {self.content2.id: self.content2.id, self.content1.id: self.content1.id})
        mock_zrevrange.assert_called_once_with(self.stream.key, 0, 0 + self.stream.paginate_by)
        mock_hmget.assert_called_once_with(BaseStream.get_throughs_key(self.stream.key), keys=[
            self.content2.id, self.content1.id,
        ])

        # Non-zero index
        mock_zrevrange.reset_mock()
        self.stream.get_cached_range(5)
        mock_zrevrange.assert_called_once_with(self.stream.key, 5, 5 + self.stream.paginate_by)

    def test_get_content(self, mock_queryset):
        qs, throughs = self.stream.get_content()
        self.assertEqual(set(qs), {self.content2, self.content1})
        self.assertEqual(throughs, {self.content2.id: self.content2.id, self.content1.id: self.content1.id})

        self.stream.last_id = self.content2.id
        qs, throughs = self.stream.get_content()
        self.assertEqual(set(qs), {self.content1})
        self.assertEqual(throughs, {self.content1.id: self.content1.id})

        self.stream.last_id = self.content1.id
        qs, throughs = self.stream.get_content()
        self.assertFalse(qs)
        self.assertFalse(throughs)

    def test_get_content_ids__returns_right_ids_according_to_last_id_and_ordering(self, mock_queryset):
        ids, throughs = self.stream.get_content_ids()
        self.assertEqual(ids, [self.content2.id, self.content1.id])
        self.assertEqual(throughs, {self.content2.id: self.content2.id, self.content1.id: self.content1.id})

        self.stream.last_id = self.content2.id
        ids, throughs = self.stream.get_content_ids()
        self.assertEqual(ids, [self.content1.id])
        self.assertEqual(throughs, {self.content1.id: self.content1.id})

        # Reverse
        self.stream.ordering = "created"
        self.stream.last_id = None

        ids, throughs = self.stream.get_content_ids()
        self.assertEqual(ids, [self.content1.id, self.content2.id])
        self.assertEqual(throughs, {self.content1.id: self.content1.id, self.content2.id: self.content2.id})

        self.stream.last_id = self.content1.id
        ids, throughs = self.stream.get_content_ids()
        self.assertEqual(ids, [self.content2.id])
        self.assertEqual(throughs, {self.content2.id: self.content2.id})

        self.stream.last_id = self.content2.id
        ids, throughs = self.stream.get_content_ids()
        self.assertFalse(ids)
        self.assertFalse(throughs)

    def test_get_content_ids__limits_by_paginate_by(self, mock_queryset):
        self.stream.paginate_by = 1
        ids, throughs = self.stream.get_content_ids()
        self.assertEqual(ids, [self.content2.id])
        self.assertEqual(throughs, {self.content2.id: self.content2.id})

    def test_get_content_ids__returns_cached_ids_if_enough_in_cache(self, mock_queryset):
        stream = FollowedStream(user=self.user)
        stream.paginate_by = 1
        with patch.object(stream, "get_queryset") as mock_queryset, \
                patch.object(stream, "get_cached_content_ids") as mock_cached:
            mock_cached.return_value = [self.content1.id], {self.content1.id: self.content1.id}
            stream.get_content_ids()
            self.assertEqual(mock_queryset.call_count, 0)

    def test_get_key_user_id(self, mock_queryset):
        self.assertEqual(BaseStream.get_key_user_id("spam:eggs:1"), 1)
        self.assertEqual(BaseStream.get_key_user_id("spam:eggs:1:throughs"), 1)
        self.assertEqual(BaseStream.get_key_user_id("spam:eggs:1:2"), 2)
        self.assertEqual(BaseStream.get_key_user_id("spam:eggs:1:2:throughs"), 2)
        self.assertIsNone(BaseStream.get_key_user_id("spam:eggs:anonymous"))
        self.assertIsNone(BaseStream.get_key_user_id("spam:eggs:anonymous:throughs"))

    def test_init(self, mock_queryset):
        stream = BaseStream(last_id=333, user="user")
        self.assertEqual(stream.last_id, 333)
        self.assertEqual(stream.user, "user")

    @patch("socialhome.streams.streams.get_redis_connection", return_value="redis")
    def test_init_redis_connection(self, mock_redis, mock_queryset):
        stream = BaseStream()
        self.assertIsNone(stream.redis)
        stream.init_redis_connection()
        mock_redis.assert_called_once_with()
        self.assertEqual(stream.redis, "redis")
        mock_redis.reset_mock()
        stream.init_redis_connection()
        self.assertFalse(mock_redis.called)

    def test_should_cache_content(self, mock_queryset):
        self.assertTrue(self.stream.should_cache_content(self.content1))
        self.assertTrue(self.stream.should_cache_content(self.content2))
        mock_queryset.return_value = Content.objects.none()
        self.assertFalse(self.stream.should_cache_content(self.content1))
        self.assertFalse(self.stream.should_cache_content(self.content2))


class TestFollowedStream(SocialhomeTestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.create_local_and_remote_user()
        cls.remote_profile.followers.add(cls.profile)
        cls.create_content_set(author=cls.remote_profile)
        cls.other_public_content = PublicContentFactory()
        SiteContentFactory()
        SelfContentFactory()
        LimitedContentFactory()

    def setUp(self):
        super().setUp()
        self.stream = FollowedStream(user=self.user)

    def test_get_content_ids__uses_cached_ids(self):
        with patch.object(self.stream, "get_cached_content_ids", return_value=([], {})) as mock_cached:
            self.stream.get_content_ids()
            mock_cached.assert_called_once_with()

    def test_get_content_ids__fills_in_non_cached_content_up_to_pagination_amount(self):
        with patch.object(self.stream, "get_cached_content_ids") as mock_cached:
            cached_ids = random.sample(range(10000, 100000), self.stream.paginate_by - 1)
            throughs = dict(zip(cached_ids, cached_ids))
            mock_cached.return_value = cached_ids, throughs
            # Fills up with one of the two that are available
            all_ids = set(cached_ids + [self.site_content.id])
            self.assertEqual(set(self.stream.get_content_ids()[0]), all_ids)

    def test_get_target_streams(self):
        self.assertEqual(
            len(FollowedStream.get_target_streams(self.public_content, self.user, self.public_content.author)), 1,
        )

    def test_get_throughs_key(self):
        self.assertEqual(
            self.stream.get_throughs_key(self.stream.key), "sh:streams:followed:%s:throughs" % self.user.id,
        )

    def test_key(self):
        self.assertEqual(self.stream.key, "sh:streams:followed:%s" % self.user.id)

    def test_only_followed_profile_content_returned(self):
        qs, _throughs = self.stream.get_content()
        self.assertEqual(
            set(qs),
            {self.public_content, self.site_content},
        )

    def test_raises_if_no_user(self):
        self.stream.user = None
        with self.assertRaises(AttributeError):
            self.stream.get_content()

    def test_should_cache_content(self):
        self.assertTrue(self.stream.should_cache_content(self.public_content))
        self.assertTrue(self.stream.should_cache_content(self.site_content))
        self.assertFalse(self.stream.should_cache_content(self.limited_content))
        self.assertFalse(self.stream.should_cache_content(self.self_content))
        self.assertFalse(self.stream.should_cache_content(self.other_public_content))


class TestLocalStream(SocialhomeTestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.user = UserFactory()
        cls.other_user = UserFactory()
        cls.create_content_set(author=cls.user.profile)
        cls.remote_content = PublicContentFactory()

    def setUp(self):
        super().setUp()
        self.stream = LocalStream(user=self.other_user)

    def test_get_target_streams(self):
        self.assertEqual(
            len(LocalStream.get_target_streams(self.public_content, self.other_user, self.public_content.author)), 1,
        )

    def test_key(self):
        self.assertEqual(self.stream.key, "sh:streams:local:%s" % self.other_user.id)

    def test_only_local_content_returned(self):
        qs, _throughs = self.stream.get_content()
        self.assertEqual(
            set(qs),
            {self.public_content, self.site_content},
        )

    def test_should_cache_content(self):
        self.assertTrue(self.stream.should_cache_content(self.public_content))
        self.assertTrue(self.stream.should_cache_content(self.site_content))
        self.assertFalse(self.stream.should_cache_content(self.limited_content))
        self.assertFalse(self.stream.should_cache_content(self.self_content))
        self.assertFalse(self.stream.should_cache_content(self.remote_content))


class TestProfileAllStream(SocialhomeTestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.create_local_and_remote_user()
        cls.create_content_set()
        cls.remote_profile_content = PublicContentFactory(author=cls.remote_profile)

    def setUp(self):
        super().setUp()
        self.stream = ProfileAllStream(user=self.user, profile=self.remote_profile)

    def test_get_content_ids__uses_cached_ids(self):
        with patch.object(self.stream, "get_cached_content_ids", return_value=([], {})) as mock_cached:
            self.stream.get_content_ids()
            mock_cached.assert_called_once_with()

    def test_get_queryset(self):
        qs = self.stream.get_queryset()
        self.assertEqual(set(qs), {self.remote_profile_content})

    def test_get_target_streams(self):
        self.assertEqual(
            len(ProfileAllStream.get_target_streams(self.public_content, self.user, self.public_content.author)), 1,
        )

    def test_key(self):
        self.assertEqual(self.stream.key, "sh:streams:profile_all:%s:%s" % (self.remote_profile.id, self.user.id))


class TestProfilePinnedStream(SocialhomeTestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.create_local_and_remote_user()
        cls.create_content_set()
        cls.pinned_content = PublicContentFactory(author=cls.profile, pinned=True)
        cls.non_pinned_content = PublicContentFactory(author=cls.profile)

    def setUp(self):
        super().setUp()
        self.stream = ProfilePinnedStream(user=self.user, profile=self.profile)

    def test_get_content_ids__does_not_use_cached_ids(self):
        with patch.object(self.stream, "get_cached_content_ids") as mock_cached:
            self.stream.get_content_ids()
            self.assertFalse(mock_cached.called)

    def test_get_queryset(self):
        qs = self.stream.get_queryset()
        self.assertEqual(set(qs), {self.pinned_content})

    def test_get_target_streams(self):
        self.assertEqual(
            len(ProfilePinnedStream.get_target_streams(self.pinned_content, self.user, self.pinned_content.author)), 1,
        )

    def test_key(self):
        self.assertEqual(self.stream.key, "sh:streams:profile_pinned:%s:%s" % (self.profile.id, self.user.id))


class TestPublicStream(SocialhomeTestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.user = UserFactory()
        cls.create_content_set()

    def setUp(self):
        super().setUp()
        self.stream = PublicStream(user=self.user)

    def test_get_content_ids_does_not_use_cached_ids(self):
        with patch.object(self.stream, "get_cached_content_ids") as mock_cached:
            self.stream.get_content_ids()
            self.assertFalse(mock_cached.called)

    def test_get_target_streams(self):
        self.assertEqual(
            len(PublicStream.get_target_streams(self.public_content, self.user, self.public_content.author)), 1,
        )

    def test_key(self):
        self.assertEqual(self.stream.key, "sh:streams:public:%s" % self.user.id)

    def test_only_public_content_returned(self):
        qs, _throughs = self.stream.get_content()
        self.assertEqual(
            set(qs),
            {self.public_content},
        )

    def test_should_cache_content(self):
        self.assertTrue(self.stream.should_cache_content(self.public_content))
        self.assertFalse(self.stream.should_cache_content(self.site_content))
        self.assertFalse(self.stream.should_cache_content(self.limited_content))
        self.assertFalse(self.stream.should_cache_content(self.self_content))


class TestTagStream(SocialhomeTestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.create_local_and_remote_user()
        cls.local_user = UserFactory()
        cls.create_content_set()
        cls.public_tagged = PublicContentFactory(text="#foobar", author=cls.profile)
        cls.site_tagged = SiteContentFactory(text="#foobar", author=cls.profile)
        cls.self_tagged = SelfContentFactory(text="#foobar", author=cls.profile)
        cls.limited_tagged = LimitedContentFactory(text="#foobar #spam #eggs", author=cls.profile)
        cls.tag = cls.public_tagged.tags.first()

    def setUp(self):
        super().setUp()
        self.stream = TagStream(tag=self.tag, user=self.user)
        self.anon_stream = TagStream(tag=self.tag, user=AnonymousUser())
        self.local_stream = TagStream(tag=self.tag, user=self.local_user)

    def test_get_content_ids_does_not_use_cached_ids(self):
        with patch.object(self.stream, "get_cached_content_ids") as mock_cached:
            self.stream.get_content_ids()
            self.assertFalse(mock_cached.called)

    def test_get_target_streams(self):
        self.assertEqual(
            len(TagStream.get_target_streams(self.limited_tagged, self.user, self.limited_tagged.author)), 3,
        )

    def test_key(self):
        self.assertEqual(self.stream.key, "sh:streams:tag:%s:%s" % (self.tag.id, self.user.id))

    def test_only_tagged_content_returned(self):
        qs, _throughs = self.anon_stream.get_content()
        self.assertEqual(
            set(qs),
            {self.public_tagged},
        )
        qs, _throughs = self.stream.get_content()
        self.assertEqual(
            set(qs),
            {self.public_tagged, self.site_tagged, self.self_tagged, self.limited_tagged},
        )
        qs, _throughs = self.local_stream.get_content()
        self.assertEqual(
            set(qs),
            {self.public_tagged, self.site_tagged},
        )

    def test_raises_if_no_user(self):
        self.stream.user = None
        with self.assertRaises(AttributeError):
            self.stream.get_content()

    def test_raises_if_no_tag(self):
        self.stream.tag = None
        with self.assertRaises(AttributeError):
            self.stream.get_content()

    def test_should_cache_content(self):
        # self.user stream
        self.assertTrue(self.stream.should_cache_content(self.public_tagged))
        self.assertTrue(self.stream.should_cache_content(self.site_tagged))
        self.assertTrue(self.stream.should_cache_content(self.limited_tagged))
        self.assertTrue(self.stream.should_cache_content(self.self_tagged))
        self.assertFalse(self.stream.should_cache_content(self.public_content))
        self.assertFalse(self.stream.should_cache_content(self.site_content))
        self.assertFalse(self.stream.should_cache_content(self.limited_content))
        self.assertFalse(self.stream.should_cache_content(self.self_content))
        # anon stream
        self.assertTrue(self.anon_stream.should_cache_content(self.public_tagged))
        self.assertFalse(self.anon_stream.should_cache_content(self.site_tagged))
        self.assertFalse(self.anon_stream.should_cache_content(self.limited_tagged))
        self.assertFalse(self.anon_stream.should_cache_content(self.self_tagged))
        self.assertFalse(self.anon_stream.should_cache_content(self.public_content))
        self.assertFalse(self.anon_stream.should_cache_content(self.site_content))
        self.assertFalse(self.anon_stream.should_cache_content(self.limited_content))
        self.assertFalse(self.anon_stream.should_cache_content(self.self_content))
        # self.local_user stream
        self.assertTrue(self.local_stream.should_cache_content(self.public_tagged))
        self.assertTrue(self.local_stream.should_cache_content(self.site_tagged))
        self.assertFalse(self.local_stream.should_cache_content(self.limited_tagged))
        self.assertFalse(self.local_stream.should_cache_content(self.self_tagged))
        self.assertFalse(self.local_stream.should_cache_content(self.public_content))
        self.assertFalse(self.local_stream.should_cache_content(self.site_content))
        self.assertFalse(self.local_stream.should_cache_content(self.limited_content))
        self.assertFalse(self.local_stream.should_cache_content(self.self_content))


class TestTagsStream(SocialhomeTestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.create_local_and_remote_user()
        cls.local_user = UserFactory()
        cls.create_content_set()
        cls.tagged_foobar = PublicContentFactory(text="#foobar", author=cls.profile)
        cls.tagged_foobar2 = SiteContentFactory(text="#foobar", author=cls.profile)
        cls.tagged_spam = PublicContentFactory(text="#spam", author=cls.profile)
        cls.tagged_spam2 = SiteContentFactory(text="#spam", author=cls.profile)
        cls.tag_foobar = Tag.objects.get(name="foobar")
        cls.tag_spam = Tag.objects.get(name="spam")
        cls.user.profile.followed_tags.add(cls.tag_spam)

    def setUp(self):
        super().setUp()
        self.stream = TagsStream(user=self.user)

    def test_only_followed_tagged_content_returned(self):
        qs, _throughs = self.stream.get_content()
        self.assertEqual(
            set(qs),
            {self.tagged_spam, self.tagged_spam2},
        )

    def test_raises_if_no_user(self):
        self.stream.user = None
        with self.assertRaises(AttributeError):
            self.stream.get_content()
