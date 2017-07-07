from django.test import override_settings

from socialhome.content.tests.factories import ContentFactory
from socialhome.enums import Visibility
from socialhome.streams.views import FollowedStreamView, PublicStreamView
from socialhome.tests.utils import SocialhomeTestCase
from socialhome.users.models import Profile
from socialhome.users.tests.factories import UserFactory, AdminUserFactory
from socialhome.users.views import ProfileDetailView, ProfileAllContentView


class TestBaseView(SocialhomeTestCase):
    @override_settings(ACCOUNT_ALLOW_REGISTRATION=False)
    def test_signup_link_do_not_show_when_signup_are_closed(self):
        response = self.client.get("/")
        assert "/accounts/signup/" not in str(response.content)

    @override_settings(ACCOUNT_ALLOW_REGISTRATION=True)
    def test_signup_link_shows_when_signup_are_opened(self):
        response = self.client.get("/")
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
    def test_logged_in_followed_stream_view_rendered_without_root_profile(self):
        with self.login(username=self.user.username):
            response = self.client.get("/")
        assert response.templates[0].name == "streams/followed.html"

    @override_settings(SOCIALHOME_ROOT_PROFILE="admin")
    def test_home_view_rendered_with_root_profile(self):
        # Set admin profile visibility, otherwise it will just redirect to login
        Profile.objects.filter(user__username="admin").update(visibility=Visibility.PUBLIC)
        response = self.client.get("/")
        assert response.templates[0].name == "streams/profile.html"
        assert response.context["profile"].user.username == "admin"


class TestHomeViewLandingPagePreference(SocialhomeTestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.user = UserFactory()
        ContentFactory(pinned=True, author=cls.user.profile)  # To ensure profile view can render

    def test_renders_profile(self):
        self.user.preferences["generic__landing_page"] = "profile"
        with self.login(self.user):
            self.get("home")
        self.assertEqual(self.context["view"].__class__, ProfileDetailView)

    def test_renders_profile_all(self):
        self.user.preferences["generic__landing_page"] = "profile_all"
        with self.login(self.user):
            self.get("home")
        self.assertEqual(self.context["view"].__class__, ProfileAllContentView)

    def test_renders_followed_stream(self):
        self.user.preferences["generic__landing_page"] = "followed"
        with self.login(self.user):
            self.get("home")
        self.assertEqual(self.context["view"].__class__, FollowedStreamView)

    def test_renders_public_stream(self):
        self.user.preferences["generic__landing_page"] = "public"
        with self.login(self.user):
            self.get("home")
        self.assertEqual(self.context["view"].__class__, PublicStreamView)

    def test_renders_profile_as_fallback(self):
        self.user.preferences["generic__landing_page"] = "foobar"
        with self.login(self.user):
            self.get("home")
        self.assertEqual(self.context["view"].__class__, ProfileDetailView)
