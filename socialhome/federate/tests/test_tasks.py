from unittest.mock import patch, Mock

import pytest
from django.conf import settings
from django.test import override_settings
from federation.entities.base import Comment
from federation.tests.fixtures.keys import get_dummy_private_key
from test_plus import TestCase

from socialhome.content.tests.factories import ContentFactory
from socialhome.enums import Visibility
from socialhome.federate.tasks import (
    receive_task, send_content, send_content_retraction, send_reply,
    forward_relayable, _get_remote_followers,
    send_follow)
from socialhome.users.models import Profile
from socialhome.users.tests.factories import UserFactory, ProfileFactory


@pytest.mark.usefixtures("db")
@patch("socialhome.federate.tasks.process_entities")
class TestReceiveTask():
    @patch("socialhome.federate.tasks.handle_receive", return_value=("sender", "diaspora", ["entity"]))
    def test_receive_task_runs(self, mock_handle_receive, mock_process_entities):
        receive_task("foobar")
        mock_process_entities.assert_called_with(["entity"])

    @patch("socialhome.federate.tasks.handle_receive", return_value=("sender", "diaspora", []))
    def test_receive_task_returns_none_on_no_entities(self, mock_handle_receive, mock_process_entities):
        assert receive_task("foobar") is None
        mock_process_entities.assert_not_called()


class TestSendContent(TestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        author = UserFactory()
        cls.limited_content = ContentFactory(visibility=Visibility.LIMITED, author=author.profile)
        cls.public_content = ContentFactory(visibility=Visibility.PUBLIC, author=author.profile)

    @patch("socialhome.federate.tasks.make_federable_entity", return_value=None)
    def test_only_public_content_calls_make_federable_entity(self, mock_maker):
        send_content(self.limited_content.id)
        mock_maker.assert_not_called()
        send_content(self.public_content.id)
        mock_maker.assert_called_once_with(self.public_content)

    @patch("socialhome.federate.tasks.handle_send")
    @patch("socialhome.federate.tasks.make_federable_entity", return_value="entity")
    def test_handle_send_is_called(self, mock_maker, mock_send):
        send_content(self.public_content.id)
        mock_send.assert_called_once_with("entity", self.public_content.author, [('relay.iliketoast.net', 'diaspora')])

    @patch("socialhome.federate.tasks.make_federable_entity", return_value=None)
    @patch("socialhome.federate.tasks.logger.warning")
    def test_warning_is_logged_on_no_entity(self, mock_logger, mock_maker):
        send_content(self.public_content.id)
        self.assertTrue(mock_logger.called)

    @override_settings(DEBUG=True)
    @patch("socialhome.federate.tasks.handle_send")
    def test_content_not_sent_in_debug_mode(self, mock_send):
        send_content(self.public_content.id)
        mock_send.assert_not_called()


class TestSendContentRetraction(TestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        author = UserFactory()
        cls.limited_content = ContentFactory(visibility=Visibility.LIMITED, author=author.profile)
        cls.public_content = ContentFactory(visibility=Visibility.PUBLIC, author=author.profile)

    @patch("socialhome.federate.tasks.make_federable_retraction", return_value=None)
    def test_only_public_content_calls_make_federable_entity(self, mock_maker):
        send_content_retraction(self.limited_content, self.limited_content.author_id)
        mock_maker.assert_not_called()
        send_content_retraction(self.public_content, self.public_content.author_id)
        mock_maker.assert_called_once_with(self.public_content, self.public_content.author)

    @patch("socialhome.federate.tasks.handle_send")
    @patch("socialhome.federate.tasks.make_federable_retraction", return_value="entity")
    def test_handle_create_payload_is_called(self, mock_maker, mock_sender):
        send_content_retraction(self.public_content, self.public_content.author_id)
        mock_sender.assert_called_once_with(
            "entity", self.public_content.author, [('relay.iliketoast.net', 'diaspora')]
        )

    @patch("socialhome.federate.tasks.make_federable_retraction", return_value=None)
    @patch("socialhome.federate.tasks.logger.warning")
    def test_warning_is_logged_on_no_entity(self, mock_logger, mock_maker):
        send_content_retraction(self.public_content, self.public_content.author_id)
        self.assertTrue(mock_logger.called)

    @override_settings(DEBUG=True)
    @patch("socialhome.federate.tasks.handle_send")
    def test_content_not_sent_in_debug_mode(self, mock_send):
        send_content_retraction(self.public_content, self.public_content.author_id)
        mock_send.assert_not_called()


class TestSendReply(TestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        author = UserFactory()
        Profile.objects.filter(id=author.profile.id).update(rsa_private_key=get_dummy_private_key().exportKey())
        cls.public_content = ContentFactory(visibility=Visibility.PUBLIC)
        cls.remote_reply = ContentFactory(parent=cls.public_content, author=ProfileFactory())
        cls.reply = ContentFactory(parent=cls.public_content, author=author.profile)

    @patch("socialhome.federate.tasks.handle_send", return_value=None)
    def test_send_reply(self, mock_sender):
        send_reply(self.reply.id)
        assert mock_sender.called == 1


class TestForwardRelayable(TestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        author = UserFactory()
        author.profile.rsa_private_key = get_dummy_private_key().exportKey()
        author.profile.save()
        cls.public_content = ContentFactory(visibility=Visibility.PUBLIC, author=author.profile)
        cls.remote_reply = ContentFactory(parent=cls.public_content, author=ProfileFactory())
        cls.reply = ContentFactory(parent=cls.public_content)

    @patch("socialhome.federate.tasks.handle_send", return_value=None)
    def test_forward_relayable(self, mock_send):
        entity = Comment(handle=self.reply.author.handle)
        entity.sign_with_parent = Mock()
        forward_relayable(entity, self.public_content.id)
        mock_send.assert_called_once_with(entity, self.public_content.author, [
            (settings.SOCIALHOME_RELAY_DOMAIN, "diaspora"),
            (self.remote_reply.author.handle, None),
        ])


class TestGetRemoveFollowers(TestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.user = UserFactory()
        cls.local_follower_user = UserFactory()
        cls.local_follower_user.profile.following.add(cls.user.profile)
        cls.remote_follower = ProfileFactory()
        cls.remote_follower.following.add(cls.user.profile)
        cls.remote_follower2 = ProfileFactory()
        cls.remote_follower2.following.add(cls.user.profile)

    def test_all_remote_returned(self):
        followers = set(_get_remote_followers(self.user.profile))
        self.assertEqual(
            followers,
            {
                (self.remote_follower.handle, None),
                (self.remote_follower2.handle, None),
            }
        )

    def test_exclude_is_excluded(self):
        followers = set(_get_remote_followers(self.user.profile, exclude=self.remote_follower.handle))
        self.assertEqual(
            followers,
            {
                (self.remote_follower2.handle, None),
            }
        )


class TestSendFollow(TestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.user = UserFactory()
        cls.profile = cls.user.profile
        cls.remote_profile = ProfileFactory()

    @patch("socialhome.federate.tasks.handle_create_payload", return_value="payload")
    @patch("socialhome.federate.tasks.send_document")
    def test_send_follow(self, mock_send, mock_payload):
        send_follow(self.profile.id, self.remote_profile.id)
        mock_send.assert_called_once_with(
            "https://%s/receive/%s" % (self.remote_profile.handle.split("@")[1], self.remote_profile.guid),
            "payload",
        )
