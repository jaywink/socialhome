from django.core.urlresolvers import reverse
from django.test import Client, TestCase

from socialhome.content.tests.factories import ContentFactory, TagFactory
from socialhome.enums import Visibility
from socialhome.tests.utils import SocialhomeTestCase
from socialhome.users.tests.factories import UserFactory


class TestPublicStreamView(TestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.content = ContentFactory(visibility=Visibility.PUBLIC)
        cls.site = ContentFactory(visibility=Visibility.SITE)
        cls.selff = ContentFactory(visibility=Visibility.SELF)
        cls.limited = ContentFactory(visibility=Visibility.LIMITED)
        cls.user = UserFactory()
        cls.client = Client()

    def test_renders_without_content(self):
        response = self.client.get(reverse("streams:public"))
        assert response.status_code == 200

    def test_renders_with_content(self):
        response = self.client.get(reverse("streams:public"))
        assert response.status_code == 200
        assert self.content.text in str(response.content)

    def test_uses_correct_template(self):
        response = self.client.get(reverse("streams:public"))
        template_names = [template.name for template in response.templates]
        assert "streams/public.html" in template_names

    def test_contains_only_public_content(self):
        response = self.client.get(reverse("streams:public"))
        assert self.content.text in str(response.content)
        assert self.site.text not in str(response.content)
        assert self.selff.text not in str(response.content)
        assert self.limited.text not in str(response.content)

    def test_logged_in_user(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse("streams:public"))
        assert response.status_code == 200


class TestTagStreamView(TestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.content = ContentFactory(text="#tag")
        cls.tag_no_content = TagFactory(name="tagnocontent")
        cls.client = Client()

    def test_context_data_is_ok(self):
        response = self.client.get(reverse("streams:tag", kwargs={"name": "tagnocontent"}))
        assert response.context["tag_name"] == "tagnocontent"

    def test_renders_without_content(self):
        response = self.client.get(reverse("streams:tag", kwargs={"name": "tagnocontent"}))
        assert "#%s" % self.tag_no_content.name in str(response.content)
        assert not response.context["content_list"]
        assert response.status_code == 200

    def test_renders_with_content(self):
        response = self.client.get(reverse("streams:tag", kwargs={"name": "tag"}))
        assert response.status_code == 200
        assert self.content.rendered in str(response.content)

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


class TestFollowedStreamView(SocialhomeTestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.user = UserFactory()
        cls.user2 = UserFactory()
        cls.content = ContentFactory(visibility=Visibility.PUBLIC)
        cls.other_content = ContentFactory(visibility=Visibility.PUBLIC)
        cls.user.profile.following.add(cls.content.author)

    def test_context_data_is_ok(self):
        with self.login(self.user):
            self.get("streams:followed")
        self.assertContext("stream_name", "followed__%s" % self.user.username)

    def test_renders_without_content(self):
        with self.login(self.user2):
            response = self.get("streams:followed")
        self.assertContains(response, "Followed")
        self.assertEquals(len(response.context["content_list"]), 0)
        self.assertEquals(response.status_code, 200)

    def test_renders_with_content(self):
        with self.login(self.user):
            response = self.get("streams:followed")
        self.assertContains(response, "Followed")
        self.assertIsNotNone(response.context["content_list"])
        self.assertEquals(set(response.context["content_list"]), {self.content})
        self.assertEquals(response.status_code, 200)

    def test_uses_correct_template(self):
        with self.login(self.user):
            response = self.get("streams:followed")
        template_names = [template.name for template in response.templates]
        assert "streams/followed.html" in template_names

    def test_redirects_to_login_if_not_authenticated(self):
        self.assertLoginRequired("streams:followed")
