from django.test import override_settings
from test_plus.test import TestCase


@override_settings(SOCIALHOME_GENERATE_USER_RSA_KEYS_ON_SAVE=True)
class TestUser(TestCase):
    def setUp(self):
        self.user = self.make_user()

    def test__str__(self):
        self.assertEqual(
            self.user.__str__(),
            "testuser"  # This is the default username for self.make_user()
        )

    def test_get_absolute_url(self):
        self.assertEqual(
            self.user.get_absolute_url(),
            '/u/testuser/'
        )

    def test_generate_new_rsa_key(self):
        current_rsa_key = self.user.rsa_private_key
        current_public_key = self.user.rsa_public_key
        self.user.generate_new_rsa_key()
        self.user.save()
        self.user.refresh_from_db()
        self.assertNotEqual(self.user.rsa_private_key, current_rsa_key)
        self.assertNotEqual(self.user.rsa_public_key, current_public_key)

    def test_local_user_always_has_rsa_key(self):
        # User is local by default
        self.assertIsNotNone(self.user.rsa_private_key)
        self.assertIsNotNone(self.user.rsa_public_key)
