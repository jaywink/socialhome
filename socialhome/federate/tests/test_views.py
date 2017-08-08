from unittest.mock import patch, Mock

import pytest
from django.core.urlresolvers import reverse
from federation.tests.fixtures.keys import get_dummy_private_key

from socialhome.content.tests.factories import ContentFactory
from socialhome.enums import Visibility
from socialhome.federate.views import DiasporaReceiveViewMixin
from socialhome.tests.utils import SocialhomeTestCase
from socialhome.users.models import Profile
from socialhome.users.tests.factories import UserFactory


@pytest.mark.usefixtures("db", "client")
class TestFederationDiscovery:
    def test_host_meta_responds(self, client):
        response = client.get(reverse("federate:host-meta"))
        assert response.status_code == 200

    def test_webfinger_responds_404_on_unknown_user(self, client):
        response = client.get("{url}?q=foobar%40socialhome.local".format(url=reverse("federate:webfinger")))
        assert response.status_code == 404

    def test_webfinger_responds_200_on_known_user(self, client):
        UserFactory(username="foobar")
        Profile.objects.filter(user__username="foobar").update(rsa_public_key="fooobar")
        response = client.get("{url}?q=foobar%40socialhome.local".format(url=reverse("federate:webfinger")))
        assert response.status_code == 200
        response = client.get("{url}?q=acct%3Afoobar%40socialhome.local".format(url=reverse("federate:webfinger")))
        assert response.status_code == 200

    def test_hcard_responds_on_404_on_unknown_user(self, client):
        response = client.get(reverse("federate:hcard", kwargs={"guid": "fehwuyfehiufhewiuhfiuhuiewfew"}))
        assert response.status_code == 404
        with patch("socialhome.federate.views.get_object_or_404") as mock_get:
            # Test also ValueError raising ending up as 404
            Profile.objects.filter(user__username="foobar").update(rsa_public_key="fooobar")
            mock_get.side_effect = ValueError()
            response = client.get(reverse("federate:hcard", kwargs={"guid": "foobar"}))
            assert response.status_code == 404

    def test_hcard_responds_on_200_on_known_user(self, client):
        user = UserFactory(username="foobar")
        Profile.objects.filter(user__username="foobar").update(rsa_public_key="fooobar")
        response = client.get(reverse("federate:hcard", kwargs={"guid": user.profile.guid}))
        assert response.status_code == 200

    def test_nodeinfo_wellknown_responds(self, client):
        response = client.get(reverse("federate:nodeinfo-wellknown"))
        assert response.status_code == 200

    def test_nodeinfo_responds(self, client):
        response = client.get(reverse("federate:nodeinfo"))
        assert response.status_code == 200

    def test_social_relay_responds(self, client):
        response = client.get(reverse("federate:social-relay"))
        assert response.status_code == 200


class TestDiasporaReceiveViewMixin(SocialhomeTestCase):
    def test_returns_legacy_xml_payload(self):
        self.assertEqual(
            DiasporaReceiveViewMixin.get_payload_from_request(Mock(body="foobar", POST={"xml": "barfoo"})),
            "barfoo",
        )

    def test_returns_other_payload(self):
        self.assertEqual(
            DiasporaReceiveViewMixin.get_payload_from_request(Mock(body="foobar", POST={})),
            "foobar",
        )


@pytest.mark.usefixtures("db", "client")
class TestReceivePublic:
    def test_receive_public_responds(self, client):
        response = client.post(reverse("federate:receive-public"), {"xml": "foo"})
        assert response.status_code == 202


@pytest.mark.usefixtures("db", "client")
class TestReceiveUser:
    def test_receive_user_responds_for_xml_payload(self, client):
        response = client.post(reverse("federate:receive-user", kwargs={"guid": "1234"}), {"xml": "foo"})
        assert response.status_code == 202

    def test_receive_user_responds_for_json_payload(self, client):
        response = client.post(
            reverse("federate:receive-user", kwargs={"guid": "1234"}), data='{"foo": "bar"}',
            content_type="application/json",
        )
        assert response.status_code == 202


class TestContentXMLView(SocialhomeTestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.limited_content = ContentFactory(visibility=Visibility.LIMITED)
        author = UserFactory()
        author.profile.rsa_private_key = get_dummy_private_key().exportKey()
        author.profile.save()
        cls.public_content = ContentFactory(visibility=Visibility.PUBLIC, author=author.profile)
        cls.profile = author.profile

    def test_non_public_content_returns_404(self):
        response = self.client.get(reverse("federate:content-xml", kwargs={"guid": self.limited_content.guid}))
        self.assertEqual(response.status_code, 404)

    def test_public_content_returns_success_code(self):
        response = self.client.get(reverse("federate:content-xml", kwargs={"guid": self.public_content.guid}))
        self.assertEqual(response.status_code, 200)

    @patch("socialhome.federate.views.make_federable_content")
    @patch("socialhome.federate.views.get_full_xml_representation", return_value="<foo></foo>")
    def test_calls_make_federable_content(self, mock_getter, mock_maker):
        self.client.get(reverse("federate:content-xml", kwargs={"guid": self.public_content.guid}))
        mock_maker.assert_called_once_with(self.public_content)

    @patch("socialhome.federate.views.make_federable_content", return_value="entity")
    @patch("socialhome.federate.views.get_full_xml_representation", return_value="<foo></foo>")
    def test_calls_get_full_xml_representation(self, mock_getter, mock_maker):
        self.client.get(reverse("federate:content-xml", kwargs={"guid": self.public_content.guid}))
        mock_getter.assert_called_once_with("entity", self.profile.private_key)


class TestContentFetchView(SocialhomeTestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        author = UserFactory()
        Profile.objects.filter(id=author.profile.id).update(rsa_private_key=get_dummy_private_key().exportKey())
        cls.limited_content = ContentFactory(visibility=Visibility.LIMITED, author=author.profile)
        cls.public_content = ContentFactory(visibility=Visibility.PUBLIC, author=author.profile)
        cls.remote_content = ContentFactory(visibility=Visibility.PUBLIC)

    def test_invalid_objtype_returns_404(self):
        response = self.client.get(reverse("federate:content-fetch", kwargs={
            "objtype": "foobar", "guid": self.public_content.guid
        }))
        self.assertEqual(response.status_code, 404)

    def test_non_public_content_returns_404(self):
        response = self.client.get(reverse("federate:content-fetch", kwargs={
            "objtype": "post", "guid": self.limited_content.guid
        }))
        self.assertEqual(response.status_code, 404)

    def test_public_content_returns_success_code(self):
        response = self.client.get(reverse("federate:content-fetch", kwargs={
            "objtype": "post", "guid": self.public_content.guid
        }))
        self.assertEqual(response.status_code, 200)

    def test_remote_content_redirects(self):
        response = self.client.get(reverse("federate:content-fetch", kwargs={
            "objtype": "post", "guid": self.remote_content.guid
        }))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, "https://%s/fetch/post/%s" %(
            self.remote_content.author.handle.split("@")[1], self.remote_content.guid
        ))
