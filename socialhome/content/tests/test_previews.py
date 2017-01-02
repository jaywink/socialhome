from unittest.mock import patch

from django.test import TestCase

from socialhome.content.previews import fetch_content_preview
from socialhome.content.tests.factories import ContentFactory


class TestFetchOgPreview(TestCase):
    @classmethod
    def setUpTestData(cls):
        super(TestFetchOgPreview, cls).setUpTestData()

    def setUp(self):
        super(TestFetchOgPreview, self).setUp()


class TestFetchContentPreview(TestCase):
    @classmethod
    def setUpTestData(cls):
        super(TestFetchContentPreview, cls).setUpTestData()
        cls.content = ContentFactory()

    @patch("socialhome.content.previews.find_urls_in_text", return_value=[])
    @patch("socialhome.content.previews.fetch_oembed_preview")
    @patch("socialhome.content.previews.fetch_og_preview")
    def test_find_urls_in_text_called(self, fetch_og, fetch_oembed, find_urls):
        fetch_content_preview(self.content)
        find_urls.assert_called_once_with(self.content.text)
        fetch_oembed.assert_not_called()
        fetch_og.assert_not_called()

    @patch("socialhome.content.previews.find_urls_in_text", return_value=["example.com"])
    @patch("socialhome.content.previews.fetch_oembed_preview", return_value="fooo")
    @patch("socialhome.content.previews.fetch_og_preview")
    def test_fetch_oembed_preview_called(self, fetch_og, fetch_oembed, find_urls):
        fetch_content_preview(self.content)
        fetch_oembed.assert_called_once_with(self.content, ["example.com"])
        fetch_og.assert_not_called()

    @patch("socialhome.content.previews.find_urls_in_text", return_value=["example.com"])
    @patch("socialhome.content.previews.fetch_oembed_preview", return_value=None)
    @patch("socialhome.content.previews.fetch_og_preview")
    def test_fetch_og_preview_called(self, fetch_og, fetch_oembed, find_urls):
        fetch_content_preview(self.content)
        fetch_og.assert_called_once_with(self.content, ["example.com"])
