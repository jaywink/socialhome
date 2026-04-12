from unittest.mock import patch

from ddt import data, ddt
from django.test import override_settings
from socialhome.tests.utils import SocialhomeTestCase
from socialhome.users.tests.factories import PublicUserFactory


@ddt
class TestHomeView(SocialhomeTestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.user = PublicUserFactory(username="foo")

    @override_settings(SOCIALHOME_ROOT_PROFILE="foo")
    def test_get_without_or_with_wrong_headers_is_disallowed(self):
        self.get("/", extra={
            "HTTP_ACCEPT": "text/html",
            "SERVER_NAME": "127.0.0.1:8000",
        })
        self.response_405()
        self.get("/", extra={
            "SERVER_NAME": "127.0.0.1:8000",
        })
        self.response_405()

    @override_settings(SOCIALHOME_ROOT_PROFILE="foo")
    @data(
        "application/json", "application/activity+json", "application/ld+json",
    )
    @patch("socialhome.federate.utils.entities.make_federable_profile")
    def test_get_with_headers_calls_activitypub_code(self, header, mock_make_federable_profile):
        try:
            self.get("/", extra={
                "HTTP_ACCEPT": header,
                "SERVER_NAME": "127.0.0.1:8000",
            })
        except TypeError:
            pass
        self.assertTrue(mock_make_federable_profile.called)

    def test_ap_get_without_root_profile(self):
        self.get("/", extra={
            "HTTP_ACCEPT": "application/ld+json",
            "SERVER_NAME": "127.0.0.1:8000",
        })
        self.response_404()
