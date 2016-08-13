import pytest
from django.core.urlresolvers import reverse

from socialhome.content.tests.factories import ContentFactory
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
