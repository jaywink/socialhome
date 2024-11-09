from unittest.mock import patch

from ddt import ddt, data
from django.conf import settings
from django.urls import reverse

from socialhome.content.enums import ContentType
from socialhome.content.tests.factories import ContentFactory
from socialhome.notifications.tasks import (
    send_reply_notifications, send_follow_notification, send_share_notification, send_data_export_ready_notification,
    send_policy_document_update_notification, send_policy_document_update_notifications, send_mention_notification,
    get_root_content_participants)
from socialhome.tests.utils import SocialhomeTestCase
from socialhome.users.tests.factories import UserFactory


class TestGetRootContentParticipants(SocialhomeTestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.create_local_and_remote_user()
        cls.local_content = ContentFactory(author=cls.profile)
        cls.remote_content = ContentFactory(author=cls.remote_profile)
        cls.local_user = UserFactory()
        cls.local_profile = cls.local_user.profile

    def test_no_participants_for_just_root_content(self):
        self.assertEqual(len(get_root_content_participants(self.local_content, exclude_user=self.user)), 0)
        self.assertEqual(len(get_root_content_participants(self.remote_content)), 0)

    def test_no_participants_for_just_remote_replies(self):
        ContentFactory(parent=self.local_content)
        ContentFactory(parent=self.remote_content)
        self.assertEqual(len(get_root_content_participants(self.local_content, exclude_user=self.user)), 0)
        self.assertEqual(len(get_root_content_participants(self.remote_content)), 0)

    def test_no_participants_for_just_remote_shares(self):
        ContentFactory(parent=self.local_content, content_type=ContentType.SHARE)
        ContentFactory(parent=self.remote_content, content_type=ContentType.SHARE)
        self.assertEqual(len(get_root_content_participants(self.local_content, exclude_user=self.user)), 0)
        self.assertEqual(len(get_root_content_participants(self.remote_content)), 0)

    def test_local_participant_for_direct_reply(self):
        ContentFactory(parent=self.local_content, author=self.local_profile)
        ContentFactory(parent=self.remote_content, author=self.local_profile)
        self.assertEqual(len(get_root_content_participants(self.local_content, exclude_user=self.user)), 1)
        self.assertEqual(len(get_root_content_participants(self.remote_content)), 1)

    def test_local_participant_for_direct_share(self):
        ContentFactory(parent=self.local_content, author=self.local_profile, content_type=ContentType.SHARE)
        ContentFactory(parent=self.remote_content, author=self.local_profile, content_type=ContentType.SHARE)
        self.assertEqual(len(get_root_content_participants(self.local_content, exclude_user=self.user)), 1)
        self.assertEqual(len(get_root_content_participants(self.remote_content)), 1)

    def test_local_participant_for_reply_of_remote_reply(self):
        reply = ContentFactory(parent=self.local_content)
        ContentFactory(parent=reply, author=self.local_profile)
        reply = ContentFactory(parent=self.remote_content)
        ContentFactory(parent=reply, author=self.local_profile)
        self.assertEqual(len(get_root_content_participants(self.local_content, exclude_user=self.user)), 1)
        self.assertEqual(len(get_root_content_participants(self.remote_content)), 1)

    def test_local_participant_for_share_of_remote_reply(self):
        reply = ContentFactory(parent=self.local_content)
        ContentFactory(parent=reply, author=self.local_profile, content_type=ContentType.SHARE)
        reply = ContentFactory(parent=self.remote_content)
        ContentFactory(parent=reply, author=self.local_profile, content_type=ContentType.SHARE)
        self.assertEqual(len(get_root_content_participants(self.local_content, exclude_user=self.user)), 1)
        self.assertEqual(len(get_root_content_participants(self.remote_content)), 1)

    def test_local_participants_of_different_types_on_remote(self):
        user2 = UserFactory()
        profile2 = user2.profile
        user3 = UserFactory()
        profile3 = user3.profile
        ContentFactory(parent=self.local_content, author=self.local_profile)
        reply = ContentFactory(parent=self.local_content)
        ContentFactory(parent=reply, author=profile2)
        reply = ContentFactory(parent=self.local_content)
        ContentFactory(parent=reply, author=profile3, content_type=ContentType.SHARE)
        self.assertEqual(len(get_root_content_participants(self.local_content, exclude_user=self.user)), 3)


class TestSendMentionNotification(SocialhomeTestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.create_local_and_remote_user()
        cls.content = ContentFactory(author=cls.profile)

    @patch("socialhome.notifications.tasks.send_mail")
    def test_calls_send_email(self, mock_send):
        send_mention_notification(self.user.id, self.remote_profile.id, self.content.id)
        self.assertEqual(mock_send.call_count, 1)
        args, kwargs = mock_send.call_args_list[0]
        self.assertEqual(args[2], settings.DEFAULT_FROM_EMAIL)
        self.assertEqual(args[3], [self.user.email])
        self.assertFalse(kwargs.get("fail_silently"))


@ddt
class TestSendPolicyDocumentUpdateNotification(SocialhomeTestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.user = UserFactory()

    @data('both', 'privacypolicy', 'tos')
    def test_docs_good_values(self, docs):
        send_policy_document_update_notification(self.user.id, docs)

    def test_docs_bad_value(self):
        with self.assertRaises(ValueError):
            send_policy_document_update_notification(self.user.id, 'foobar')

    @patch("socialhome.notifications.tasks.send_mail")
    def test_send_mail_call(self, mock_send):
        send_policy_document_update_notification(self.user.id, 'both')
        args, kwargs = mock_send.call_args
        self.assertEqual(args[2], settings.DEFAULT_FROM_EMAIL)
        self.assertEqual(args[3][0], self.user.email)
        self.assertEqual(len(args[3]), 1)
        self.assertFalse(kwargs.get("fail_silently"))


class TestSendPolicyDocumentUpdateNotifications(SocialhomeTestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.user = UserFactory(with_verified_email=True)
        cls.user2 = UserFactory(with_verified_email=True)
        cls.user3 = UserFactory()
        cls.verified_users = (cls.user.id, cls.user2.id)

    @patch("socialhome.notifications.tasks.django_rq.enqueue")
    def test_queued_for_users_with_verified_email(self, mock_enqueue):
        send_policy_document_update_notifications('both')
        self.assertEqual(mock_enqueue.call_count, 2)
        for cal in mock_enqueue.call_args_list:
            args, kwargs = cal
            self.assertIn(args[1], self.verified_users)


class TestSendReplyNotification(SocialhomeTestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        user = UserFactory()
        not_related_user = UserFactory()
        replying_user = UserFactory()
        replying_user2 = UserFactory()
        sharing_user = UserFactory()
        replying_user3 = UserFactory()
        cls.content = ContentFactory(author=user.profile)
        cls.not_related_content = ContentFactory(author=not_related_user.profile)
        cls.reply = ContentFactory(author=replying_user.profile, parent=cls.content)
        cls.reply2 = ContentFactory(author=replying_user2.profile, parent=cls.content)
        cls.share = ContentFactory(author=sharing_user.profile, share_of=cls.content)
        cls.reply3 = ContentFactory(author=replying_user3.profile, parent=cls.share)
        cls.content_url = "http://127.0.0.1:8000%s" % reverse(
            "content:view-by-slug", kwargs={"pk": cls.content.id, "slug": cls.content.slug}
        )
        cls.participant_emails = [
            user.email, replying_user.email, sharing_user.email, replying_user3.email,
        ]

    @patch("socialhome.notifications.tasks.send_mail")
    def test_calls_send_email(self, mock_send):
        send_reply_notifications(self.reply2.id)
        self.assertEqual(mock_send.call_count, 4)
        for cal in mock_send.call_args_list:
            args, kwargs = cal
            self.assertEqual(args[2], settings.DEFAULT_FROM_EMAIL)
            self.assertTrue(args[3][0] in self.participant_emails)
            self.assertEqual(len(args[3]), 1)
            self.assertFalse(kwargs.get("fail_silently"))


class TestSendFollowNotification(SocialhomeTestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.create_local_and_remote_user()

    @patch("socialhome.notifications.tasks.send_mail")
    def test_calls_send_email(self, mock_send):
        send_follow_notification(self.profile.id, self.user.profile.id)
        self.assertEqual(mock_send.call_count, 1)
        args, kwargs = mock_send.call_args_list[0]
        self.assertEqual(args[2], settings.DEFAULT_FROM_EMAIL)
        self.assertEqual(args[3], [self.user.email])
        self.assertFalse(kwargs.get("fail_silently"))


class TestSendShareNotification(SocialhomeTestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.create_local_and_remote_user()
        cls.content = ContentFactory(author=cls.profile)
        cls.share = ContentFactory(share_of=cls.content)

    @patch("socialhome.notifications.tasks.send_mail")
    def test_calls_send_email(self, mock_send):
        send_share_notification(self.share.id)
        self.assertEqual(mock_send.call_count, 1)
        args, kwargs = mock_send.call_args_list[0]
        self.assertEqual(args[2], settings.DEFAULT_FROM_EMAIL)
        self.assertEqual(args[3], [self.user.email])
        self.assertFalse(kwargs.get("fail_silently"))


class TestSendDataExportReadyNotification(SocialhomeTestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.user = UserFactory()

    @patch("socialhome.notifications.tasks.send_mail")
    def test_calls_send_email(self, mock_send):
        send_data_export_ready_notification(self.user.id)

        self.assertEqual(mock_send.call_count, 1)
        args, kwargs = mock_send.call_args_list[0]
        self.assertEqual(args[2], settings.DEFAULT_FROM_EMAIL)
        self.assertEqual(args[3], [self.user.email])
        self.assertFalse(kwargs.get("fail_silently"))
