from unittest.mock import Mock, patch

from django.test import override_settings

from socialhome.tests.utils import SocialhomeTestCase
from socialhome.users.tests.factories import ProfileFactory, UserFactory
from socialhome.users.utils import get_pony_urls


class TestUser(SocialhomeTestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.user = UserFactory()
        cls.profile = cls.user.profile

    def test__str__(self):
        self.assertEqual(self.user.__str__(), self.user.username)

    def test_get_absolute_url(self):
        assert self.user.get_absolute_url() == "/u/%s/" % self.user.username

    def test_get_first_name(self):
        self.user.first_name = "foo"
        assert self.user.get_first_name() == "foo"
        self.user.first_name = ""
        self.user.name = "bar foo"
        assert self.user.get_first_name() == "bar"
        self.user.first_name = ""
        self.user.name = ""
        assert self.user.get_first_name() == ""

    def test_get_last_name(self):
        self.user.last_name = "foo"
        assert self.user.get_last_name() == "foo"
        self.user.last_name = ""
        self.user.name = "foo bar"
        assert self.user.get_last_name() == "bar"
        self.user.name = "foo"
        assert self.user.get_last_name() == ""
        self.user.last_name = ""
        self.user.name = ""
        assert self.user.get_last_name() == ""

    @patch("socialhome.users.models.User.picture")
    def test_copy_picture_to_profile(self, mock_picture):
        class MockCropped(object):
            def __init__(self, name):
                self.name = name

        self.profile.image_url_small = self.profile.image_url_medium = self.profile.image_url_large = "foo"
        self.user.picture = Mock(crop={
            "50x50": MockCropped("small"),
            "100x100": MockCropped("medium"),
            "300x300": MockCropped("large"),
        })
        self.user.copy_picture_to_profile()
        self.profile.refresh_from_db()
        self.assertEqual(self.profile.image_url_small, "http://127.0.0.1:8000/media/small")
        self.assertEqual(self.profile.image_url_medium, "http://127.0.0.1:8000/media/medium")
        self.assertEqual(self.profile.image_url_large, "http://127.0.0.1:8000/media/large")


class TestProfile(SocialhomeTestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.profile = ProfileFactory(guid="1234")
        cls.user = UserFactory()

    def test_generate_new_rsa_key(self):
        profile = ProfileFactory()
        current_rsa_key = profile.rsa_private_key
        current_public_key = profile.rsa_public_key
        profile.generate_new_rsa_key()
        profile.save()
        assert profile.rsa_private_key !=  current_rsa_key
        assert profile.rsa_public_key != current_public_key

    def test_get_absolute_url(self):
        self.assertEqual(self.profile.get_absolute_url(), "/p/1234/")

    def test_home_url(self):
        self.assertEqual(self.profile.home_url, self.profile.remote_url)
        self.assertEqual(self.user.profile.home_url, self.user.profile.get_absolute_url())

    def test_remote_url(self):
        self.assertEqual(self.profile.remote_url, "https://example.com/people/1234")

    def test_profile_image_urls_default_to_ponies(self):
        profile = ProfileFactory(image_url_small="", image_url_medium="", image_url_large="")
        ponies = get_pony_urls()
        urls = [profile.image_url_large, profile.image_url_medium, profile.image_url_small]
        self.assertEqual(urls, ponies)

    def test___str__(self):
        profile = ProfileFactory(name="foo", handle="foo@example.com")
        assert str(profile) == "foo (foo@example.com)"

    @override_settings(SOCIALHOME_GENERATE_USER_RSA_KEYS_ON_SAVE=True)
    def test_key_properties(self):
        user = UserFactory()
        assert user.profile.private_key
        assert user.profile.key

    def test_get_first_name(self):
        user = UserFactory()
        profile = user.profile
        user.first_name = "foo"
        assert profile.get_first_name() == "foo"
        profile.user = None
        profile.name = "bar foo"
        assert profile.get_first_name() == "bar"
        profile.name = ""
        assert profile.get_first_name() == ""

    def test_get_last_name(self):
        user = UserFactory()
        profile = user.profile
        user.last_name = "foo"
        assert profile.get_last_name() == "foo"
        profile.user = None
        profile.name = "foo bar"
        assert profile.get_last_name() == "bar"
        profile.name = "foo"
        assert profile.get_last_name() == ""
        profile.name = ""
        assert profile.get_last_name() == ""

    def test_safer_image_url_small(self):
        profile = ProfileFactory.build(image_url_small="/foobar", handle="foo@localhost")
        assert profile.safer_image_url_small == "https://localhost/foobar"
        profile.image_url_small = "https://example.com/foobar"
        assert profile.safer_image_url_small == "https://example.com/foobar"

    def test_empty_guid(self):
        with self.assertRaises(ValueError):
            ProfileFactory(guid="")

    def test_is_local(self):
        self.assertTrue(self.user.profile.is_local)
        self.assertFalse(self.profile.is_local)
