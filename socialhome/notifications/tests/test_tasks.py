from unittest.mock import patch

from django.conf import settings
from django.urls import reverse

from socialhome.content.tests.factories import ContentFactory
from socialhome.notifications.tasks import send_reply_notifications, send_follow_notification
from socialhome.tests.utils import SocialhomeTestCase
from socialhome.users.tests.factories import UserFactory, ProfileFactory


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

    @patch("socialhome.notifications.tasks.send_mail")
    def test_calls_send_email(self, mock_send):
        send_follow_notification(self.profile.id, self.user.profile.id)
        self.assertEqual(mock_send.call_count, 1)
        args, kwargs = mock_send.call_args_list[0]
        self.assertEqual(args[2], settings.DEFAULT_FROM_EMAIL)
        self.assertEqual(args[3], [self.user.email])
        self.assertFalse(kwargs.get("fail_silently"))
