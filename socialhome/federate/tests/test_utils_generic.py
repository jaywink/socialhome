from unittest.mock import patch

from socialhome.federate.tasks import receive_task
from socialhome.federate.utils import queue_payload
from socialhome.tests.utils import SocialhomeTestCase


class TestQueuePayload(SocialhomeTestCase):
    def setUp(self):
        super().setUp()
        self.request = self.get_request(None)

    @patch("socialhome.federate.utils.generic.django_rq.enqueue", autospec=True)
    def test_calls_enqueue(self, mock_enqueue):
        queue_payload(self.request)
        mock_enqueue.assert_called_once_with(receive_task, self.request.body, uuid=None)

    @patch("socialhome.federate.utils.generic.django_rq.enqueue", autospec=True)
    def test_calls_enqueue__with_uuid(self, mock_enqueue):
        queue_payload(self.request, uuid='1234')
        mock_enqueue.assert_called_once_with(receive_task, self.request.body, uuid='1234')
