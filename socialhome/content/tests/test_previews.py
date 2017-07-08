import datetime
from unittest.mock import patch

import requests
from django.db import DataError
from freezegun import freeze_time
from opengraph import OpenGraph
from pyembed.core import PyEmbedError
from pyembed.core.consumer import PyEmbedConsumerError
from pyembed.core.discovery import PyEmbedDiscoveryError

from socialhome.content.models import OpenGraphCache, OEmbedCache
from socialhome.content.previews import fetch_content_preview, fetch_og_preview, OEmbedDiscoverer, fetch_oembed_preview
from socialhome.content.tests.factories import ContentFactory, OpenGraphCacheFactory, OEmbedCacheFactory
from socialhome.tests.utils import SocialhomeTestCase


class MockOpenGraph(dict):
    @property
    def title(self):
        return self.__getitem__("title")

    @property
    def image(self):
        return self.__getitem__("image")


class TestFetchOgPreview(SocialhomeTestCase):
    @classmethod
    def setUpTestData(cls):
        super(TestFetchOgPreview, cls).setUpTestData()
        cls.content = ContentFactory()
        cls.nsfw_content = ContentFactory(text="foo #nsfw")
        cls.urls = ["https://example.com"]

    def test_if_cached_already_dont_fetch(self):
        opengraph = OpenGraphCacheFactory(url=self.urls[0])
        result = fetch_og_preview(self.content, self.urls)
        self.assertTrue(result)
        self.content.refresh_from_db()
        self.assertEqual(self.content.opengraph, opengraph)

    @patch("socialhome.content.previews.OpenGraph")
    def test_if_cached_already_but_older_than_7_days_then_fetch(self, og):
        with freeze_time(datetime.date.today() - datetime.timedelta(days=8)):
            OpenGraphCacheFactory(url=self.urls[0])
        fetch_og_preview(self.content, self.urls)
        og.assert_called_once_with(url=self.urls[0])

    @patch("socialhome.content.previews.OpenGraph._parse")
    def test_opengraph_data_cleared_before_fetching(self, og_parse):
        OpenGraph.__data__ = {"foo": "bar"}
        fetch_og_preview(self.content, self.urls)
        self.assertEqual(OpenGraph.__data__, {})

    @patch("socialhome.content.previews.OpenGraph")
    def test_opengraph_fetch_called(self, og):
        fetch_og_preview(self.content, self.urls)
        og.assert_called_once_with(url=self.urls[0])

    @patch("socialhome.content.previews.OpenGraph", side_effect=requests.exceptions.ConnectionError)
    def test_opengraph_connection_error_is_passed(self, og):
        result = fetch_og_preview(self.content, self.urls)
        self.assertFalse(result)

    @patch("socialhome.content.previews.OpenGraph")
    def test_opengraph_ignored_if_not_enough_attributes(self, og):
        og.return_value = {}
        result = fetch_og_preview(self.content, self.urls)
        self.assertFalse(result)
        og.return_value = {"foo": "bar"}
        result = fetch_og_preview(self.content, self.urls)
        self.assertFalse(result)

    @patch("socialhome.content.previews.OpenGraph")
    def test_opengraph_cache_created(self, og):
        og.return_value = MockOpenGraph({"title": "foo"})
        opengraph = fetch_og_preview(self.content, self.urls)
        self.assertEqual(opengraph.title, "foo")
        self.assertEqual(opengraph.description, "")
        self.assertEqual(opengraph.image, "")
        self.assertEqual(opengraph.url, self.urls[0])

    @patch("socialhome.content.previews.OpenGraph")
    def test_opengraph_cache_created_without_image_for_nsfw_content(self, og):
        og.return_value = MockOpenGraph({"title": "foo", "image": "https://domain.tld/pic.png"})
        opengraph = fetch_og_preview(self.nsfw_content, self.urls)
        self.assertEqual(opengraph.title, "foo")
        self.assertEqual(opengraph.description, "")
        self.assertEqual(opengraph.image, "")
        self.assertEqual(opengraph.url, self.urls[0])

    @patch("socialhome.content.previews.OpenGraphCache.objects.create", side_effect=DataError)
    @patch("socialhome.content.previews.OpenGraph")
    def test_opengraph_data_error_is_passed(self, og, create):
        og.return_value = MockOpenGraph({"title": "foo"})
        result = fetch_og_preview(self.content, self.urls)
        self.assertFalse(result)

    @patch("socialhome.content.previews.OpenGraphCache.objects.filter", return_value=OpenGraphCache.objects.none())
    @patch("socialhome.content.previews.OpenGraph")
    def test_opengraph_integrity_error_updates_with_existing_object(self, og, filter):
        opengraph = OpenGraphCacheFactory(url=self.urls[0])
        og.return_value = MockOpenGraph({"title": "foo"})
        result = fetch_og_preview(self.content, self.urls)
        self.assertEqual(opengraph, result)


