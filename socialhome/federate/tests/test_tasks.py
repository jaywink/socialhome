from unittest.mock import patch

from django.test import override_settings
from federation.entities.base import Comment
from federation.tests.fixtures.keys import get_dummy_private_key
from test_plus import TestCase

from socialhome.content.tests.factories import (
    ContentFactory, LocalContentFactory, PublicContentFactory, LimitedContentFactory)
from socialhome.enums import Visibility
from socialhome.federate.tasks import (
    receive_task, send_content, send_content_retraction, send_reply, forward_entity, _get_remote_followers,
    send_follow_change, send_profile, send_share, send_profile_retraction, _get_limited_recipients)
from socialhome.tests.utils import SocialhomeTestCase
from socialhome.users.models import Profile
from socialhome.users.tests.factories import (
    UserFactory, ProfileFactory, PublicUserFactory, PublicProfileFactory, UserWithKeyFactory, LimitedUserFactory)


@patch("socialhome.federate.tasks.process_entities", autospec=True)
class TestReceiveTask(SocialhomeTestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.user = UserFactory()

    @patch("socialhome.federate.tasks.handle_receive", return_value=("sender", "diaspora", ["entity"]), autospec=True)
    def test_receive_task_runs(self, mock_handle_receive, mock_process_entities):
        receive_task("foobar")
        mock_process_entities.assert_called_with(["entity"], receiving_profile=None)

    @patch("socialhome.federate.tasks.handle_receive", return_value=("sender", "diaspora", []), autospec=True)
    def test_receive_task_returns_none_on_no_entities(self, mock_handle_receive, mock_process_entities):
        self.assertIsNone(receive_task("foobar"))
        self.assertTrue(mock_process_entities.called is False)

    @patch("socialhome.federate.tasks.handle_receive", return_value=("sender", "diaspora", ["entity"]), autospec=True)
    def test_receive_task_with_uuid(self, mock_handle_receive, mock_process_entities):
        receive_task("foobar", uuid=self.user.profile.uuid)
        mock_process_entities.assert_called_with(["entity"], receiving_profile=self.user.profile)


class TestSendContent(SocialhomeTestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.user = UserFactory()
        cls.profile = cls.user.profile
        cls.remote_profile = ProfileFactory(with_key=True)
        cls.create_content_set(author=cls.profile)

    @patch("socialhome.federate.tasks.make_federable_content", return_value=None, autospec=True)
    def test_only_limited_and_public_content_calls_make_federable_content(self, mock_maker):
        send_content(self.self_content.id)
        self.assertTrue(mock_maker.called is False)
        send_content(self.site_content.id)
        self.assertTrue(mock_maker.called is False)
        send_content(self.limited_content.id)
        mock_maker.assert_called_once_with(self.limited_content)
        mock_maker.reset_mock()
        send_content(self.public_content.id)
        mock_maker.assert_called_once_with(self.public_content)

    @patch("socialhome.federate.tasks.handle_send")
    @patch("socialhome.federate.tasks.make_federable_content", return_value="entity")
    def test_handle_send_is_called(self, mock_maker, mock_send):
        send_content(self.public_content.id)
        mock_send.assert_called_once_with(
            "entity",
            self.public_content.author,
            ["diaspora://relay@relay.iliketoast.net/profile/"],
        )

    @patch("socialhome.federate.tasks.handle_send")
    @patch("socialhome.federate.tasks.make_federable_content", return_value="entity")
    def test_handle_send_is_called__limited_content(self, mock_maker, mock_send):
        send_content(self.limited_content.id, recipient_id=self.remote_profile.id)
        mock_send.assert_called_once_with(
            "entity",
            self.limited_content.author,
            [(
                self.remote_profile.fid,
                self.remote_profile.key,
            )],
        )

    @patch("socialhome.federate.tasks.make_federable_content", return_value=None)
    @patch("socialhome.federate.tasks.logger.warning")
    def test_warning_is_logged_on_no_entity(self, mock_logger, mock_maker):
        send_content(self.public_content.id)
        self.assertTrue(mock_logger.called)

    @override_settings(DEBUG=True)
    @patch("socialhome.federate.tasks.handle_send")
    def test_content_not_sent_in_debug_mode(self, mock_send):
        send_content(self.public_content.id)
        self.assertTrue(mock_send.called is False)


class TestSendContentRetraction(SocialhomeTestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        author = UserFactory()
        cls.create_content_set(author=author.profile)
        cls.user = UserWithKeyFactory()
        cls.profile = cls.user.profile
        cls.limited_content2 = LimitedContentFactory(author=cls.profile)

    @patch("socialhome.federate.tasks.handle_send")
    @patch("socialhome.federate.tasks._get_limited_recipients")
    @patch("socialhome.federate.tasks.make_federable_retraction", return_value="entity")
    def test_limited_retraction_calls_get_recipients(self, mock_maker, mock_get, mock_send):
        send_content_retraction(self.limited_content2, self.limited_content2.author.id)
        self.assertTrue(mock_send.called is True)
        self.assertTrue(mock_get.called is True)

    @patch("socialhome.federate.tasks.make_federable_retraction", return_value=None, autospec=True)
    def test_only_limited_and_public_content_calls_make_federable_retraction(self, mock_maker):
        send_content_retraction(self.self_content, self.self_content.author_id)
        self.assertTrue(mock_maker.called is False)
        send_content_retraction(self.site_content, self.site_content.author_id)
        self.assertTrue(mock_maker.called is False)
        send_content_retraction(self.limited_content, self.limited_content.author_id)
        mock_maker.assert_called_once_with(self.limited_content, self.limited_content.author)
        mock_maker.reset_mock()
        send_content_retraction(self.public_content, self.public_content.author_id)
        mock_maker.assert_called_once_with(self.public_content, self.public_content.author)

    @patch("socialhome.federate.tasks.handle_send")
    @patch("socialhome.federate.tasks.make_federable_retraction", return_value="entity")
    def test_handle_create_payload_is_called(self, mock_maker, mock_sender):
        send_content_retraction(self.public_content, self.public_content.author_id)
        mock_sender.assert_called_once_with(
            "entity", self.public_content.author, ["diaspora://relay@relay.iliketoast.net/profile/"]
        )

    @patch("socialhome.federate.tasks.make_federable_retraction", return_value=None)
    @patch("socialhome.federate.tasks.logger.warning")
    def test_warning_is_logged_on_no_entity(self, mock_logger, mock_maker):
        send_content_retraction(self.public_content, self.public_content.author_id)
        self.assertTrue(mock_logger.called is True)

    @override_settings(DEBUG=True)
    @patch("socialhome.federate.tasks.handle_send")
    def test_content_not_sent_in_debug_mode(self, mock_send):
        send_content_retraction(self.public_content, self.public_content.author_id)
        self.assertTrue(mock_send.called is False)


@patch("socialhome.federate.tasks.handle_send")
@patch("socialhome.federate.tasks.make_federable_retraction", return_value="entity")
class TestSendProfileRetraction(SocialhomeTestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.public_user = PublicUserFactory()
        cls.public_profile = cls.public_user.profile
        cls.remote_profile = PublicProfileFactory()
        cls.user = UserFactory()
        cls.profile = cls.user.profile
        cls.limited_user = LimitedUserFactory()
        cls.limited_profile = cls.limited_user.profile
        cls.public_profile.followers.add(cls.remote_profile)
        cls.limited_profile.followers.add(cls.remote_profile)

    @patch("socialhome.federate.tasks._get_remote_followers", autospec=True)
    def test_get_remote_followers_is_called(self, mock_followers, mock_make, mock_send):
        send_profile_retraction(self.public_profile)
        mock_followers.assert_called_once_with(self.public_profile)

    def test_handle_send_is_called(self, mock_make, mock_send):
        send_profile_retraction(self.public_profile)
        mock_send.assert_called_once_with(
            "entity",
            self.public_profile,
            [
                'diaspora://relay@relay.iliketoast.net/profile/',
                self.remote_profile.fid,
            ],
        )

    def test_limited_profile_retraction_not_sent_to_relay(self, mock_make, mock_send):
        send_profile_retraction(self.limited_profile)
        mock_send.assert_called_once_with(
            "entity",
            self.limited_profile,
            [
                self.remote_profile.fid,
            ],
        )

    def test_non_local_profile_does_not_get_sent(self, mock_make, mock_send):
        send_profile_retraction(self.remote_profile)
        self.assertTrue(mock_send.called is False)

    def test_non_public_or_limited_profile_does_not_get_sent(self, mock_make, mock_send):
        send_profile_retraction(self.profile)
        self.assertTrue(mock_send.called is False)


class TestSendReply(SocialhomeTestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        author = UserFactory()
        Profile.objects.filter(id=author.profile.id).update(
            rsa_private_key=get_dummy_private_key().exportKey().decode("utf-8")
        )
        cls.public_content = ContentFactory(author=author.profile, visibility=Visibility.PUBLIC)
        cls.remote_content = ContentFactory(visibility=Visibility.PUBLIC)
        cls.remote_profile = ProfileFactory(with_key=True)
        cls.remote_reply = ContentFactory(parent=cls.public_content, author=cls.remote_profile)
        cls.reply = ContentFactory(parent=cls.public_content, author=author.profile)
        cls.reply2 = ContentFactory(parent=cls.remote_content, author=author.profile)
        cls.limited_content = LimitedContentFactory(author=cls.remote_profile)
        cls.limited_reply = LimitedContentFactory(author=author.profile, parent=cls.limited_content)

    @patch("socialhome.federate.tasks.handle_send")
    @patch("socialhome.federate.tasks.forward_entity")
    @patch("socialhome.federate.tasks.make_federable_content", return_value="entity")
    def test_send_reply__limited_content(self, mock_make, mock_forward, mock_sender):
        send_reply(self.limited_reply.id)
        mock_sender.assert_called_once_with(
            "entity",
            self.limited_reply.author,
            [(
                self.remote_profile.fid,
                self.remote_profile.key,
            )],
        )

    @patch("socialhome.federate.tasks.handle_send")
    @patch("socialhome.federate.tasks.forward_entity")
    @patch("socialhome.federate.tasks.make_federable_content", return_value="entity")
    def test_send_reply_relaying_via_local_author(self, mock_make, mock_forward, mock_sender):
        send_reply(self.reply.id)
        mock_forward.assert_called_once_with("entity", self.public_content.id)
        self.assertTrue(mock_sender.called is False)

    @patch("socialhome.federate.tasks.handle_send")
    @patch("socialhome.federate.tasks.forward_entity")
    @patch("socialhome.federate.tasks.make_federable_content", return_value="entity")
    def test_send_reply_to_remote_author(self, mock_make, mock_forward, mock_sender):
        send_reply(self.reply2.id)
        mock_sender.assert_called_once_with("entity", self.reply2.author, [
            self.remote_content.author.fid,
        ])
        self.assertTrue(mock_forward.called is False)


class TestSendShare(SocialhomeTestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.create_local_and_remote_user()
        Profile.objects.filter(id=cls.profile.id).update(
            rsa_private_key=get_dummy_private_key().exportKey().decode("utf-8")
        )
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
        self.assertTrue(mock_maker.called is False)
        send_share(self.share.id)
        mock_maker.assert_called_once_with(self.share)

    @patch("socialhome.federate.tasks.handle_send")
    @patch("socialhome.federate.tasks.make_federable_content", return_value="entity")
    def test_handle_send_is_called(self, mock_maker, mock_send):
        send_share(self.share.id)
        mock_send.assert_called_once_with(
            "entity",
            self.share.author,
            [self.content.author.fid],
        )

    @patch("socialhome.federate.tasks.make_federable_content", return_value=None)
    @patch("socialhome.federate.tasks.logger.warning")
    def test_warning_is_logged_on_no_entity(self, mock_logger, mock_maker):
        send_share(self.share.id)
        self.assertTrue(mock_logger.called)

    @override_settings(DEBUG=True)
    @patch("socialhome.federate.tasks.handle_send")
    def test_content_not_sent_in_debug_mode(self, mock_send):
        send_share(self.share.id)
        self.assertTrue(mock_send.called is False)

    @patch("socialhome.federate.tasks.handle_send")
    @patch("socialhome.federate.tasks.make_federable_content", return_value="entity")
    def test_doesnt_send_to_local_share_author(self, mock_maker, mock_send):
        send_share(self.local_share.id)
        mock_send.assert_called_once_with("entity", self.local_share.author, [])


class TestForwardEntity(TestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        author = UserFactory()
        author.profile.rsa_private_key = get_dummy_private_key().exportKey()
        author.profile.save()
        cls.public_content = PublicContentFactory(author=author.profile)
        cls.remote_reply = PublicContentFactory(parent=cls.public_content, author=ProfileFactory())
        cls.reply = PublicContentFactory(parent=cls.public_content)
        cls.share = PublicContentFactory(share_of=cls.public_content)
        cls.share_reply = PublicContentFactory(parent=cls.share)
        cls.limited_content = LimitedContentFactory(author=author.profile)
        cls.limited_reply = LimitedContentFactory(parent=cls.limited_content)
        cls.remote_limited_reply = LimitedContentFactory(parent=cls.limited_content)
        cls.limited_content.limited_visibilities.set((cls.limited_reply.author, cls.remote_limited_reply.author))

    @patch("socialhome.federate.tasks.handle_send", return_value=None)
    def test_forward_entity(self, mock_send):
        entity = Comment(actor_id=self.reply.author.fid, id=self.reply.fid)
        forward_entity(entity, self.public_content.id)
        mock_send.assert_called_once_with(entity, self.reply.author, [
            self.remote_reply.author.fid,
            self.share.author.fid,
            self.share_reply.author.fid,
        ], parent_user=self.public_content.author)

    @patch("socialhome.federate.tasks.handle_send", return_value=None)
    def test_forward_entity__limited_content(self, mock_send):
        entity = Comment(actor_id=self.limited_reply.author.fid, id=self.limited_reply.fid)
        forward_entity(entity, self.limited_content.id)
        mock_send.assert_called_once_with(entity, self.limited_reply.author, [(
            self.remote_limited_reply.author.fid,
            self.remote_limited_reply.author.key,
        )], parent_user=self.limited_content.author)


class TestGetRemoteFollowers(TestCase):
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
                self.remote_follower.fid,
                self.remote_follower2.fid,
            }
        )

    def test_exclude_is_excluded(self):
        followers = set(_get_remote_followers(self.user.profile, exclude=self.remote_follower.fid))
        self.assertEqual(
            followers,
            {
                self.remote_follower2.fid,
            }
        )


class TestGetLimitedRecipients(SocialhomeTestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.profile = ProfileFactory()
        cls.limited_content = LimitedContentFactory(author=cls.profile)
        cls.profile2 = ProfileFactory(with_key=True)
        cls.profile3 = ProfileFactory(with_key=True)
        cls.limited_content.limited_visibilities.set((cls.profile2, cls.profile3))

    def test_correct_recipients_returned(self):
        recipients = _get_limited_recipients(self.profile.fid, self.limited_content)
        recipients = {id for id, key in recipients}
        self.assertEqual(
            recipients,
            {
                self.profile2.fid,
                self.profile3.fid,
            },
        )


class TestSendFollow(TestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.user = UserFactory()
        cls.profile = cls.user.profile
        cls.remote_profile = ProfileFactory(
            rsa_public_key=get_dummy_private_key().publickey().exportKey(),
        )

    @patch("socialhome.federate.tasks.handle_send")
    @patch("socialhome.federate.tasks.send_profile")
    @patch("socialhome.federate.tasks.base.Follow", return_value="entity")
    def test_send_follow_change(self, mock_follow, mock_profile, mock_send):
        send_follow_change(self.profile.id, self.remote_profile.id, True)
        mock_send.assert_called_once_with(
            "entity",
            self.profile,
            [(self.remote_profile.fid, self.remote_profile.key)],
        )
        mock_profile.assert_called_once_with(self.profile.id, recipients=[
            self.remote_profile.fid,
        ])


class TestSendProfile(SocialhomeTestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.user = UserFactory()
        cls.profile = cls.user.profile
        cls.remote_profile = ProfileFactory()
        cls.remote_profile2 = ProfileFactory()

    @patch("socialhome.federate.tasks.handle_send")
    @patch("socialhome.federate.tasks._get_remote_followers")
    @patch("socialhome.federate.tasks.make_federable_profile", return_value="profile")
    def test_send_local_profile(self, mock_federable, mock_get, mock_send):
        recipients = [
            self.remote_profile.fid,
            self.remote_profile2.fid,
        ]
        mock_get.return_value = recipients
        send_profile(self.profile.id)
        mock_send.assert_called_once_with(
            "profile", self.profile, recipients,
        )

    @patch("socialhome.federate.tasks.make_federable_profile")
    def test_skip_remote_profile(self, mock_make):
        send_profile(self.remote_profile.id)
        self.assertFalse(mock_make.called)

    @patch("socialhome.federate.tasks.handle_send")
    @patch("socialhome.federate.tasks.make_federable_profile", return_value="profile")
    def test_send_to_given_recipients_only(self, mock_federable, mock_send):
        recipients = [self.remote_profile.fid]
        send_profile(self.profile.id, recipients=recipients)
        mock_send.assert_called_once_with("profile", self.profile, recipients)
