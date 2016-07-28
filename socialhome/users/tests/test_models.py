import pytest
from test_plus.test import TestCase

from socialhome.users.tests.factories import ProfileFactory


class TestUser(TestCase):
    def setUp(self):
        self.user = self.make_user()

    def test__str__(self):
        self.assertEqual(
            self.user.__str__(),
            "testuser"  # This is the default username for self.make_user()
        )


@pytest.mark.usefixtures("db")
class TestProfile(object):
    def test_generate_new_rsa_key(self):
        profile = ProfileFactory()
        current_rsa_key = profile.rsa_private_key
        current_public_key = profile.rsa_public_key
        profile.generate_new_rsa_key()
        profile.save()
        profile.refresh_from_db()
        assert profile.rsa_private_key !=  current_rsa_key
        assert profile.rsa_public_key != current_public_key

    def test_get_absolute_url(self, settings):
        profile = ProfileFactory(nickname="testuser")
        assert profile.get_absolute_url() == "/u/testuser/"
