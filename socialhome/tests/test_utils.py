from unittest.mock import patch

from django.conf import settings
from test_plus import TestCase

from socialhome.tests.utils import SocialhomeTestCase
from socialhome.utils import get_full_media_url, get_redis_connection


class TestGetFullMediaUrl(SocialhomeTestCase):
    def test_url_is_correct(self):
        self.assertEqual(
            get_full_media_url("foobar"),
            "%s%s%s" % (settings.SOCIALHOME_URL, settings.MEDIA_URL, "foobar"),
        )


class TestGetRedisConnection(TestCase):
    @patch("socialhome.utils.redis.StrictRedis")
    @patch("socialhome.utils.redis_connection", new=None)
    def test_get_redis_connection(self, mock_redis):
        get_redis_connection()
        self.assertTrue(mock_redis.called)
