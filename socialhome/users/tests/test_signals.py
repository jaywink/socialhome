from unittest.mock import patch, call, Mock

from django.conf import settings
from django.test import TransactionTestCase, override_settings

from socialhome.federate.tasks import send_follow_change, send_profile
from socialhome.tests.utils import SocialhomeTestCase
from socialhome.users.models import User
from socialhome.users.signals import delete_user_pictures
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
        assert profile.fid
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


class TestFederateProfile(TransactionTestCase):
    @patch("socialhome.users.signals.django_rq.enqueue", autospec=True)
    def test_non_local_profile_does_not_get_sent(self, mock_send):
        ProfileFactory()
        self.assertTrue(mock_send.called is False)

    @patch("socialhome.content.signals.django_rq.enqueue")
    def test_local_profile_gets_sent(self, mock_send):
        user = UserFactory()
        mock_send.assert_called_once_with(send_profile, user.profile.id)


class TestFederateProfileRetraction(SocialhomeTestCase):
    @patch("socialhome.users.signals.send_profile_retraction")
    def test_non_local_profile_does_not_get_sent(self, mock_send):
        profile = ProfileFactory()
        profile.delete()
        self.assertTrue(mock_send.called is False)

    @patch("socialhome.users.signals.send_profile_retraction")
    def test_local_profile_gets_sent(self, mock_send):
        user = UserFactory()
        user.profile.delete()
        self.assertTrue(mock_send.called is True)


class TestDeleteUserPictures(SocialhomeTestCase):
    def test_user_pictures_are_deleted(self):
        user = Mock(picture=Mock())
        delete_user_pictures(User, user)
        self.assertTrue(user.picture.delete_all_created_images.called is True)
        self.assertTrue(user.picture.delete.called is True)
