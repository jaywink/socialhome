from unittest.mock import Mock

from test_plus import TestCase

from socialhome.context_processors import enums
from socialhome.streams.enums import StreamType


class TestEnums(TestCase):
    def test_enums(self):
        self.assertEqual(
            enums(Mock()),
            {
                "ENUMS": {
                    "StreamType": StreamType.to_dict(),
                },
            },
        )
