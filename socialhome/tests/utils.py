import tempfile
from unittest.mock import Mock

from PIL import Image
from django.test import override_settings
from rest_framework.test import APITestCase
from test_plus import TestCase
from test_plus.test import CBVTestCase

import socialhome.tests.environment  # Set some environment tweaks


class SocialhomeTestBase:
    maxDiff = None

    @staticmethod
    @override_settings(MEDIA_ROOT=tempfile.gettempdir())
    def get_temp_image():
        image = Image.new("RGB", (100, 100))
        tmp_file = tempfile.NamedTemporaryFile(suffix=".jpg")
        image.save(tmp_file)
        tmp_file.seek(0)
        return tmp_file


class SocialhomeTestCase(SocialhomeTestBase, TestCase):
    pass


class SocialhomeCBVTestCase(SocialhomeTestBase, CBVTestCase):
    pass


class SocialhomeAPITestCase(SocialhomeTestBase, APITestCase, TestCase):
    pass


# py.test monkeypatches while we still have two kinds of tests
# Remove these once all our tests are either `SocialhomeTestCase` or another test class
def disable_requests(monkeypatch):
    """Mock away request.get and requests.post."""
    monkeypatch.setattr("requests.post", Mock())

    class MockResponse(str):
        status_code = 200
        text = ""

        @staticmethod
        def raise_for_status():
            pass

    monkeypatch.setattr("requests.get", Mock(return_value=MockResponse))


def disable_mailer(monkeypatch):
    """Mock away mail sending."""
    monkeypatch.setattr("django.core.mail.send_mail", Mock())
