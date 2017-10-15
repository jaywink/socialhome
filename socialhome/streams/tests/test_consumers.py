import json
from unittest.mock import patch, Mock

from channels.tests import Client
from django.contrib.auth.models import AnonymousUser
from django.test import SimpleTestCase
from freezegun import freeze_time

from socialhome.content.models import Content
from socialhome.content.tests.factories import ContentFactory, TagFactory
from socialhome.streams.consumers import StreamConsumer
from socialhome.streams.streams import PublicStream, FollowedStream, TagStream
from socialhome.tests.utils import SocialhomeChannelTestCase
from socialhome.users.tests.factories import UserFactory


@freeze_time("2017-03-11")
class TestStreamConsumer(SocialhomeChannelTestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.user = UserFactory()
        cls.content = ContentFactory()
        cls.content2 = ContentFactory()
        cls.child_content = ContentFactory(parent=cls.content)
        cls.tag = TagFactory()

    def setUp(self):
        super().setUp()
        self.client = Client()

    @patch.object(StreamConsumer, "__init__", return_value=None)
    @patch("socialhome.streams.consumers.PublicStream.get_queryset", return_value="spam")
    def test__get_base_qs(self, mock_qs, mock_consumer):
        consumer = StreamConsumer()
        consumer.stream_name = "public"
        self.assertEqual(consumer._get_base_qs(), "spam")

    @patch.object(StreamConsumer, "__init__", return_value=None)
    def test__get_stream_class(self, mock_consumer):
        consumer = StreamConsumer()
        consumer.stream_name = "public"
        self.assertEqual(consumer._get_stream_class(), PublicStream)
        consumer.stream_name = "followed"
        self.assertEqual(consumer._get_stream_class(), FollowedStream)
        consumer.stream_name = "tag"
        self.assertEqual(consumer._get_stream_class(), TagStream)

    @patch.object(StreamConsumer, "__init__", return_value=None)
    def test__get_stream_info(self, mock_consumer):
        consumer = StreamConsumer()
        consumer.kwargs = {"stream": "spam"}
        self.assertEqual(consumer._get_stream_info(), ("spam", None))
        consumer.kwargs = {"stream": "spam__eggs"}
        self.assertEqual(consumer._get_stream_info(), ("spam", "eggs"))

    @patch.object(StreamConsumer, "__init__", return_value=None)
    def test__get_stream_instance(self, mock_consumer):
        consumer = StreamConsumer()
        consumer.stream_name = "public"
        instance = consumer._get_stream_instance()
        self.assertTrue(isinstance(instance, PublicStream))
        consumer.stream_name = "followed"
        consumer.message = Mock(user=self.user)
        instance = consumer._get_stream_instance()
        self.assertTrue(isinstance(instance, FollowedStream))
        self.assertTrue(instance.user, self.user)
        consumer.stream_name = "tag"
        consumer.stream_info = str(self.tag.id)
        instance = consumer._get_stream_instance()
        self.assertTrue(isinstance(instance, TagStream))
        self.assertEqual(instance.tag, self.tag)

    @patch.object(StreamConsumer, "__init__", return_value=None)
    @patch("socialhome.streams.consumers.PublicStream.get_content", return_value="spam")
    def test__get_stream_qs(self, mock_qs, mock_consumer):
        consumer = StreamConsumer()
        consumer.stream_name = "public"
        self.assertEqual(consumer._get_stream_qs(), "spam")

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
        self.assertEqual(text["contents"], [self.content.dict_for_view(AnonymousUser())])

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
        self.assertEqual(text["contents"], [self.content.dict_for_view(AnonymousUser())])

    def test_receive_load_children_sends_reply_content(self):
        self.client.send_and_consume(
            "websocket.receive",
            {
                "path": "/ch/streams/public/",
                "text": '{"action": "load_children", "content_id": %s}' % self.content.id,
            },
        )
        receive = self.client.receive()
        text = json.loads(receive["text"])
        self.assertEqual(text["event"], "content")
        self.assertEqual(text["placement"], "children")
        self.assertEqual(text["parent_id"], self.content.id)
        self.assertEqual(text["contents"], [self.child_content.dict_for_view(AnonymousUser())])

    @patch("socialhome.streams.consumers.Content.objects.public", return_value=Content.objects.none())
    @patch("socialhome.streams.consumers.Content.objects.tag", return_value=Content.objects.none())
    @patch("socialhome.streams.consumers.Content.objects.profile", return_value=Content.objects.none())
    @patch("socialhome.streams.consumers.Content.objects.followed", return_value=Content.objects.none())
    def test_get_stream_qs_per_stream(self, mock_followed, mock_profile, mock_tag, mock_public):
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
                "path": "/ch/streams/tag__%s_%s/" % (self.tag.id, self.tag.name),
                "text": '{"action": "load_more", "last_id": %s}' % self.content2.id,
            },
        )
        self.assertEqual(mock_tag.call_count, 1)
        self.assertEqual(mock_tag.call_args[0][0], self.tag)
        self.client.send_and_consume(
            "websocket.receive",
            {
                "path": "/ch/streams/profile_all__%s/" % self.user.profile.id,
                "text": '{"action": "load_more", "last_id": %s}' % self.content2.id,
            },
        )
        self.assertEqual(mock_profile.call_count, 1)
        self.assertEqual(mock_profile.call_args[0][0], self.user.profile)
        self.client.send_and_consume(
            "websocket.receive",
            {
                "path": "/ch/streams/followed__foobar/",
                "text": '{"action": "load_more", "last_id": %s}' % self.content2.id,
            },
        )
        self.assertEqual(mock_followed.call_count, 1)


class TestStreamConsumerConnectionGroups(SimpleTestCase):
    @patch.object(StreamConsumer, "__init__", return_value=None)
    def test_connection_groups(self, mock_consumer):
        consumer = StreamConsumer()
        self.assertEqual(consumer.connection_groups(stream="foobar"), ["streams_foobar"])
