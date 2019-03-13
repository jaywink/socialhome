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
        args, kwargs = mock_enqueue.call_args
        self.assertEqual(args[0], receive_task)
        request = args[1]
        self.assertEqual(request.body, self.request.body)
        self.assertEqual(request.headers['Server-name'], 'testserver')
        self.assertEqual(request.method, 'GET')
        self.assertEqual(request.url, self.request.build_absolute_uri())
        self.assertIsNone(kwargs['uuid'])

    @patch("socialhome.federate.utils.generic.django_rq.enqueue", autospec=True)
    def test_calls_enqueue__with_uuid(self, mock_enqueue):
        queue_payload(self.request, uuid='1234')
        _args, kwargs = mock_enqueue.call_args
        self.assertEqual(kwargs['uuid'], '1234')