class TestFetchContentPreview(SocialhomeTestCase):
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


class TestOEmbedDiscoverer:
    def test_oembed_discoverer_inits(self):
        OEmbedDiscoverer()


class TestFetchOEmbedPreview(SocialhomeTestCase):
    @classmethod
    def setUpTestData(cls):
        super(TestFetchOEmbedPreview, cls).setUpTestData()
        cls.content = ContentFactory()
        cls.urls = ["https://example.com"]

    def test_cache_not_updated_if_previous_found(self):
        OEmbedCacheFactory(url=self.urls[0])
        result = fetch_oembed_preview(self.content, self.urls)
        self.content.refresh_from_db()
        self.assertEqual(self.content.oembed, result)

    @patch("socialhome.content.previews.PyEmbed.embed", return_value="")
    def test_cache_updated_if_previous_found_older_than_7_days(self, embed):
        with freeze_time(datetime.date.today() - datetime.timedelta(days=8)):
            OEmbedCacheFactory(url=self.urls[0])
        fetch_oembed_preview(self.content, self.urls)
        embed.assert_called_once_with(self.urls[0])

    @patch("socialhome.content.previews.PyEmbed.embed", return_value="")
    def test_pyembed_called(self, embed):
        fetch_oembed_preview(self.content, self.urls)
        embed.assert_called_once_with(self.urls[0])

    def test_pyembed_errors_swallowed(self):
        for error in [PyEmbedError, PyEmbedDiscoveryError, PyEmbedConsumerError, ValueError]:
            with patch("socialhome.content.previews.PyEmbed.embed", side_effect=error):
                result = fetch_oembed_preview(self.content, self.urls)
                self.assertFalse(result)

    @patch("socialhome.content.previews.PyEmbed.embed", return_value="")
    def test_empty_oembed_skipped(self, embed):
        result = fetch_oembed_preview(self.content, self.urls)
        embed.assert_called_once_with(self.urls[0])
        self.assertFalse(result)

    @patch("socialhome.content.previews.PyEmbed.embed", return_value='foo width="50" height="100" bar')
    def test_oembed_width_corrected(self, embed):
        result = fetch_oembed_preview(self.content, self.urls)
        self.assertEqual(result.oembed, 'foo width="100%"  bar')

    @patch("socialhome.content.previews.PyEmbed.embed", return_value="foobar")
    def test_oembed_cache_created(self, embed):
        result = fetch_oembed_preview(self.content, self.urls)
        self.assertEqual(result.oembed, "foobar")
        self.content.refresh_from_db()
        self.assertEqual(self.content.oembed, result)

    @patch("socialhome.content.previews.OEmbedCache.objects.filter", return_value=OEmbedCache.objects.none())
    @patch("socialhome.content.previews.PyEmbed.embed", return_value="foobar")
    def test_integrityerror_updates_with_found_cache(self, embed, filter):
        oembed = OEmbedCacheFactory(url=self.urls[0])
        result = fetch_oembed_preview(self.content, self.urls)
        self.assertEqual(result, oembed)
