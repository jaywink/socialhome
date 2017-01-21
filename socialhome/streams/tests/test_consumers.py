from unittest.mock import patch

import pytest
from channels.tests import ChannelTestCase, Client
from django.test import SimpleTestCase

from socialhome.content.tests.factories import ContentFactory
from socialhome.streams.consumers import StreamConsumer


@pytest.mark.usefixtures("db")
class TestStreamConsumerReceive(ChannelTestCase):
    @classmethod
    def setUpTestData(cls):
        super(TestStreamConsumerReceive, cls).setUpTestData()
        cls.content = ContentFactory()

    def setUp(self):
        super(TestStreamConsumerReceive, self).setUp()
        self.client = Client()

    def test_receive_sends_reply_content(self):
        self.client.send_and_consume(
            "websocket.receive",
            {
                "path": "/ch/streams/public/",
                "text": '{"action": "load_content", "ids": [%s]}' % self.content.id,
            },
        )
        self.assertEqual(
            self.client.receive(),
            {
                'text': '{"event": "content", "contents": [{"id": %s, "author": %s, "rendered": "%s"}]}' % (
                    self.content.id, self.content.author.id, self.content.rendered
                )
            }
        )


class TestStreamConsumerConnectionGroups(SimpleTestCase):
    @patch.object(StreamConsumer, "__init__", return_value=None)
    def test_connection_groups(self, mock_consumer):
        consumer = StreamConsumer()
        self.assertEqual(consumer.connection_groups(stream="foobar"), ["streams_foobar"])
