import json
from unittest.mock import patch

import pytest
from channels.tests import ChannelTestCase, Client
from django.test import SimpleTestCase
from freezegun import freeze_time

from socialhome.content.models import Content
from socialhome.content.tests.factories import ContentFactory
from socialhome.streams.consumers import StreamConsumer


@pytest.mark.usefixtures("db")
@freeze_time("2017-03-11")
class TestStreamConsumerReceive(ChannelTestCase):
    @classmethod
    def setUpTestData(cls):
        super(TestStreamConsumerReceive, cls).setUpTestData()
        cls.content = ContentFactory()
        cls.content2 = ContentFactory()

    def setUp(self):
        super(TestStreamConsumerReceive, self).setUp()
        self.client = Client()

    def test_receive_load_content_sends_reply_content(self):
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
        self.assertEqual(text["placement"], "prepended")
        self.assertEqual(text["contents"], [
            {
                "id": self.content.id,
                "guid": self.content.guid,
                "author": self.content.author.id,
                "author_image": self.content.author.safer_image_url_small,
                "author_name": self.content.author.handle,
                "rendered": self.content.rendered,
                "humanized_timestamp": self.content.humanized_timestamp,
                "formatted_timestamp": self.content.formatted_timestamp,
            }
        ])

    def test_receive_load_more_sends_more_content(self):
        self.client.send_and_consume(
            "websocket.receive",
            {
                "path": "/ch/streams/public/",
                "text": '{"action": "load_more", "last_id": %s}' % self.content2.id,
            },
        )
        receive = self.client.receive()
        text = json.loads(receive["text"])
        self.assertEqual(text["event"], "content")
        self.assertEqual(text["placement"], "appended")
        self.assertEqual(text["contents"], [
            {
                "id": self.content.id,
                "guid": self.content.guid,
                "author": self.content.author.id,
                "author_image": self.content.author.safer_image_url_small,
                "author_name": self.content.author.handle,
                "rendered": self.content.rendered,
                "humanized_timestamp": self.content.humanized_timestamp,
                "formatted_timestamp": self.content.formatted_timestamp,
            }
        ])

    @patch("socialhome.streams.consumers.Content.objects.public", return_value=Content.objects.none())
    @patch("socialhome.streams.consumers.Content.objects.tags", return_value=Content.objects.none())
    @patch("socialhome.streams.consumers.Content.objects.profile", return_value=Content.objects.none())
    def test_get_stream_qs_per_stream(self, mock_profile, mock_tags, mock_public):
        self.client.send_and_consume(
            "websocket.receive",
            {
                "path": "/ch/streams/public/",
                "text": '{"action": "load_more", "last_id": %s}' % self.content2.id,
            },
        )
        mock_public.assert_called_once_with()
        self.client.send_and_consume(
            "websocket.receive",
            {
                "path": "/ch/streams/tags__foobar/",
                "text": '{"action": "load_more", "last_id": %s}' % self.content2.id,
            },
        )
        self.assertEqual(mock_tags.call_count, 1)
        self.assertEqual(mock_tags.call_args[0][0], "foobar")
        self.client.send_and_consume(
            "websocket.receive",
            {
                "path": "/ch/streams/profile__1234/",
                "text": '{"action": "load_more", "last_id": %s}' % self.content2.id,
            },
        )
        self.assertEqual(mock_profile.call_count, 1)
        self.assertEqual(mock_profile.call_args[0][0], "1234")


class TestStreamConsumerConnectionGroups(SimpleTestCase):
    @patch.object(StreamConsumer, "__init__", return_value=None)
    def test_connection_groups(self, mock_consumer):
        consumer = StreamConsumer()
        self.assertEqual(consumer.connection_groups(stream="foobar"), ["streams_foobar"])
