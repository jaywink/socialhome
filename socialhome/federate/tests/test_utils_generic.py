from unittest.mock import patch

from socialhome.federate import tasks  # noqa
from socialhome.federate.utils import queue_payload
from socialhome.tests.utils import SocialhomeTestCase


class TestQueuePayload(SocialhomeTestCase):
    def setUp(self):
        super().setUp()
        self.request = self.get_request(None)

    def test_calls_enqueue(self):
        with patch.object(tasks, "receive_task", autospec=True) as mock_enqueue:
            queue_payload(self.request)
        assert len(mock_enqueue.method_calls) == 1
        name, args, kwargs = mock_enqueue.method_calls[0]
        self.assertEqual(name, 'send')
        request = args[0]
        self.assertEqual(request.body, self.request.body)
        self.assertEqual(request.headers['server-name'], 'testserver')
        self.assertEqual(request.headers['Server-name'], 'testserver')
        self.assertEqual(request.method, 'GET')
        self.assertEqual(request.url, self.request.build_absolute_uri())
        self.assertIsNone(kwargs['uuid'])

    def test_calls_enqueue__with_uuid(self):
        with patch.object(tasks, "receive_task", autospec=True) as mock_enqueue:
            queue_payload(self.request, uuid='1234')
        assert len(mock_enqueue.method_calls) == 1
        name, _args, kwargs = mock_enqueue.method_calls[0]
        self.assertEqual(name, 'send')
        self.assertEqual(kwargs['uuid'], '1234')

    def test_calls_enqueue__with_uuid_from_path(self):
        request = self.get_request(None, path="/p/1234/inbox/")
        with patch.object(tasks, "receive_task", autospec=True) as mock_enqueue:
            queue_payload(request)
        assert len(mock_enqueue.method_calls) == 1
        name, _args, kwargs = mock_enqueue.method_calls[0]
        self.assertEqual(name, 'send')
        self.assertEqual(kwargs['uuid'], '1234')
