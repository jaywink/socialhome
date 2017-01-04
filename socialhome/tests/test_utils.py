from unittest import TestCase
from unittest.mock import Mock

from socialhome.utils import safe_clear_cached_property


class TestSafeClearCachedProperty(TestCase):
    def setUp(self):
        super(TestSafeClearCachedProperty, self).setUp()
        self.instance = Mock(foo="bar")

    def test_clears_attribute(self):
        safe_clear_cached_property(self.instance, "foo")
        self.assertFalse(hasattr(self.instance, "foo"))

    def test_doesnt_raise_on_unknown_attribute(self):
        safe_clear_cached_property(self.instance, "bar")
