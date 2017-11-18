from unittest.mock import patch, call

import pytest
from django.conf import settings
from django.test import override_settings
from federation.entities.base import Comment
from federation.tests.fixtures.keys import get_dummy_private_key
from test_plus import TestCase

from socialhome.content.tests.factories import ContentFactory, LocalContentFactory
from socialhome.enums import Visibility
from socialhome.federate.tasks import (
    receive_task, send_content, send_content_retraction, send_reply,
    forward_relayable, _get_remote_followers,
    send_follow_change, send_profile, send_share)
from socialhome.tests.utils import SocialhomeTestCase
from socialhome.users.models import Profile
from socialhome.users.tests.factories import UserFactory, ProfileFactory


@pytest.mark.usefixtures("db")
@patch("socialhome.federate.tasks.process_entities")
class TestReceiveTask:
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

    @patch("socialhome.federate.tasks.make_federable_content", return_value=None)
    def test_only_public_content_calls_make_federable_content(self, mock_maker):
        send_content(self.limited_content.id)
        mock_maker.assert_not_called()
        send_content(self.public_content.id)
        mock_maker.assert_called_once_with(self.public_content)

    @patch("socialhome.federate.tasks.handle_send")
    @patch("socialhome.federate.tasks.make_federable_content", return_value="entity")
    def test_handle_send_is_called(self, mock_maker, mock_send):
        send_content(self.public_content.id)
        mock_send.assert_called_once_with("entity", self.public_content.author, [('relay.iliketoast.net', 'diaspora')])

    @patch("socialhome.federate.tasks.make_federable_content", return_value=None)
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
    def test_only_public_content_calls_make_federable_retraction(self, mock_maker):
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


