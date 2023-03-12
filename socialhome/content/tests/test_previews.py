import datetime
from unittest.mock import patch

from django.db import DataError
from freezegun import freeze_time
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
        super().setUpTestData()
        cls.content = ContentFactory()
        cls.urls = ["https://example.com"]

    def test_if_cached_already_dont_fetch(self):
        opengraph = OpenGraphCacheFactory(url=self.urls[0])
        with freeze_time(datetime.date.today() + datetime.timedelta(days=3)):
            result = fetch_og_preview(self.content, self.urls)
        self.assertTrue(result)
        self.content.refresh_from_db()
        self.assertEqual(self.content.opengraph, opengraph)

    @patch("socialhome.content.previews.OpenGraph")
    def test_if_cached_already_but_older_than_7_days_then_fetch(self, og):
        OpenGraphCacheFactory(url=self.urls[0])
        with freeze_time(datetime.date.today() + datetime.timedelta(days=8)):
            fetch_og_preview(self.content, self.urls)
        og.assert_called_once_with(url=self.urls[0], parser="lxml")

    @patch("socialhome.content.previews.OpenGraph")
    def test_opengraph_fetch_called(self, og):
        fetch_og_preview(self.content, self.urls)
        og.assert_called_once_with(url=self.urls[0], parser="lxml")

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
        super().setUpTestData()
        cls.content = ContentFactory()

    @patch("socialhome.content.previews.find_urls_in_text", return_value=[], autospec=True)
    @patch("socialhome.content.previews.fetch_oembed_preview", autospec=True)
    @patch("socialhome.content.previews.fetch_og_preview", autospec=True)
    def test_find_urls_in_text_called(self, fetch_og, fetch_oembed, find_urls):
        fetch_content_preview(self.content)
        find_urls.assert_called_once_with(self.content.text)
        self.assertTrue(fetch_oembed.called is False)
        self.assertTrue(fetch_og.called is False)

    @patch("socialhome.content.previews.find_urls_in_text", return_value=["example.com"], autospec=True)
    @patch("socialhome.content.previews.fetch_oembed_preview", return_value="fooo", autospec=True)
    @patch("socialhome.content.previews.fetch_og_preview", autospec=True)
    def test_fetch_oembed_preview_called(self, fetch_og, fetch_oembed, find_urls):
        fetch_content_preview(self.content)
        fetch_oembed.assert_called_once_with(self.content, ["example.com"])
        self.assertTrue(fetch_og.called is False)

    @patch("socialhome.content.previews.find_urls_in_text", return_value=["example.com"])
    @patch("socialhome.content.previews.fetch_oembed_preview", return_value=None)
    @patch("socialhome.content.previews.fetch_og_preview")
    def test_fetch_og_preview_called(self, fetch_og, fetch_oembed, find_urls):
        fetch_content_preview(self.content)
        fetch_og.assert_called_once_with(self.content, ["example.com"])

    @patch("socialhome.content.previews.find_urls_in_text", autospec=True)
    @patch("socialhome.content.previews.fetch_oembed_preview", autospec=True)
    @patch("socialhome.content.previews.fetch_og_preview", autospec=True)
    def test_no_fetch_if_show_preview_false(self, fetch_og, fetch_oembed, find_urls):
        self.content.show_preview = False
        fetch_content_preview(self.content)
        assert not fetch_og.called
        assert not fetch_oembed.called
        assert not find_urls.called


class TestOEmbedDiscoverer:
    def test_oembed_discoverer_inits(self):
        OEmbedDiscoverer()


class TestFetchOEmbedPreview(SocialhomeTestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.content = ContentFactory()
        cls.urls = ["https://example.com"]

    @patch("socialhome.content.previews.PyEmbed.embed", return_value="")
    def test_adds_dnt_flag_to_twitter_oembed(self, embed):
        fetch_oembed_preview(self.content, ["https://twitter.com/foobar/12345"])
        embed.assert_called_once_with("https://twitter.com/foobar/12345", dnt="true", omit_script="true")

    def test_cache_not_updated_if_previous_found(self):
        OEmbedCacheFactory(url=self.urls[0])
        result = fetch_oembed_preview(self.content, self.urls)
        self.content.refresh_from_db()
        self.assertEqual(self.content.oembed, result)

    @patch("socialhome.content.previews.PyEmbed.embed", return_value="")
    def test_cache_updated_if_previous_found_older_than_7_days(self, embed):
        OEmbedCacheFactory(url=self.urls[0])
        with freeze_time(datetime.date.today() + datetime.timedelta(days=8)):
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
    def test_skips_twitter_profile_stream_oembeds(self, embed):
        fetch_oembed_preview(self.content, ["https://twitter.com/foobar"])
        self.assertFalse(embed.called)
        self.content.refresh_from_db()
        self.assertIsNone(self.content.oembed)

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
