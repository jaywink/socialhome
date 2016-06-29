from test_plus.test import TestCase


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
        self.user.generate_new_rsa_key()
        self.user.save()
        self.assertIsNotNone(self.user.rsa_private_key)
        self.assertIsNotNone(self.user.rsa_public_key)
