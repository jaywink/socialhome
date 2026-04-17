from unittest.mock import patch

from ddt import data, ddt

from socialhome.content.tests.factories import PublicContentFactory
from socialhome.tests.utils import SocialhomeTestCase
from socialhome.users.tests.factories import PublicUserFactory


@ddt
class TestContentView(SocialhomeTestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.user = PublicUserFactory(username="foo")
        cls.content = PublicContentFactory(author=cls.user.profile)

    def test_get_without_or_with_wrong_headers_is_disallowed(self):
        for url in (
            f"/content/{self.content.pk}/",
            f"/content/{self.content.pk}/sluggity-slug/",
            f"/content/{self.content.uuid}/",
        ):
            self.get(url, extra={
                "HTTP_ACCEPT": "text/html",
                "SERVER_NAME": "127.0.0.1:8000",
            })
            self.response_405()
            self.get(url, extra={
                "SERVER_NAME": "127.0.0.1:8000",
            })
            self.response_405()

    @data(
        "application/json", "application/activity+json", "application/ld+json",
    )
    @patch("socialhome.federate.utils.entities.make_federable_content")
    def test_get_with_headers_calls_activitypub_code(self, header, mock_make_federable_content):
        for url in (
                f"/content/{self.content.pk}/",
                f"/content/{self.content.pk}/sluggity-slug/",
                f"/content/{self.content.uuid}/",
        ):
            try:
                self.get(url, extra={
                    "HTTP_ACCEPT": header,
                    "SERVER_NAME": "127.0.0.1:8000",
                })
            except TypeError:
                pass
            self.assertTrue(mock_make_federable_content.called)
            mock_make_federable_content.reset_mock()
