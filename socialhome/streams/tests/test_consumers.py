import json
from unittest.mock import patch

import pytest
from channels.tests import Client
from django.test import SimpleTestCase, TestCase

from socialhome.content.models import Content
from socialhome.content.tests.factories import ContentFactory
from socialhome.streams.consumers import StreamConsumer
from socialhome.users.tests.factories import UserFactory


@pytest.mark.usefixtures("db")
class TestStreamConsumerReceive(TestCase):
    @classmethod
    def setUpTestData(cls):
        super(TestStreamConsumerReceive, cls).setUpTestData()
        cls.content = ContentFactory()
        cls.user = UserFactory()

    def setUp(self):
        super(TestStreamConsumerReceive, self).setUp()
        self.client = Client()

    @patch.object(StreamConsumer, "send")
    def test_receive_sends_reply_content(self, mock_send):
        self.client.send_and_consume(
            "websocket.receive",
            {
                "path": "/ch/streams/public/",
                "text": '{"action": "load_content", "ids": [%s]}' % self.content.id,
            },
        )
        mock_send.assert_called_once_with(
            json.dumps({
                "event": "content",
                "contents": Content.get_rendered_contents_for_user([self.content.id], self.user),
            })
        )


class TestStreamConsumerConnectionGroups(SimpleTestCase):
    @patch.object(StreamConsumer, "__init__", return_value=None)
    def test_connection_groups(self, mock_consumer):
        consumer = StreamConsumer()
        self.assertEqual(consumer.connection_groups(stream="foobar"), ["streams_foobar"])
