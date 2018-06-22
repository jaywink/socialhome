from django.test import override_settings, RequestFactory

from socialhome.content.tests.factories import ContentFactory
from socialhome.enums import Visibility, PolicyDocumentType
from socialhome.models import PolicyDocument
from socialhome.streams.views import FollowedStreamView, PublicStreamView
from socialhome.tests.utils import SocialhomeTestCase, SocialhomeCBVTestCase
from socialhome.users.models import Profile
from socialhome.users.tests.factories import UserFactory, AdminUserFactory
from socialhome.users.views import ProfileDetailView, ProfileAllContentView
from socialhome.views import MarkdownXImageUploadView


class TestBaseView(SocialhomeTestCase):
    @override_settings(ACCOUNT_ALLOW_REGISTRATION=False)
    def test_signup_link_do_not_show_when_signup_are_closed(self):
        response = self.client.get("/")
        assert "/accounts/signup/" not in str(response.content)

    @override_settings(ACCOUNT_ALLOW_REGISTRATION=True)
    def test_signup_link_shows_when_signup_are_opened(self):
        response = self.client.get("/")
        assert "/accounts/signup/" in str(response.content)


class TestPolicyDocumentView(SocialhomeTestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        if PolicyDocument.objects.count() == 0:
            # Pytest ignores data migrations for some reason..
            # Possibly related? https://github.com/pytest-dev/pytest-django/issues/341
            PolicyDocument.objects.create(
                type=PolicyDocumentType.TERMS_OF_SERVICE,
                content='foo',
                state='draft',
            )
            PolicyDocument.objects.create(
                type=PolicyDocumentType.PRIVACY_POLICY,
                content='foo',
                state='draft',
            )

    def test_privacy_policy_document(self):
        pd = PolicyDocument.objects.get(type=PolicyDocumentType.PRIVACY_POLICY)
        pd.publish()
        pd.save()
        self.get('privacy-policy')
        self.response_200()

    def test_privacy_policy_document__not_published(self):
        self.get('privacy-policy')
        self.response_404()

    def test_tos_document(self):
        pd = PolicyDocument.objects.get(type=PolicyDocumentType.TERMS_OF_SERVICE)
        pd.publish()
        pd.save()
        self.get('terms-of-service')
        self.response_200()

    def test_tos_document__not_published(self):
        self.get('terms-of-service')
        self.response_404()


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
        assert response.templates[0].name == "streams/base.html"

    @override_settings(SOCIALHOME_ROOT_PROFILE="admin")
    def test_home_view_rendered_with_root_profile(self):
        # Set admin profile visibility, otherwise it will just redirect to login
        Profile.objects.filter(user__username="admin").update(visibility=Visibility.PUBLIC)
        response = self.client.get("/")
        assert response.templates[0].name == "streams/base.html"
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


class TestCustomHomeViewLandingPage(SocialhomeTestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.user = UserFactory()
        ContentFactory(pinned=True, author=cls.user.profile)

    @override_settings(SOCIALHOME_HOME_VIEW="socialhome.streams.views.PublicStreamView")
    def test_renders_custom_view(self):
        with self.login(self.user):
            self.get("home")
        self.assertEqual(self.context["view"].__class__, PublicStreamView)


class TestMarkdownXImageUploadViewMethods(SocialhomeCBVTestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.user = UserFactory()

    def test_form_kwargs_has_user(self):
        request = RequestFactory().get("/")
        request.user = self.user
        view = self.get_instance(MarkdownXImageUploadView, request=request)
        kwargs = view.get_form_kwargs()
        self.assertEqual(kwargs.get("user"), self.user)


class TestMarkdownXImageUploadView(SocialhomeTestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.user = UserFactory()

    def test_login_required(self):
        self.post("markdownx_upload")
        self.response_403()
        with self.login(self.user):
            # Well umm, markdownx upload seems to crash on invalid image payload ¯\_(ツ)_/¯
            # We really just want to test that a logged in user goes past the "login required" check
            with self.assertRaises(AttributeError):
                self.post("markdownx_upload")
