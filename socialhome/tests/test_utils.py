from django.conf import settings

from socialhome.tests.utils import SocialhomeTestCase
from socialhome.utils import get_full_media_url


class TestGetFullMediaUrl(SocialhomeTestCase):
    def test_url_is_correct(self):
        self.assertEqual(
            get_full_media_url("foobar"),
            "%s%s%s" % (settings.SOCIALHOME_URL, settings.MEDIA_URL, "foobar"),
        )
