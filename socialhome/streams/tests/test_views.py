from django.contrib.auth.models import AnonymousUser
from django.urls import reverse
from django.test import Client

from socialhome.content.tests.factories import ContentFactory, TagFactory
from socialhome.enums import Visibility
from socialhome.streams.enums import StreamType
from socialhome.streams.views import PublicStreamView, TagStreamView, FollowedStreamView, LimitedStreamView
from socialhome.tests.utils import SocialhomeCBVTestCase
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
        view = self.get_instance(FollowedStreamView, request=self.get_request(self.user))
        self.assertEqual(
            view.get_json_context(),
            {
                "currentBrowsingProfileId": self.user.profile.id,
                "streamName": view.stream_name,
                "isUserAuthenticated": True,
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
            view.stream_name, "%s__%s" % (StreamType.FOLLOWED.value, self.user.username)
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
        view = self.get_instance(LimitedStreamView, request=self.get_request(self.user))
        self.assertEqual(
            view.get_json_context(),
            {
                "currentBrowsingProfileId": self.user.profile.id,
                "streamName": view.stream_name,
                "isUserAuthenticated": True,
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
        self.assertEqual(view.stream_name, StreamType.LIMITED.value)

    def test_stream_type_value(self):
        view = self.get_instance(LimitedStreamView)
        self.assertEqual(view.stream_type_value, StreamType.LIMITED.value)

    def test_uses_correct_template(self):
        with self.login(self.user):
            response = self.client.get(reverse("streams:limited"))
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
        view = self.get_instance(PublicStreamView, request=self.get_request(self.user))
        self.assertEqual(
            view.get_json_context(),
            {
                "currentBrowsingProfileId": self.user.profile.id,
                "streamName": view.stream_name,
                "isUserAuthenticated": True,
            }
        )
        view = self.get_instance(PublicStreamView, request=self.get_request(AnonymousUser()))
        self.assertEqual(
            view.get_json_context(),
            {
                "currentBrowsingProfileId": None,
                "streamName": view.stream_name,
                "isUserAuthenticated": False,
            }
        )

    def test_renders(self):
        response = self.client.get(reverse("streams:public"))
        self.assertEqual(response.status_code, 200)

    def test_stream_name(self):
        view = self.get_instance(PublicStreamView)
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
        cls.client = Client()

    def test_get_json_context(self):
        view = self.get_instance(TagStreamView, request=self.get_request(self.user))
        view.tag = self.tag_no_content
        self.assertEqual(
            view.get_json_context(),
            {
                "currentBrowsingProfileId": self.user.profile.id,
                "streamName": view.stream_name,
                "isUserAuthenticated": True,
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
            }
        )

    def test_renders(self):
        response = self.client.get(reverse("streams:tag", kwargs={"name": "tagnocontent"}))
        assert response.status_code == 200

    def test_stream_name(self):
        view = self.get_instance(TagStreamView)
        view.tag = self.content.tags.first()
        self.assertEqual(
            view.stream_name, "%s__%s" % (StreamType.TAG.value, view.tag.channel_group_name)
        )

    def test_stream_type_value(self):
        view = self.get_instance(TagStreamView)
        self.assertEqual(view.stream_type_value, StreamType.TAG.value)

    def test_uses_correct_template(self):
        response = self.client.get(reverse("streams:tag", kwargs={"name": "tagnocontent"}))
        template_names = [template.name for template in response.templates]
        assert "streams/base.html" in template_names
