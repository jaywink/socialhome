from django.contrib.auth.models import AnonymousUser
from django.core.urlresolvers import reverse
from django.test import Client

from socialhome.content.tests.factories import ContentFactory, TagFactory
from socialhome.enums import Visibility
from socialhome.streams.enums import StreamType
from socialhome.streams.views import PublicStreamView, TagStreamView, FollowedStreamView
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
        self.assertEquals(len(self.context["content_list"]), 0)
        self.response_200()

    def test_renders_with_content(self):
        response = self.get(FollowedStreamView, request=self.get_request(self.user))
        self.assertContains(response, "Followed")
        self.assertIsNotNone(response.context["content_list"])
        self.assertEquals(set(response.context["content_list"]), {self.content})
        self.assertEquals(response.status_code, 200)

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
        assert "streams/followed.html" in template_names

    def test_redirects_to_login_if_not_authenticated(self):
        self.assertLoginRequired("streams:followed")


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

    def test_renders_without_content(self):
        response = self.client.get(reverse("streams:public"))
        assert response.status_code == 200

    def test_renders_with_content(self):
        response = self.client.get(reverse("streams:public"))
        assert response.status_code == 200
        assert self.content.get_absolute_url() in str(response.content)

    def test_stream_name(self):
        view = self.get_instance(PublicStreamView)
        self.assertEqual(view.stream_name, StreamType.PUBLIC.value)

    def test_stream_type_value(self):
        view = self.get_instance(PublicStreamView)
        self.assertEqual(view.stream_type_value, StreamType.PUBLIC.value)

    def test_throughs_in_context(self):
        response = self.client.get(reverse("streams:public"))
        self.assertEqual(response.context["throughs"], {self.content.id: self.content.id})

    def test_uses_correct_template(self):
        response = self.client.get(reverse("streams:public"))
        template_names = [template.name for template in response.templates]
        assert "streams/public.html" in template_names

    def test_contains_only_public_content(self):
        response = self.client.get(reverse("streams:public"))
        assert self.content.get_absolute_url() in str(response.content)
        assert self.site.get_absolute_url() not in str(response.content)
        assert self.selff.get_absolute_url() not in str(response.content)
        assert self.limited.get_absolute_url() not in str(response.content)

    def test_logged_in_user(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse("streams:public"))
        assert response.status_code == 200


class TestTagStreamView(SocialhomeCBVTestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.user = PublicUserFactory()
        cls.content = ContentFactory(text="#tag")
        cls.tag_no_content = TagFactory(name="tagnocontent")
        cls.client = Client()

    def test_context_data_is_ok(self):
        response = self.client.get(reverse("streams:tag", kwargs={"name": "tagnocontent"}))
        assert response.context["tag_name"] == "tagnocontent"

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

    def test_renders_without_content(self):
        response = self.client.get(reverse("streams:tag", kwargs={"name": "tagnocontent"}))
        assert "#%s" % self.tag_no_content.name in str(response.content)
        assert not response.context["content_list"]
        assert response.status_code == 200

    def test_renders_with_content(self):
        response = self.client.get(reverse("streams:tag", kwargs={"name": "tag"}))
        assert response.status_code == 200
        assert self.content.rendered in str(response.content)

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
        assert "streams/tag.html" in template_names

    def test_contains_only_public_content(self):
        content = ContentFactory(text="#tag public", visibility=Visibility.PUBLIC)
        site = ContentFactory(text="#tag site", visibility=Visibility.SITE)
        selff = ContentFactory(text="#tag self", visibility=Visibility.SELF)
        limited = ContentFactory(text="#tag limited", visibility=Visibility.LIMITED)
        response = self.client.get(reverse("streams:tag", kwargs={"name": "tag"}))
        assert content.rendered in str(response.content)
        assert site.rendered not in str(response.content)
        assert selff.rendered not in str(response.content)
        assert limited.rendered not in str(response.content)
