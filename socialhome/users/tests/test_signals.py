from unittest.mock import patch

import pytest
from django.test import TransactionTestCase

from socialhome.notifications.tasks import send_follow_notification
from socialhome.users.tests.factories import UserFactory, ProfileFactory


@pytest.mark.django_db
class TestProfile:
    def test_signal_creates_a_profile(self, settings):
        settings.SOCIALHOME_GENERATE_USER_RSA_KEYS_ON_SAVE = True
        user = UserFactory()
        profile = user.profile
        assert profile.user == user
        assert profile.name == user.name
        assert profile.email == user.email
        assert profile.rsa_private_key
        assert profile.rsa_public_key
        assert profile.handle == "%s@%s" %(user.username, settings.SOCIALHOME_DOMAIN)
        assert profile.guid


class TestUserFollowersChange(TransactionTestCase):
    def setUp(self):
        super().setUp()
        self.user = UserFactory()
        self.profile = ProfileFactory()

    @patch("socialhome.users.signals.django_rq.enqueue")
    def test_adding_follower_sends_a_notification(self, mock_enqueue):
        self.user.followers.add(self.profile)
        mock_enqueue.assert_called_once_with(send_follow_notification, self.profile.id, self.user.id)
