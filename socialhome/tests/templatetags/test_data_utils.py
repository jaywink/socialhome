from unittest import TestCase

from socialhome.templatetags.data_utils import dict_value


class TestDictValue(TestCase):
    def test_dict_value(self):
        self.assertEqual(dict_value({"spam": "eggs"}, "spam"), "eggs")
        self.assertEqual(dict_value({"spam": "eggs"}, "foobar"), None)
