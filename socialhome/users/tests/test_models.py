import pytest
from test_plus.test import TestCase

from socialhome.users.tests.factories import ProfileFactory, UserFactory
from socialhome.users.utils import get_pony_urls


class TestUser(TestCase):
    def setUp(self):
        self.user = self.make_user()

    def test__str__(self):
        self.assertEqual(
            self.user.__str__(),
            "testuser"  # This is the default username for self.make_user()
        )

    def test_get_absolute_url(self):
        assert self.user.get_absolute_url() == "/u/testuser/"

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


@pytest.mark.usefixtures("db")
class TestProfile():
    def test_generate_new_rsa_key(self):
        profile = ProfileFactory()
        current_rsa_key = profile.rsa_private_key
        current_public_key = profile.rsa_public_key
        profile.generate_new_rsa_key()
        profile.save()
        assert profile.rsa_private_key !=  current_rsa_key
        assert profile.rsa_public_key != current_public_key

    def test_get_absolute_url(self):
        profile = ProfileFactory(guid="1234")
        assert profile.get_absolute_url() == "/p/1234/"

    def test_home_url(self):
        profile = ProfileFactory(guid="1234")
        assert profile.home_url == profile.remote_url
        user = UserFactory()
        assert user.profile.home_url == user.profile.get_absolute_url()

    def test_remote_url(self):
        profile = ProfileFactory(guid="1234")
        assert profile.remote_url == "https://example.com/people/1234"

    def test_get_image_urls_returns_ponies(self):
        profile = ProfileFactory(guid="1234")
        ponies = get_pony_urls()
        urls = profile.get_image_urls()
        assert urls == ponies

    def test_get_image_urls_returns_urls(self):
        profile = ProfileFactory(
            guid="1234", image_url_large="large", image_url_medium="medium", image_url_small="small"
        )
        urls = profile.get_image_urls()
        assert urls == ("large", "medium", "small")

    def test___str__(self):
        profile = ProfileFactory(name="foo", handle="foo@example.com")
        assert str(profile) == "foo (foo@example.com)"

    @pytest.mark.usefixtures("settings")
    def test_private_key(self, settings):
        settings.SOCIALHOME_GENERATE_USER_RSA_KEYS_ON_SAVE = True
        user = UserFactory()
        assert user.profile.private_key

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
