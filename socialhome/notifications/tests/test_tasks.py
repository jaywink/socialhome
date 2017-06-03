from unittest.mock import patch

from django.conf import settings
from django.test import TestCase
from django.urls import reverse

from socialhome.content.tests.factories import ContentFactory
from socialhome.notifications.tasks import send_reply_notifications, send_follow_notification
from socialhome.users.tests.factories import UserFactory, ProfileFactory


class TestSendReplyNotification(TestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        user = UserFactory()
        not_related_user = UserFactory()
        replying_user = UserFactory()
        replying_user2 = UserFactory()
        cls.content = ContentFactory(author=user.profile)
        cls.not_related_content = ContentFactory(author=not_related_user.profile)
        cls.reply = ContentFactory(author=replying_user.profile, parent=cls.content)
        cls.reply2 = ContentFactory(author=replying_user2.profile, parent=cls.content)
        cls.content_url = "http://127.0.0.1:8000%s" % reverse(
            "content:view-by-slug", kwargs={"pk": cls.content.id, "slug": cls.content.slug}
        )
        cls.participant_emails = {user.email, replying_user.email}

    @patch("socialhome.notifications.tasks.send_mail")
    def test_calls_send_email(self, mock_send):
        send_reply_notifications(self.reply2.id)
        mock_send.assert_called_once_with(
            "[Django] New reply to content you have participated in",
            "There is a new reply to content you have participated in, see it here: %s" % self.content_url,
            settings.DEFAULT_FROM_EMAIL,
            self.participant_emails,
            fail_silently=False,
        )


class TestSendFollowNotification(TestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.user = UserFactory()
        cls.profile = ProfileFactory()

    @patch("socialhome.notifications.tasks.send_mail")
    def test_calls_send_email(self, mock_send):
        send_follow_notification(self.profile.id, self.user.profile.id)
        mock_send.assert_called_once_with(
            "[Django] New follower",
            "You have a new follower: %s" % self.profile.handle,
            settings.DEFAULT_FROM_EMAIL,
            [self.user.email],
            fail_silently=False,
        )
