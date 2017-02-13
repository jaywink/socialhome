import pytest
from django.core.urlresolvers import reverse
from django.test import Client, TestCase

from socialhome.content.tests.factories import ContentFactory, TagFactory
from socialhome.enums import Visibility


@pytest.mark.usefixtures("db", "client")
class TestPublicStreamView(object):
    def test_renders_without_content(self, client):
        response = client.get(reverse("streams:public"))
        assert response.status_code == 200

    def test_renders_with_content(self, client):
        content = ContentFactory(visibility=Visibility.PUBLIC)
        response = client.get(reverse("streams:public"))
        assert response.status_code == 200
        assert content.text in str(response.content)

    def test_uses_correct_template(self, client):
        response = client.get(reverse("streams:public"))
        template_names = [template.name for template in response.templates]
        assert "streams/public.html" in template_names

    def test_contains_only_public_content(self, client):
        content = ContentFactory(visibility=Visibility.PUBLIC)
        site = ContentFactory(visibility=Visibility.SITE)
        selff = ContentFactory(visibility=Visibility.SELF)
        limited = ContentFactory(visibility=Visibility.LIMITED)
        response = client.get(reverse("streams:public"))
        assert content.text in str(response.content)
        assert site.text not in str(response.content)
        assert selff.text not in str(response.content)
        assert limited.text not in str(response.content)


class TestTagsStreamView(TestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.content = ContentFactory(text="#tag")
        cls.tag_no_content = TagFactory(name="tagnocontent")
        cls.client = Client()

    def test_context_data_is_ok(self):
        response = self.client.get(reverse("streams:tags", kwargs={"name": "tagnocontent"}))
        assert response.context["tag_name"] == "tagnocontent"

    def test_renders_without_content(self):
        response = self.client.get(reverse("streams:tags", kwargs={"name": "tagnocontent"}))
        assert "#%s" % self.tag_no_content.name in str(response.content)
        assert not response.context["content_list"]
        assert response.status_code == 200

    def test_renders_with_content(self):
        response = self.client.get(reverse("streams:tags", kwargs={"name": "tag"}))
        assert response.status_code == 200
        assert self.content.rendered in str(response.content)

    def test_uses_correct_template(self):
        response = self.client.get(reverse("streams:tags", kwargs={"name": "tagnocontent"}))
        template_names = [template.name for template in response.templates]
        assert "streams/tag.html" in template_names

    def test_contains_only_public_content(self):
        content = ContentFactory(text="#tag public", visibility=Visibility.PUBLIC)
        site = ContentFactory(text="#tag site", visibility=Visibility.SITE)
        selff = ContentFactory(text="#tag self", visibility=Visibility.SELF)
        limited = ContentFactory(text="#tag limited", visibility=Visibility.LIMITED)
        response = self.client.get(reverse("streams:tags", kwargs={"name": "tag"}))
        assert content.rendered in str(response.content)
        assert site.rendered not in str(response.content)
        assert selff.rendered not in str(response.content)
        assert limited.rendered not in str(response.content)
