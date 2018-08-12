from unittest.mock import Mock, patch

from django.conf import settings
from django.test import override_settings

from socialhome.enums import Visibility
from socialhome.tests.utils import SocialhomeTestCase
from socialhome.users.models import Profile
from socialhome.users.tests.factories import ProfileFactory, UserFactory, BaseProfileFactory
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

    def test_handle_can_have_port(self):
        self.profile.handle = "foo@example.com:3000"
        self.profile.save()

    def test_home_url(self):
        self.assertEqual(self.profile.home_url, self.profile.remote_url)
        self.assertEqual(
            self.user.profile.home_url, "%s%s" % (settings.SOCIALHOME_URL, self.user.profile.get_absolute_url()),
        )

    def test_name_or_handle(self):
        self.assertEqual(self.profile.name_or_handle, self.profile.name)
        self.profile.name = ""
        self.assertEqual(self.profile.name_or_handle, self.profile.handle)

    def test_remote_url(self):
        self.assertEqual(
            self.profile.remote_url,
            "https://%s/people/%s" % (self.profile.handle.split("@")[1], self.profile.guid)
        )

    def test_profile_image_urls_default_to_ponies(self):
        profile = ProfileFactory(image_url_small="", image_url_medium="", image_url_large="")
        ponies = get_pony_urls()
        urls = [profile.image_url_large, profile.image_url_medium, profile.image_url_small]
        self.assertEqual(urls, ponies)

    def test___str__(self):
        profile = ProfileFactory(name="foo")
        assert str(profile) == f"foo ({profile.fid})"

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

    def test_is_local(self):
        self.assertTrue(self.user.profile.is_local)
        self.assertFalse(self.profile.is_local)

    def test_from_remote_profile_relative_image_url(self):
        remote_profile = BaseProfileFactory(public=False)
        remote_profile.handle = "foo@example.com"
        remote_profile.image_urls["small"] = "/sm"
        remote_profile.image_urls["medium"] = "/me"
        remote_profile.image_urls["large"] = "/lg"
        profile = Profile.from_remote_profile(remote_profile)
        self.assertEqual(profile.image_url_small, "https://example.com/sm")
        self.assertEqual(profile.image_url_medium, "https://example.com/me")
        self.assertEqual(profile.image_url_large, "https://example.com/lg")

    def test_from_remote_profile_absolute_image_url(self):
        remote_profile = BaseProfileFactory(public=False)
        remote_profile.handle = "foo@example.com"
        remote_profile.image_urls["small"] = "https://example1.com/sm"
        remote_profile.image_urls["medium"] = "https://example2.com/me"
        remote_profile.image_urls["large"] = "https://example3.com/lg"
        profile = Profile.from_remote_profile(remote_profile)
        self.assertEqual(profile.image_url_small, "https://example1.com/sm")
        self.assertEqual(profile.image_url_medium, "https://example2.com/me")
        self.assertEqual(profile.image_url_large, "https://example3.com/lg")

    def test_from_remote_profile(self):
        remote_profile = BaseProfileFactory(public=False)
        profile = Profile.from_remote_profile(remote_profile)
        self.assertEqual(profile.fid, remote_profile.id)
        self.assertEqual(profile.name, remote_profile.name)
        self.assertEqual(profile.visibility, Visibility.LIMITED)
        self.assertEqual(profile.image_url_large, remote_profile.image_urls["large"])
        self.assertEqual(profile.image_url_medium, remote_profile.image_urls["medium"])
        self.assertEqual(profile.image_url_small, remote_profile.image_urls["small"])
        self.assertEqual(profile.location, remote_profile.location)
        self.assertEqual(profile.email, remote_profile.email)
        self.assertEqual(profile.rsa_public_key, remote_profile.public_key)

        # Update to public
        remote_profile_update = BaseProfileFactory(public=True, id=remote_profile.id)
        profile = Profile.from_remote_profile(remote_profile_update)
        self.assertEqual(profile.fid, remote_profile.id)
        self.assertEqual(profile.visibility, Visibility.PUBLIC)

        # Make sure public key doesn't get deleted if it doesn't have a value
        public_key = profile.rsa_public_key
        assert public_key
        remote_profile_update = BaseProfileFactory(public_key="", id=remote_profile.id)
        profile = Profile.from_remote_profile(remote_profile_update)
        self.assertEqual(profile.rsa_public_key, public_key)
        remote_profile_update = BaseProfileFactory(public_key=None, id=remote_profile.id)
        profile = Profile.from_remote_profile(remote_profile_update)
        self.assertEqual(profile.rsa_public_key, public_key)
