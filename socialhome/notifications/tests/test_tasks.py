from unittest.mock import patch

from django.conf import settings
from django.test import TestCase
from django.urls import reverse

from socialhome.content.tests.factories import ContentFactory
from socialhome.notifications.tasks import send_reply_notification
from socialhome.users.tests.factories import UserFactory


class TestSendReplyNotification(TestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        user = UserFactory()
        cls.content = ContentFactory(author=user.profile)
        cls.content_url = "http://127.0.0.1:8000%s" % reverse(
            "content:view-by-slug", kwargs={"pk": cls.content.id, "slug": cls.content.slug}
        )

    @patch("socialhome.notifications.tasks.send_mail")
    def test_calls_send_email(self, mock_send):
        send_reply_notification(self.content.id)
        mock_send.assert_called_once_with(
            "New reply to your content",
            "There is a new reply to your content, see it here: %s" % self.content_url,
            settings.DEFAULT_FROM_EMAIL,
            [self.content.author.user.email],
            fail_silently=False,
        )
