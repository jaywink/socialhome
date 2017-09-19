from unittest import TestCase

from socialhome.templatetags.string_utils import startswith


class TestStartswith(TestCase):
    def test_startswith(self):
        self.assertTrue(startswith("spam", "sp"))
        self.assertFalse(startswith("spam", "am"))
