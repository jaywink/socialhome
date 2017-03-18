import json
from unittest.mock import patch

import pytest
from channels.tests import ChannelTestCase, Client
from django.test import SimpleTestCase
from freezegun import freeze_time

from socialhome.content.tests.factories import ContentFactory
from socialhome.streams.consumers import StreamConsumer


@pytest.mark.usefixtures("db")
@freeze_time("2017-03-11")
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
        receive = self.client.receive()
        text = json.loads(receive["text"])
        self.assertEqual(text["event"], "content")
        self.assertEqual(text["contents"], [
            {
                "id": self.content.id,
                "guid": self.content.guid,
                "author": self.content.author.id,
                "rendered": self.content.rendered,
                "humanized_timestamp": self.content.humanized_timestamp,
                "formatted_timestamp": self.content.formatted_timestamp,
            }
        ])


class TestStreamConsumerConnectionGroups(SimpleTestCase):
    @patch.object(StreamConsumer, "__init__", return_value=None)
    def test_connection_groups(self, mock_consumer):
        consumer = StreamConsumer()
        self.assertEqual(consumer.connection_groups(stream="foobar"), ["streams_foobar"])
