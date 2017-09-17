from test_plus import TestCase

from socialhome.streams.enums import StreamType


class TestStreamType(TestCase):
    def test_to_dict(self):
        # noinspection PyTypeChecker
        self.assertEqual(
            StreamType.to_dict(),
            {i.name: i.value for i in StreamType},
        )
