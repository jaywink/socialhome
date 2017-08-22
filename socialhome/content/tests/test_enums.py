from test_plus import TestCase

from socialhome.content.enums import ContentType


class TestContentType(TestCase):
    def test_string_value(self):
        self.assertEqual(ContentType.CONTENT.string_value, "content")
        self.assertEqual(ContentType.REPLY.string_value, "reply")
        self.assertEqual(ContentType.SHARE.string_value, "share")
