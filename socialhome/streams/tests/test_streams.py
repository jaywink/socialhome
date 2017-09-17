import random
from unittest import skip
from unittest.mock import patch, Mock, call

from django.contrib.auth.models import AnonymousUser
from django.db.models import Max

from socialhome.content.enums import ContentType
from socialhome.content.models import Content
from socialhome.content.tests.factories import (
    ContentFactory, PublicContentFactory, SiteContentFactory, SelfContentFactory, LimitedContentFactory)
from socialhome.streams.enums import StreamType
from socialhome.streams.streams import (
    BaseStream, FollowedStream, PublicStream, TagStream, add_to_redis, add_to_stream_for_users,
    update_streams_with_content, check_and_add_to_keys)
from socialhome.tests.utils import SocialhomeTestCase
from socialhome.users.tests.factories import UserFactory


@patch("socialhome.streams.streams.get_redis_connection")
@patch("socialhome.streams.streams.time.time", return_value=123.123)
class TestAddToRedis(SocialhomeTestCase):
    def test_adds_each_key(self, mock_time, mock_get):
        mock_zadd = Mock()
        mock_get.return_value = Mock(zadd=mock_zadd, zrank=Mock(return_value=None))
        add_to_redis(Mock(id=1), ["spam", "eggs"])
        calls = [
            call("spam", 123, "1"),
            call("eggs", 123, "1"),
        ]
        self.assertEqual(mock_zadd.call_args_list, calls)

    def test_returns_on_no_keys(self, mock_time, mock_get):
        mock_zadd = Mock()
        mock_get.return_value = Mock(zadd=mock_zadd, zrank=Mock(return_value=None))
        add_to_redis(Mock(), [])


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
        add_to_stream_for_users(self.content.id, "FollowedStream")
        stream = FollowedStream(user=self.user)
        mock_add.assert_called_once_with(self.content, [stream.get_key()])

    @patch("socialhome.streams.streams.check_and_add_to_keys")
    @patch("socialhome.streams.streams.CACHED_ANONYMOUS_STREAM_CLASSES", new=tuple())
    def test_calls_check_and_add_to_keys_for_each_user(self, mock_check):
        add_to_stream_for_users(self.content.id, "FollowedStream")
        mock_check.assert_called_once_with(FollowedStream, self.user, self.content, [])

    @skip("Add when anonymous user cached streams exist")
    @patch("socialhome.streams.streams.check_and_add_to_keys")
    def test_includes_anonymous_user_for_anonymous_user_streams(self, mock_check):
        add_to_stream_for_users(self.content.id, "ProfileAllStream", profile=self.profile)
        anon_call = mock_check.call_args_list[1]
        self.assertTrue(isinstance(anon_call[1], AnonymousUser))

    @patch("socialhome.streams.streams.Content.objects.filter")
    def test_returns_on_no_content_or_reply(self, mock_filter):
        add_to_stream_for_users(Content.objects.aggregate(max_id=Max("id")).get("max_id") + 1, PublicStream)
        self.assertFalse(mock_filter.called)
        add_to_stream_for_users(self.reply.id, PublicStream)
        self.assertFalse(mock_filter.called)

    @patch("socialhome.streams.streams.check_and_add_to_keys", return_value=True)
    def test_skips_if_not_cached_stream(self, mock_get):
        add_to_stream_for_users(self.content.id, "SpamStream")
        self.assertFalse(mock_get.called)
        add_to_stream_for_users(self.content.id, "PublicStream")
        self.assertFalse(mock_get.called)


