from test_plus import TestCase

from socialhome.content.enums import ContentType


class TestContentType(TestCase):
    def test_string_value(self):
        self.assertEqual(ContentType.CONTENT.string, "content")
        self.assertEqual(ContentType.REPLY.string, "reply")
        self.assertEqual(ContentType.SHARE.string, "share")