class TestSendReply(SocialhomeTestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        author = UserFactory()
        Profile.objects.filter(id=author.profile.id).update(rsa_private_key=get_dummy_private_key().exportKey())
        cls.public_content = ContentFactory(author=author.profile, visibility=Visibility.PUBLIC)
        cls.remote_content = ContentFactory(visibility=Visibility.PUBLIC)
        cls.remote_reply = ContentFactory(parent=cls.public_content, author=ProfileFactory())
        cls.reply = ContentFactory(parent=cls.public_content, author=author.profile)
        cls.reply2 = ContentFactory(parent=cls.remote_content, author=author.profile)

    @patch("socialhome.federate.tasks.handle_send")
    @patch("socialhome.federate.tasks.forward_relayable")
    @patch("socialhome.federate.tasks.make_federable_content", return_value="entity")
    def test_send_reply_relaying_via_local_author(self, mock_make, mock_forward, mock_sender):
        send_reply(self.reply.id)
        mock_forward.assert_called_once_with("entity", self.public_content.id)
        assert mock_sender.called == 0

    @patch("socialhome.federate.tasks.handle_send")
    @patch("socialhome.federate.tasks.forward_relayable")
    @patch("socialhome.federate.tasks.make_federable_content", return_value="entity")
    def test_send_reply_to_remote_author(self, mock_make, mock_forward, mock_sender):
        send_reply(self.reply2.id)
        mock_sender.assert_called_once_with("entity", self.reply2.author, [
            (self.remote_content.author.handle, None),
        ])
        assert mock_forward.called == 0


class TestSendShare(SocialhomeTestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.create_local_and_remote_user()
        Profile.objects.filter(id=cls.profile.id).update(rsa_private_key=get_dummy_private_key().exportKey())
        cls.content = ContentFactory(author=cls.remote_profile, visibility=Visibility.PUBLIC)
        cls.limited_content = ContentFactory(author=cls.remote_profile, visibility=Visibility.LIMITED)
        cls.share = ContentFactory(share_of=cls.content, author=cls.profile, visibility=Visibility.PUBLIC)
        cls.limited_share = ContentFactory(
            share_of=cls.limited_content, author=cls.profile, visibility=Visibility.LIMITED
        )
        cls.local_content = LocalContentFactory(visibility=Visibility.PUBLIC)
        cls.local_share = ContentFactory(share_of=cls.local_content, author=cls.profile, visibility=Visibility.PUBLIC)

    @patch("socialhome.federate.tasks.make_federable_content", return_value=None)
    def test_only_public_share_calls_make_federable_content(self, mock_maker):
        send_share(self.limited_share.id)
        mock_maker.assert_not_called()
        send_share(self.share.id)
        mock_maker.assert_called_once_with(self.share)

    @patch("socialhome.federate.tasks.handle_send")
    @patch("socialhome.federate.tasks.make_federable_content", return_value="entity")
    def test_handle_send_is_called(self, mock_maker, mock_send):
        send_share(self.share.id)
        mock_send.assert_called_once_with("entity", self.share.author, [(self.content.author.handle, None)])

    @patch("socialhome.federate.tasks.make_federable_content", return_value=None)
    @patch("socialhome.federate.tasks.logger.warning")
    def test_warning_is_logged_on_no_entity(self, mock_logger, mock_maker):
        send_share(self.share.id)
        self.assertTrue(mock_logger.called)

    @override_settings(DEBUG=True)
    @patch("socialhome.federate.tasks.handle_send")
    def test_content_not_sent_in_debug_mode(self, mock_send):
        send_share(self.share.id)
        mock_send.assert_not_called()

    @patch("socialhome.federate.tasks.handle_send")
    @patch("socialhome.federate.tasks.make_federable_content", return_value="entity")
    def test_doesnt_send_to_local_share_author(self, mock_maker, mock_send):
        send_share(self.local_share.id)
        mock_send.assert_called_once_with("entity", self.local_share.author, [])


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
        entity = Comment(handle=self.reply.author.handle, guid=self.reply.guid)
        forward_relayable(entity, self.public_content.id)
        mock_send.assert_called_once_with(entity, self.reply.author, [
            (self.remote_reply.author.handle, None),
        ], parent_user=self.public_content.author)


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
    @patch("socialhome.federate.tasks.send_profile")
    def test_send_follow_change(self, mock_profile, mock_send, mock_payload):
        send_follow_change(self.profile.id, self.remote_profile.id, True)
        mock_send.assert_called_once_with(
            "https://%s/receive/users/%s" % (self.remote_profile.handle.split("@")[1], self.remote_profile.guid),
            "payload",
        )
        mock_profile.assert_called_once_with(self.profile.id, recipients=[(self.remote_profile.handle, None)])


class TestSendProfile(SocialhomeTestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.user = UserFactory()
        cls.profile = cls.user.profile
        cls.remote_profile = ProfileFactory()
        cls.remote_profile2 = ProfileFactory()

    @patch("socialhome.federate.tasks.handle_create_payload", return_value="payload")
    @patch("socialhome.federate.tasks._get_remote_followers")
    @patch("socialhome.federate.tasks.send_document")
    @patch("socialhome.federate.tasks.make_federable_profile", return_value="profile")
    def test_send_local_profile(self, mock_federable, mock_send, mock_get, mock_payload):
        mock_get.return_value = [(self.remote_profile.handle, None), (self.remote_profile2.handle, None)]
        send_profile(self.profile.id)
        mock_payload_calls = [
            call("profile", self.profile, to_user=self.remote_profile),
            call("profile", self.profile, to_user=self.remote_profile2),
        ]
        self.assertEqual(mock_payload_calls, mock_payload.call_args_list)
        mock_send_calls = [
            call("https://%s/receive/users/%s" % (self.remote_profile.handle.split("@")[1], self.remote_profile.guid),
                 "payload"),
            call("https://%s/receive/users/%s" % (self.remote_profile2.handle.split("@")[1], self.remote_profile2.guid),
                 "payload"),
        ]
        self.assertEqual(mock_send_calls, mock_send.call_args_list)

    @patch("socialhome.federate.tasks.make_federable_profile")
    def test_skip_remote_profile(self, mock_make):
        send_profile(self.remote_profile.id)
        self.assertFalse(mock_make.called)

    @patch("socialhome.federate.tasks.handle_create_payload", return_value="payload")
    @patch("socialhome.federate.tasks.send_document")
    @patch("socialhome.federate.tasks.make_federable_profile", return_value="profile")
    def test_send_to_given_recipients_only(self, mock_federable, mock_send, mock_payload):
        send_profile(self.profile.id, recipients=[(self.remote_profile.handle, None)])
        mock_payload_calls = [
            call("profile", self.profile, to_user=self.remote_profile),
        ]
        self.assertEqual(mock_payload_calls, mock_payload.call_args_list)
        mock_send_calls = [
            call("https://%s/receive/users/%s" % (self.remote_profile.handle.split("@")[1], self.remote_profile.guid),
                 "payload"),
        ]
        self.assertEqual(mock_send_calls, mock_send.call_args_list)
