from unittest.mock import patch

from django.test import RequestFactory
from django.urls import reverse

from socialhome.content.tests.factories import (
    PublicContentFactory, SiteContentFactory, SelfContentFactory, LimitedContentFactory)
from socialhome.streams.tests.utils import MockStream
from socialhome.streams.viewsets import StreamsAPIBaseView
from socialhome.tests.utils import SocialhomeAPITestCase


class TestFollowedStreamAPIView(SocialhomeAPITestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.create_local_and_remote_user()
        cls.remote_profile.followers.add(cls.profile)
        cls.content = PublicContentFactory(author=cls.remote_profile)
        PublicContentFactory()

    def test_followed_content_returned(self):
        with self.login(self.user):
            self.get("api-streams:followed")
        self.assertEqual(len(self.last_response.data), 1)
        self.assertEqual(self.last_response.data[0]["id"], self.content.id)

    def test_login_required(self):
        self.get("api-streams:followed")
        self.response_403()

    @patch("socialhome.streams.viewsets.ContentSerializer", autospec=True)
    def test_serializer_context(self, mock_serializer):
        request = RequestFactory().get("/")
        view = StreamsAPIBaseView()
        view.get(request)
        mock_serializer.assert_called_once_with([], many=True, context={"throughs": {}, "request": request})

    @patch("socialhome.streams.viewsets.FollowedStream")
    def test_users_correct_stream_class(self, mock_stream):
        mock_stream.return_value = MockStream()
        with self.login(self.user):
            self.get("api-streams:followed")
        mock_stream.assert_called_once_with(last_id=None, user=self.user)


class TestLimitedStreamAPIView(SocialhomeAPITestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.create_local_and_remote_user()
        cls.create_content_set()
        LimitedContentFactory()
        cls.limited_content.limited_visibilities.add(cls.profile)

    def test_limited_content_returned(self):
        with self.login(self.user):
            self.get("api-streams:limited")
        self.assertEqual(len(self.last_response.data), 2)
        self.assertEqual(
            {item['id'] for item in self.last_response.data},
            {self.limited_content.id, self.site_content.id},
        )

    def test_login_required(self):
        self.get("api-streams:limited")
        self.response_403()

    @patch("socialhome.streams.viewsets.LimitedStream")
    def test_users_correct_stream_class(self, mock_stream):
        mock_stream.return_value = MockStream()
        with self.login(self.user):
            self.get("api-streams:limited")
        mock_stream.assert_called_once_with(last_id=None, user=self.user)


class TestProfileAllStreamAPIView(SocialhomeAPITestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.create_local_and_remote_user()
        cls.content = PublicContentFactory(author=cls.remote_profile)
        SiteContentFactory(author=cls.profile)
        SelfContentFactory(author=cls.profile)
        LimitedContentFactory(author=cls.profile)

    def test_profile_content_returned(self):
        self.get("api-streams:profile-all", id=self.content.author.id)
        self.assertEqual(len(self.last_response.data), 1)
        self.assertEqual(self.last_response.data[0]["id"], self.content.id)

    @patch("socialhome.streams.viewsets.ProfileAllStream")
    def test_users_correct_stream_class(self, mock_stream):
        mock_stream.return_value = MockStream()
        with self.login(self.user):
            self.get("api-streams:profile-all", id=self.content.author.id)
        mock_stream.assert_called_once_with(last_id=None, profile=self.content.author, user=self.user)


class TestProfilePinnedStreamAPIView(SocialhomeAPITestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.create_local_and_remote_user()
        cls.content = PublicContentFactory(author=cls.remote_profile, pinned=True)
        PublicContentFactory(author=cls.remote_profile)
        SiteContentFactory(author=cls.profile, pinned=True)
        SelfContentFactory(author=cls.profile, pinned=True)
        LimitedContentFactory(author=cls.profile, pinned=True)

    def test_profile_content_returned(self):
        self.get("api-streams:profile-pinned", id=self.content.author.id)
        self.assertEqual(len(self.last_response.data), 1)
        self.assertEqual(self.last_response.data[0]["id"], self.content.id)

    @patch("socialhome.streams.viewsets.ProfilePinnedStream")
    def test_users_correct_stream_class(self, mock_stream):
        mock_stream.return_value = MockStream()
        with self.login(self.user):
            self.get("api-streams:profile-pinned", id=self.content.author.id)
        mock_stream.assert_called_once_with(last_id=None, profile=self.content.author, user=self.user)


class TestPublicStreamAPIView(SocialhomeAPITestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.content = PublicContentFactory()
        cls.content2 = PublicContentFactory()
        SiteContentFactory()
        SelfContentFactory()
        LimitedContentFactory()

    def test_public_content_returned(self):
        self.get("api-streams:public")
        self.assertEqual(len(self.last_response.data), 2)
        self.assertEqual(self.last_response.data[0]["id"], self.content2.id)
        self.assertEqual(self.last_response.data[1]["id"], self.content.id)

    def test_last_id_is_respected(self):
        self.get("%s?last_id=%s" % (reverse("api-streams:public"), self.content2.id))
        self.assertEqual(len(self.last_response.data), 1)
        self.assertEqual(self.last_response.data[0]["id"], self.content.id)

    @patch("socialhome.streams.viewsets.PublicStream")
    def test_users_correct_stream_class(self, mock_stream):
        mock_stream.return_value = MockStream()
        self.get("api-streams:public")
        mock_stream.assert_called_once_with(last_id=None)


class TestTagStreamAPIView(SocialhomeAPITestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.create_local_and_remote_user()
        cls.content = PublicContentFactory(text="#foobar")
        SiteContentFactory(text="#foobar")
        SelfContentFactory(text="#foobar")
        LimitedContentFactory(text="#foobar")

    def test_public_content_returned(self):
        self.get("api-streams:tag", name="foobar")
        self.assertEqual(len(self.last_response.data), 1)
        self.assertEqual(self.last_response.data[0]["id"], self.content.id)

    @patch("socialhome.streams.viewsets.TagStream")
    def test_users_correct_stream_class(self, mock_stream):
        mock_stream.return_value = MockStream()
        with self.login(self.user):
            self.get("api-streams:tag", name="foobar")
        mock_stream.assert_called_once_with(last_id=None, tag=self.content.tags.first(), user=self.user)
