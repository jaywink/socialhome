from unittest.mock import patch, Mock

from socialhome.signals import delete_upload_from_disk
from socialhome.tests.utils import SocialhomeTestCase


class TestDeleteUploadFromDisk(SocialhomeTestCase):
    @patch("socialhome.signals.os.unlink")
    def test_calls_unlink(self, mock_unlink):
        delete_upload_from_disk(Mock(image=Mock(path="/foo.png")))
        self.assertTrue(mock_unlink.called is True)
