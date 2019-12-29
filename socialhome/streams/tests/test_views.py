from django.contrib.auth.models import AnonymousUser
from django.urls import reverse
from django.test import Client

from socialhome.content.tests.factories import ContentFactory, TagFactory, PublicContentFactory
from socialhome.enums import Visibility
from socialhome.streams.enums import StreamType
from socialhome.streams.views import (
    PublicStreamView, TagStreamView, FollowedStreamView, LimitedStreamView, LocalStreamView, TagsStreamView)
from socialhome.tests.utils import SocialhomeCBVTestCase
from socialhome.users.serializers import ProfileSerializer
from socialhome.users.tests.factories import UserFactory, PublicUserFactory


class TestFollowedStreamView(SocialhomeCBVTestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.user = UserFactory()
        cls.user2 = UserFactory()
        cls.content = ContentFactory(visibility=Visibility.PUBLIC)
        cls.other_content = ContentFactory(visibility=Visibility.PUBLIC)
        cls.user.profile.following.add(cls.content.author)

    def test_get_json_context(self):
        request = self.get_request(self.user)
        view = self.get_instance(FollowedStreamView, request=request)
        profile = ProfileSerializer(request.user.profile, context={'request': request}).data
        self.assertEqual(
            view.get_json_context(),
            {
                "currentBrowsingProfileId": self.user.profile.id,
                "streamName": view.stream_name,
                "isUserAuthenticated": True,
                "ownProfile": profile,
            }
        )

    def test_renders_without_content(self):
        self.get(FollowedStreamView, request=self.get_request(self.user2))
        self.assertContains(self.last_response, "Followed")
        self.response_200()

    def test_renders_with_content(self):
        response = self.get(FollowedStreamView, request=self.get_request(self.user))
        self.assertContains(response, "Followed")
        self.assertEqual(response.status_code, 200)

    def test_stream_name(self):
        view = self.get_instance(FollowedStreamView, request=self.get_request(self.user))
        self.assertEqual(
            view.stream_name, "%s__%s" % (StreamType.FOLLOWED.value, self.user.id)
        )

    def test_stream_type_value(self):
        view = self.get_instance(FollowedStreamView)
        self.assertEqual(view.stream_type_value, StreamType.FOLLOWED.value)

    def test_uses_correct_template(self):
        response = self.get(FollowedStreamView, request=self.get_request(self.user))
        template_names = [template.name for template in response.templates]
        assert "streams/base.html" in template_names

    def test_redirects_to_login_if_not_authenticated(self):
        self.assertLoginRequired("streams:followed")


class TestLimitedStreamView(SocialhomeCBVTestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.content = ContentFactory(visibility=Visibility.PUBLIC)
        cls.site = ContentFactory(visibility=Visibility.SITE)
        cls.selff = ContentFactory(visibility=Visibility.SELF)
        cls.limited = ContentFactory(visibility=Visibility.LIMITED)
        cls.user = UserFactory()
        cls.client = Client()

    def test_get_json_context(self):
        request = self.get_request(self.user)
        view = self.get_instance(LimitedStreamView, request=request)
        profile = ProfileSerializer(request.user.profile, context={'request': request}).data
        self.assertEqual(
            view.get_json_context(),
            {
                "currentBrowsingProfileId": self.user.profile.id,
                "streamName": view.stream_name,
                "isUserAuthenticated": True,
                "ownProfile": profile,
            }
        )

    def test_renders(self):
        with self.login(self.user):
            response = self.client.get(reverse("streams:limited"))
        self.assertEqual(response.status_code, 200)

    def test_requires_being_logged_in(self):
        response = self.client.get(reverse("streams:limited"))
        self.assertEqual(response.status_code, 302)

    def test_stream_name(self):
        view = self.get_instance(LimitedStreamView)
        view.request = self.get_request(self.user)
        self.assertEqual(view.stream_name, f"{StreamType.LIMITED.value}__{self.user.id}")

    def test_stream_type_value(self):
        view = self.get_instance(LimitedStreamView)
        self.assertEqual(view.stream_type_value, StreamType.LIMITED.value)

    def test_uses_correct_template(self):
        with self.login(self.user):
            response = self.client.get(reverse("streams:limited"))
        template_names = [template.name for template in response.templates]
        self.assertIn("streams/base.html", template_names)


class TestLocalStreamView(SocialhomeCBVTestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.local_user = UserFactory()
        cls.content = ContentFactory(visibility=Visibility.PUBLIC, author=cls.local_user.profile)
        cls.remote_content = ContentFactory(visibility=Visibility.PUBLIC)
        cls.site = ContentFactory(visibility=Visibility.SITE, author=cls.local_user.profile)
        cls.selff = ContentFactory(visibility=Visibility.SELF, author=cls.local_user.profile)
        cls.limited = ContentFactory(visibility=Visibility.LIMITED)
        cls.user = UserFactory()
        cls.client = Client()

    def test_does_not_require_being_logged_in(self):
        response = self.client.get(reverse("streams:local"))
        self.assertEqual(response.status_code, 200)

    def test_get_json_context(self):
        request = self.get_request(self.user)
        view = self.get_instance(LocalStreamView, request=request)
        profile = ProfileSerializer(request.user.profile, context={'request': request}).data
        self.assertEqual(
            view.get_json_context(),
            {
                "currentBrowsingProfileId": self.user.profile.id,
                "streamName": view.stream_name,
                "isUserAuthenticated": True,
                "ownProfile": profile,
            }
        )

    def test_renders(self):
        with self.login(self.user):
            response = self.client.get(reverse("streams:local"))
        self.assertEqual(response.status_code, 200)

    def test_stream_name(self):
        view = self.get_instance(LocalStreamView)
        view.request = self.get_request(AnonymousUser())
        self.assertEqual(view.stream_name, StreamType.LOCAL.value)

    def test_stream_type_value(self):
        view = self.get_instance(LocalStreamView)
        self.assertEqual(view.stream_type_value, StreamType.LOCAL.value)

    def test_uses_correct_template(self):
        with self.login(self.user):
            response = self.client.get(reverse("streams:local"))
        template_names = [template.name for template in response.templates]
        self.assertIn("streams/base.html", template_names)


class TestPublicStreamView(SocialhomeCBVTestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.content = ContentFactory(visibility=Visibility.PUBLIC)
        cls.site = ContentFactory(visibility=Visibility.SITE)
        cls.selff = ContentFactory(visibility=Visibility.SELF)
        cls.limited = ContentFactory(visibility=Visibility.LIMITED)
        cls.user = UserFactory()
        cls.client = Client()

    def test_get_json_context(self):
        request = self.get_request(self.user)
        view = self.get_instance(PublicStreamView, request=request)
        profile = ProfileSerializer(request.user.profile, context={'request': request}).data
        self.assertEqual(
            view.get_json_context(),
            {
                "currentBrowsingProfileId": self.user.profile.id,
                "streamName": view.stream_name,
                "isUserAuthenticated": True,
                "ownProfile": profile,
            }
        )
        view = self.get_instance(PublicStreamView, request=self.get_request(AnonymousUser()))
        self.assertEqual(
            view.get_json_context(),
            {
                "currentBrowsingProfileId": None,
                "streamName": view.stream_name,
                "isUserAuthenticated": False,
                "ownProfile": {},
            }
        )

    def test_renders(self):
        response = self.client.get(reverse("streams:public"))
        self.assertEqual(response.status_code, 200)

    def test_stream_name(self):
        view = self.get_instance(PublicStreamView)
        view.request = self.get_request(AnonymousUser())
        self.assertEqual(view.stream_name, StreamType.PUBLIC.value)

    def test_stream_type_value(self):
        view = self.get_instance(PublicStreamView)
        self.assertEqual(view.stream_type_value, StreamType.PUBLIC.value)

    def test_uses_correct_template(self):
        response = self.client.get(reverse("streams:public"))
        template_names = [template.name for template in response.templates]
        assert "streams/base.html" in template_names

    def test_logged_in_user(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse("streams:public"))
        self.assertEqual(response.status_code, 200)


class TestTagStreamView(SocialhomeCBVTestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.user = PublicUserFactory()
        cls.content = ContentFactory(text="#tag")
        cls.tag_no_content = TagFactory(name="tagnocontent")
        cls.russian_tag = TagFactory(name="тег")
        cls.client = Client()

    def test_get_json_context(self):
        request = self.get_request(self.user)
        view = self.get_instance(TagStreamView, request=request)
        profile = ProfileSerializer(request.user.profile, context={'request': request}).data
        view.tag = self.tag_no_content
        self.assertEqual(
            view.get_json_context(),
            {
                "currentBrowsingProfileId": self.user.profile.id,
                "streamName": view.stream_name,
                "isUserAuthenticated": True,
                "ownProfile": profile,
            }
        )
        view = self.get_instance(TagStreamView, request=self.get_request(AnonymousUser()))
        view.tag = self.tag_no_content
        self.assertEqual(
            view.get_json_context(),
            {
                "currentBrowsingProfileId": None,
                "streamName": view.stream_name,
                "isUserAuthenticated": False,
                "ownProfile": {},
            }
        )

    def test_renders(self):
        response = self.client.get(reverse("streams:tag", kwargs={"name": "tagnocontent"}))
        assert response.status_code == 200

    def test_renders__by_uuid(self):
        response = self.client.get(reverse("streams:tag-by-uuid", kwargs={"uuid": self.russian_tag.uuid}))
        assert response.status_code == 200

    def test_stream_name(self):
        view = self.get_instance(TagStreamView)
        view.tag = self.content.tags.first()
        view.request = self.get_request(self.user)
        self.assertEqual(
            view.stream_name, f"{StreamType.TAG.value}__{view.tag.id}__{self.user.id}",
        )

    def test_stream_type_value(self):
        view = self.get_instance(TagStreamView)
        self.assertEqual(view.stream_type_value, StreamType.TAG.value)

    def test_uses_correct_template(self):
        response = self.client.get(reverse("streams:tag", kwargs={"name": "tagnocontent"}))
        template_names = [template.name for template in response.templates]
        assert "streams/base.html" in template_names


class TestTagsStreamView(SocialhomeCBVTestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.user = PublicUserFactory()
        cls.content_spam = PublicContentFactory(text="#spam")
        cls.content_eggs = PublicContentFactory(text="#eggs")
        cls.client = Client()

    def test_get_json_context(self):
        request = self.get_request(self.user)
        view = self.get_instance(TagsStreamView, request=request)
        profile = ProfileSerializer(request.user.profile, context={'request': request}).data
        self.assertEqual(
            view.get_json_context(),
            {
                "currentBrowsingProfileId": self.user.profile.id,
                "streamName": view.stream_name,
                "isUserAuthenticated": True,
                "ownProfile": profile,
            }
        )

    def test_renders(self):
        with self.login(self.user):
            response = self.client.get(reverse("streams:tags"))
        assert response.status_code == 200

    def test_requires_being_logged_in(self):
        response = self.client.get(reverse("streams:tags"))
        self.assertEqual(response.status_code, 302)

    def test_stream_name(self):
        view = self.get_instance(TagsStreamView)
        view.request = self.get_request(self.user)
        self.assertEqual(view.stream_name, f"{StreamType.TAGS.value}__{self.user.id}")

    def test_stream_type_value(self):
        view = self.get_instance(TagsStreamView)
        self.assertEqual(view.stream_type_value, StreamType.TAGS.value)

    def test_uses_correct_template(self):
        with self.login(self.user):
            response = self.client.get(reverse("streams:tags"))
        template_names = [template.name for template in response.templates]
        assert "streams/base.html" in template_names