class TestCheckAndAddToKeys(SocialhomeTestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.create_local_and_remote_user()
        cls.profile.following.add(cls.remote_profile)
        cls.content = PublicContentFactory()
        cls.remote_content = PublicContentFactory(author=cls.remote_profile)

    def test_adds_if_should_cache(self):
        self.assertEqual(
            check_and_add_to_keys(FollowedStream, self.user, self.remote_content, []),
            ["socialhome:streams:followed:%s" % self.user.id],
        )

    def test_does_not_add_if_shouldnt_cache(self):
        self.assertEqual(
            check_and_add_to_keys(FollowedStream, self.user, self.content, []),
            [],
        )


class TestUpdateStreamsWithContent(SocialhomeTestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.create_local_and_remote_user()
        cls.content = PublicContentFactory(author=cls.profile)
        cls.remote_content = PublicContentFactory()

    @patch("socialhome.streams.streams.django_rq.enqueue")
    @patch("socialhome.streams.streams.add_to_redis")
    @patch("socialhome.streams.streams.CACHED_STREAM_CLASSES", new=(FollowedStream, PublicStream))
    def test_adds_with_local_user(self, mock_add, mock_enqueue):
        update_streams_with_content(self.remote_content)
        self.assertFalse(mock_add.called)
        update_streams_with_content(self.content)
        mock_add.assert_called_once_with(self.content, ["socialhome:streams:public:%s" % self.user.id])

    @patch("socialhome.streams.streams.django_rq.enqueue")
    def test_enqueues_each_stream_to_rq(self, mock_enqueue):
        update_streams_with_content(self.content)
        mock_enqueue.assert_called_once_with(add_to_stream_for_users, self.content.id, "FollowedStream")

    def test_returns_if_reply(self):
        self.assertIsNone(update_streams_with_content(Mock(content_type=ContentType.REPLY)))


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
        mock_redis = Mock()
        mock_get.return_value = mock_redis
        self.stream.stream_type = StreamType.PUBLIC
        self.stream.get_cached_content_ids()
        # Skips zrevrank if not last_id
        self.assertFalse(mock_redis.zrevrank.called)
        # Calls zrevrange with correct parameters
        mock_redis.zrevrange.assert_called_once_with(self.stream.get_key(), 0, self.stream.paginate_by)
        mock_redis.reset_mock()
        # Calls zrevrank with last_id
        self.stream.last_id = self.content2.id
        mock_redis.zrevrank.return_value = 3
        self.stream.get_cached_content_ids()
        mock_redis.zrevrank.assert_called_once_with(self.stream.get_key(), self.content2.id)
        mock_redis.zrevrange.assert_called_once_with(self.stream.get_key(), 4, 4 + self.stream.paginate_by)

    @patch("socialhome.streams.streams.get_redis_connection")
    def test_get_cached_content_ids__returns_empty_list_if_outside_cached_ids(self, mock_get, mock_queryset):
        mock_redis = Mock(zrevrank=Mock(return_value=None))
        mock_get.return_value = mock_redis
        self.stream.stream_type = StreamType.PUBLIC
        self.stream.last_id = 123
        self.assertEqual(self.stream.get_cached_content_ids(), [])
        self.assertFalse(mock_redis.zrevrange.called)

    def test_get_content(self, mock_queryset):
        self.assertEqual([self.content2, self.content1], list(self.stream.get_content()))
        self.stream.last_id = self.content2.id
        self.assertEqual([self.content1], list(self.stream.get_content()))
        self.stream.last_id = self.content1.id
        self.assertEqual([], list(self.stream.get_content()))

    def test_get_content_ids_returns_right_ids_according_to_last_id_and_ordering(self, mock_queryset):
        self.assertEqual({self.content2.id, self.content1.id}, set(self.stream.get_content_ids()))
        self.stream.last_id = self.content2.id
        self.assertEqual({self.content1.id}, set(self.stream.get_content_ids()))
        self.stream.last_id = self.content1.id
        self.assertEqual(set(), set(self.stream.get_content_ids()))

        # Reverse
        self.stream.ordering = "created"
        self.stream.last_id = None
        self.assertEqual({self.content2.id, self.content1.id}, set(self.stream.get_content_ids()))
        self.stream.last_id = self.content1.id
        self.assertEqual({self.content2.id}, set(self.stream.get_content_ids()))
        self.stream.last_id = self.content2.id
        self.assertEqual(set(), set(self.stream.get_content_ids()))

    def test_get_content_ids_limits_by_paginate_by(self, mock_queryset):
        self.stream.paginate_by = 1
        self.assertEqual({self.content2.id}, set(self.stream.get_content_ids()))

    def test_init(self, mock_queryset):
        stream = BaseStream(last_id=333, user="user")
        self.assertEqual(stream.last_id, 333)
        self.assertEqual(stream.user, "user")

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

    def test_get_content_ids_uses_cached_ids(self):
        with patch.object(self.stream, "get_cached_content_ids") as mock_cached:
            self.stream.get_content_ids()
            mock_cached.assert_called_once_with()

    def test_get_content_ids_fills_in_non_cached_content_up_to_pagination_amount(self):
        with patch.object(self.stream, "get_cached_content_ids") as mock_cached:
            cached_ids = random.sample(range(10000, 100000), self.stream.paginate_by - 1)
            mock_cached.return_value = cached_ids
            # Fills up with one of the two that are available
            all_ids = set(cached_ids + [self.site_content.id])
            self.assertEqual(set(self.stream.get_content_ids()), all_ids)

    def test_get_key(self):
        self.assertEqual(self.stream.get_key(), "socialhome:streams:followed:%s" % self.user.id)

    def test_only_followed_profile_content_returned(self):
        self.assertEqual(
            {self.public_content, self.site_content},
            set(self.stream.get_content()),
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

    def test_get_key(self):
        self.assertEqual(self.stream.get_key(), "socialhome:streams:public:%s" % self.user.id)
        stream = PublicStream(user=AnonymousUser())
        self.assertEqual(stream.get_key(), "socialhome:streams:public:anonymous")

    def test_only_public_content_returned(self):
        self.assertEqual(
            {self.public_content},
            set(self.stream.get_content()),
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
        cls.limited_tagged = LimitedContentFactory(text="#foobar", author=cls.profile)
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

    def test_get_key(self):
        self.assertEqual(self.stream.get_key(), "socialhome:streams:tag:%s" % self.user.id)
        stream = PublicStream(user=AnonymousUser())
        self.assertEqual(stream.get_key(), "socialhome:streams:public:anonymous")

    def test_only_tagged_content_returned(self):
        self.assertEqual(
            {self.public_tagged},
            set(self.anon_stream.get_content()),
        )
        self.assertEqual(
            {self.public_tagged, self.site_tagged, self.self_tagged, self.limited_tagged},
            set(self.stream.get_content()),
        )
        self.assertEqual(
            {self.public_tagged, self.site_tagged},
            set(self.local_stream.get_content()),
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
