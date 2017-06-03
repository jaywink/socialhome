from unittest.mock import patch, call

import pytest
from django.test import TransactionTestCase

from socialhome.federate.tasks import send_follow_change
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


class TestProfileFollowingChange(TransactionTestCase):
    def setUp(self):
        super().setUp()
        self.user = UserFactory()
        self.user2 = UserFactory()
        self.profile2 = self.user2.profile
        self.profile = ProfileFactory()

    @patch("socialhome.users.signals.django_rq.enqueue")
    def test_adding_follower_sends_a_notification(self, mock_enqueue):
        self.profile2.following.add(self.user.profile)
        mock_enqueue.assert_called_once_with(send_follow_notification, self.profile2.id, self.user.profile.id)

    @patch("socialhome.users.signals.django_rq.enqueue")
    def test_adding_remote_follower_triggers_federation_event(self, mock_enqueue):
        self.profile2.following.add(self.profile)
        self.assertEqual(
            mock_enqueue.call_args_list,
            [
                call(send_follow_notification, self.profile2.id, self.profile.id),
                call(send_follow_change, self.profile2.id, self.profile.id, True),
            ]
        )

    @patch("socialhome.users.signals.django_rq.enqueue")
    def test_removing_remote_follower_triggers_federation_event(self, mock_enqueue):
        self.profile2.following.add(self.profile)
        mock_enqueue.reset_mock()
        self.profile2.following.remove(self.profile)
        self.assertEqual(
            mock_enqueue.call_args_list,
            [
                call(send_follow_change, self.profile2.id, self.profile.id, False),
            ]
        )
