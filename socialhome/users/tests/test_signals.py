from unittest.mock import patch, call

from django.conf import settings
from django.test import TransactionTestCase, override_settings

from socialhome.federate.tasks import send_follow_change
from socialhome.tests.utils import SocialhomeTestCase
from socialhome.users.models import User
from socialhome.users.tests.factories import UserFactory, ProfileFactory


class TestUserPostSave(SocialhomeTestCase):
    @override_settings(SOCIALHOME_GENERATE_USER_RSA_KEYS_ON_SAVE=True)
    @patch.object(User, "init_pictures_on_disk")
    def test_user_post_save_creates_a_profile(self, mock_init):
        user = UserFactory()
        profile = user.profile
        assert profile.user == user
        assert profile.name == user.name
        assert profile.email == user.email
        assert profile.rsa_private_key
        assert profile.rsa_public_key
        assert profile.handle == "%s@%s" % (user.username, settings.SOCIALHOME_DOMAIN)
        assert profile.guid
        self.assertEqual(mock_init.call_count, 2)

    @patch.object(User, "init_pictures_on_disk")
    def test_user_post_save_existing_user_calls_copy_picture_to_profile(self, mock_init):
        user = UserFactory()
        mock_init.reset_mock()
        with patch.object(user, "copy_picture_to_profile") as mock_copy:
            user.save()
            mock_copy.assert_called_once_with()
            mock_init.assert_called_once_with()


class TestProfileFollowingChange(TransactionTestCase):
    def setUp(self):
        super().setUp()
        self.user = UserFactory()
        self.user2 = UserFactory()
        self.profile2 = self.user2.profile
        self.profile = ProfileFactory()

    @patch("socialhome.users.signals.django_rq.enqueue")
    def test_adding_remote_follower_triggers_federation_event(self, mock_enqueue):
        self.profile2.following.add(self.profile)
        self.assertEqual(
            mock_enqueue.call_args_list,
            [
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
