import pytest
from django.test import override_settings

from socialhome.enums import Visibility
from socialhome.tests.utils import SocialhomeTestCase
from socialhome.users.models import Profile
from socialhome.users.tests.factories import UserFactory, AdminUserFactory


@pytest.mark.usefixtures("db")
class TestBaseView(object):
    @pytest.mark.usefixtures("client", "settings")
    def test_signup_link_do_not_show_when_signup_are_closed(self, client, settings):
        settings.ACCOUNT_ALLOW_REGISTRATION = False
        response = client.get("/")
        assert "/accounts/signup/" not in str(response.content)

    @pytest.mark.usefixtures("client", "settings")
    def test_signup_link_shows_when_signup_are_opened(self, client, settings):
        settings.ACCOUNT_ALLOW_REGISTRATION = True
        response = client.get("/")
        assert "/accounts/signup/" in str(response.content)


class TestRootProfile(SocialhomeTestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.user = UserFactory()
        cls.admin_user = AdminUserFactory()

    @override_settings(SOCIALHOME_ROOT_PROFILE=None)
    def test_home_view_rendered_without_root_profile(self):
        response = self.client.get("/")
        assert response.templates[0].name == "pages/home.html"

    @override_settings(SOCIALHOME_ROOT_PROFILE=None)
    def test_logged_in_profile_view_rendered_without_root_profile(self):
        with self.login(username=self.user.username):
            response = self.client.get("/")
        assert response.templates[0].name == "streams/profile.html"
        assert response.context["profile"].user.username == self.user.username

    @override_settings(SOCIALHOME_ROOT_PROFILE="admin")
    def test_home_view_rendered_with_root_profile(self):
        # Set admin profile visibility, otherwise it will just redirect to login
        Profile.objects.filter(user__username="admin").update(visibility=Visibility.PUBLIC)
        with self.login(username=self.admin_user.username):
            response = self.client.get("/")
        assert response.templates[0].name == "streams/profile.html"
        assert response.context["profile"].user.username == "admin"
