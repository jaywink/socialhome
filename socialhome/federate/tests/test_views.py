import datetime
import json
import uuid
from unittest.mock import patch, Mock

from django.urls import reverse
from django.test.utils import override_settings
from django.utils.timezone import now
from federation.hostmeta.generators import NODEINFO_DOCUMENT_PATH
from federation.tests.fixtures.keys import get_dummy_private_key
from federation.utils.text import decode_if_bytes

from socialhome.content.enums import ContentType
from socialhome.content.models import Content
from socialhome.content.tests.factories import ContentFactory
from socialhome.enums import Visibility
from socialhome.federate.views import DiasporaReceiveViewMixin
from socialhome.tests.utils import SocialhomeTestCase
from socialhome.users.models import Profile, User
from socialhome.users.tests.factories import UserFactory


class TestFederationDiscovery(SocialhomeTestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.user = UserFactory(username="foobar")
        cls.profile = cls.user.profile
        cls.profile.rsa_public_key = "fooobar"
        cls.profile.save()

    def test_host_meta_responds(self):
        self.get("federate:host-meta")
        self.response_200()

    def test_webfinger_responds_404_on_unknown_user(self):
        self.get("{url}?q=barfoo%40socialhome.local".format(url=reverse("federate:webfinger")))
        self.response_404()

    def test_webfinger_responds_200_on_known_user(self):
        self.get("{url}?q=foobar%40socialhome.local".format(url=reverse("federate:webfinger")))
        self.response_200()
        self.get("{url}?q=acct%3Afoobar%40socialhome.local".format(url=reverse("federate:webfinger")))
        self.response_200()

    def test_hcard_responds_on_404_on_unknown_user(self):
        self.get("federate:hcard", uuid="fehwuyfehiufhewiuhfiuhuiewfew")
        self.response_404()
        with patch("socialhome.federate.views.get_object_or_404") as mock_get:
            # Test also ValueError raising ending up as 404
            mock_get.side_effect = ValueError()
            self.get("federate:hcard", uuid="foobar")
            self.response_404()

    def test_hcard_responds_on_200_on_known_user(self):
        self.get("federate:hcard", uuid=self.user.profile.uuid)
        self.response_200()

    def test_nodeinfo_wellknown_responds(self):
        self.get("federate:nodeinfo-wellknown")
        self.response_200()

    def test_nodeinfo_responds(self):
        self.get("federate:nodeinfo")
        self.response_200()

    def test_social_relay_responds(self):
        self.get("federate:social-relay")
        self.response_200()


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


class TestReceivePublic(SocialhomeTestCase):
    def test_receive_public_responds(self):
        self.post("federate:receive-public", data={"xml": "foo"})
        self.assertEqual(self.last_response.status_code, 202)


class TestReceiveUser(SocialhomeTestCase):
    def test_receive_user_responds_for_xml_payload(self):
        self.post("federate:receive-user", uuid=str(uuid.uuid4()), data={"xml": "foo"})
        self.assertEqual(self.last_response.status_code, 202)

    def test_receive_user_responds_for_json_payload(self):
        self.post(
            "federate:receive-user", uuid=str(uuid.uuid4()), data='{"foo": "bar"}',
            extra={"content_type": "application/json"},
        )
        self.assertEqual(self.last_response.status_code, 202)


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
        response = self.client.get(reverse("federate:content-xml", kwargs={"uuid": self.limited_content.uuid}))
        self.assertEqual(response.status_code, 404)

    def test_public_content_returns_success_code(self):
        response = self.client.get(reverse("federate:content-xml", kwargs={"uuid": self.public_content.uuid}))
        self.assertEqual(response.status_code, 200)

    @patch("socialhome.federate.views.make_federable_content")
    @patch("socialhome.federate.views.get_full_xml_representation", return_value="<foo></foo>")
    def test_calls_make_federable_content(self, mock_getter, mock_maker):
        self.client.get(reverse("federate:content-xml", kwargs={"uuid": self.public_content.uuid}))
        mock_maker.assert_called_once_with(self.public_content)

    @patch("socialhome.federate.views.make_federable_content", return_value="entity")
    @patch("socialhome.federate.views.get_full_xml_representation", return_value="<foo></foo>")
    def test_calls_get_full_xml_representation(self, mock_getter, mock_maker):
        self.client.get(reverse("federate:content-xml", kwargs={"uuid": self.public_content.uuid}))
        mock_getter.assert_called_once_with("entity", self.profile.private_key)


class TestContentFetchView(SocialhomeTestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        author = UserFactory()
        Profile.objects.filter(id=author.profile.id).update(
            rsa_private_key=get_dummy_private_key().exportKey().decode("utf-8")
        )
        cls.limited_content = ContentFactory(visibility=Visibility.LIMITED, author=author.profile)
        cls.public_content = ContentFactory(visibility=Visibility.PUBLIC, author=author.profile)
        cls.remote_content = ContentFactory(visibility=Visibility.PUBLIC)

    def test_invalid_objtype_returns_404(self):
        response = self.client.get(reverse("federate:content-fetch", kwargs={
            "objtype": "foobar", "uuid": self.public_content.uuid
        }))
        self.assertEqual(response.status_code, 404)

    def test_non_public_content_returns_404(self):
        response = self.client.get(reverse("federate:content-fetch", kwargs={
            "objtype": "post", "uuid": self.limited_content.uuid
        }))
        self.assertEqual(response.status_code, 404)

    def test_public_content_returns_success_code(self):
        response = self.client.get(reverse("federate:content-fetch", kwargs={
            "objtype": "post", "uuid": self.public_content.uuid
        }))
        self.assertEqual(response.status_code, 200)

    def test_remote_content_redirects(self):
        response = self.client.get(reverse("federate:content-fetch", kwargs={
            "objtype": "post", "uuid": self.remote_content.uuid
        }))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, "https://%s/fetch/post/%s" %(
            self.remote_content.author.handle.split("@")[1], self.remote_content.uuid
        ))


class TestNodeInfoView(SocialhomeTestCase):
    @override_settings(SOCIALHOME_STATISTICS=False)
    def test_view_responds_stats_off(self):
        self.get(NODEINFO_DOCUMENT_PATH)
        self.response_200()
        self.assertEqual(
            json.loads(decode_if_bytes(self.last_response.content))["usage"],
            {"users": {}}
        )

    @override_settings(SOCIALHOME_STATISTICS=True)
    def test_view_responds_stats_on(self):
        self.get(NODEINFO_DOCUMENT_PATH)
        self.response_200()
        self.assertEqual(
            json.loads(decode_if_bytes(self.last_response.content))["usage"],
            {
                "users": {
                    "total": User.objects.count(),
                    "activeHalfyear": User.objects.filter(last_login__gte=now() - datetime.timedelta(days=180)).count(),
                    "activeMonth": User.objects.filter(last_login__gte=now() - datetime.timedelta(days=30)).count(),
                },
                "localPosts": Content.objects.filter(
                    author__user__isnull=False, content_type=ContentType.CONTENT).count(),
                "localComments": Content.objects.filter(
                    author__user__isnull=False, content_type=ContentType.REPLY).count(),
            }
        )
