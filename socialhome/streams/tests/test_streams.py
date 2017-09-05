from unittest.mock import patch

from django.contrib.auth.models import AnonymousUser

from socialhome.content.models import Content
from socialhome.content.tests.factories import (
    ContentFactory, PublicContentFactory, SiteContentFactory, SelfContentFactory, LimitedContentFactory)
from socialhome.streams.streams import BaseStream, FollowedStream, PublicStream, TagStream
from socialhome.tests.utils import SocialhomeTestCase
from socialhome.users.tests.factories import UserFactory


@patch("socialhome.streams.streams.BaseStream.get_queryset", return_value=Content.objects.all())
class TestBaseStream(SocialhomeTestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.content1 = ContentFactory()
        cls.content2 = ContentFactory()

    def setUp(self):
        super().setUp()
        self.stream = BaseStream()

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


class TestFollowedStream(SocialhomeTestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.create_local_and_remote_user()
        cls.remote_profile.followers.add(cls.profile)
        cls.create_content_set(author=cls.remote_profile)
        PublicContentFactory()
        SiteContentFactory()
        SelfContentFactory()
        LimitedContentFactory()

    def setUp(self):
        super().setUp()
        self.stream = FollowedStream(user=self.user)

    def test_only_followed_profile_content_returned(self):
        self.assertEqual(
            {self.public_content, self.site_content},
            set(self.stream.get_content()),
        )

    def test_raises_if_no_user(self):
        self.stream.user = None
        with self.assertRaises(AttributeError):
            self.stream.get_content()


class TestPublicStream(SocialhomeTestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.create_content_set()

    def setUp(self):
        super().setUp()
        self.stream = PublicStream()

    def test_only_public_content_returned(self):
        self.assertEqual(
            {self.public_content},
            set(self.stream.get_content()),
        )


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
