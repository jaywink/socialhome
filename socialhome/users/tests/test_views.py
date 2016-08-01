import pytest
from django.contrib.auth.models import AnonymousUser
from django.core.urlresolvers import reverse
from django.test import RequestFactory
from test_plus.test import TestCase

from socialhome.content.tests.factories import ContentFactory
from socialhome.enums import Visibility
from socialhome.users.models import User, Profile
from socialhome.users.tests.factories import UserFactory
from socialhome.users.views import UserRedirectView, ProfileUpdateView, ProfileDetailView,\
    OrganizeContentProfileDetailView


class BaseUserTestCase(TestCase):
    def setUp(self):
        self.user = self.make_user()
        self.factory = RequestFactory()


class TestUserRedirectView(BaseUserTestCase):
    def test_get_redirect_url(self):
        # Instantiate the view directly. Never do this outside a test!
        view = UserRedirectView()
        # Generate a fake request
        request = self.factory.get('/fake-url')
        # Attach the user to the request
        request.user = self.user
        # Attach the request to the view
        view.request = request
        # Expect: '/users/testuser/', as that is the default username for
        #   self.make_user()
        self.assertEqual(
            view.get_redirect_url(),
            '/u/testuser/'
        )


class TestProfileUpdateView(BaseUserTestCase):
    def setUp(self):
        # call BaseUserTestCase.setUp()
        super(TestProfileUpdateView, self).setUp()
        # Instantiate the view directly. Never do this outside a test!
        self.view = ProfileUpdateView()
        # Generate a fake request
        request = self.factory.get('/fake-url')
        # Attach the user to the request
        request.user = self.user
        # Attach the request to the view
        self.view.request = request

    def test_get_success_url(self):
        # Expect: '/users/testuser/', as that is the default username for
        #   self.make_user()
        self.assertEqual(
            self.view.get_success_url(),
            '/u/testuser/'
        )

    def test_get_object(self):
        # Expect: self.user, as that is the request's user object
        self.assertEqual(
            self.view.get_object(),
            self.user.profile
        )


@pytest.mark.usefixtures("admin_client", "rf")
class TestProfileDetailView(object):
    def _get_request_view_and_content(self, rf, create_content=True):
        request = rf.get("/")
        request.user = UserFactory()
        profile = request.user.profile
        profile.visibility = Visibility.PUBLIC
        profile.save()
        contents = []
        if create_content:
            contents.extend([
                ContentFactory(author=profile, order=3, pinned=True),
                ContentFactory(author=profile, order=2, pinned=True),
                ContentFactory(author=profile, order=1, pinned=True),
            ])
        view = ProfileDetailView(request=request, kwargs={"guid": profile.guid})
        view.object = profile
        view.target_profile = profile
        return request, view, contents, profile

    def test_get_context_data_contains_content_objects(self, admin_client, rf):
        request, view, contents, profile = self._get_request_view_and_content(rf)
        context = view.get_context_data()
        assert context["contents"].count() == 3
        context_objs = {content for content in context["contents"]}
        objs = set(contents)
        assert context_objs == objs

    def test_get_context_data_does_not_contain_content_for_other_users(self, admin_client, rf):
        request, view, contents, profile = self._get_request_view_and_content(rf, create_content=False)
        user = UserFactory()
        ContentFactory(author=user.profile, pinned=True)
        user = UserFactory()
        ContentFactory(author=user.profile, pinned=True)
        context = view.get_context_data()
        assert len(context["contents"]) == 0

    def test_detail_view_renders(self, admin_client, rf):
        request, view, contents, profile = self._get_request_view_and_content(rf)
        response = admin_client.get(profile.get_absolute_url())
        assert response.status_code == 200

    def test_contents_queryset_returns_public_only_for_unauthenticated(self, admin_client, rf):
        request, view, contents, profile = self._get_request_view_and_content(rf, create_content=False)
        ContentFactory(author=profile, visibility=Visibility.SITE, pinned=True)
        ContentFactory(author=profile, visibility=Visibility.SELF, pinned=True)
        ContentFactory(author=profile, visibility=Visibility.LIMITED, pinned=True)
        public = ContentFactory(author=profile, visibility=Visibility.PUBLIC, pinned=True)
        request.user = AnonymousUser()
        qs = view._get_contents_queryset()
        assert qs.count() == 1
        assert qs.first() == public

    def test_contents_queryset_returns_public_or_site_only_for_authenticated(self, admin_client, rf):
        request, view, contents, profile = self._get_request_view_and_content(rf, create_content=False)
        site = ContentFactory(author=profile, visibility=Visibility.SITE, pinned=True)
        ContentFactory(author=profile, visibility=Visibility.SELF, pinned=True)
        ContentFactory(author=profile, visibility=Visibility.LIMITED, pinned=True)
        public = ContentFactory(author=profile, visibility=Visibility.PUBLIC, pinned=True)
        request.user = User.objects.get(username="admin")
        qs = view._get_contents_queryset()
        assert qs.count() == 2
        assert set(qs) == {public, site}

    def test_contents_queryset_returns_all_for_self(self, admin_client, rf):
        request, view, contents, profile = self._get_request_view_and_content(rf, create_content=False)
        site = ContentFactory(author=profile, visibility=Visibility.SITE, pinned=True)
        selff = ContentFactory(author=profile, visibility=Visibility.SELF, pinned=True)
        limited = ContentFactory(author=profile, visibility=Visibility.LIMITED, pinned=True)
        public = ContentFactory(author=profile, visibility=Visibility.PUBLIC, pinned=True)
        qs = view._get_contents_queryset()
        assert qs.count() == 4
        assert set(qs) == {public, site, selff, limited}

    def test_contents_queryset_returns_content_in_correct_order(self, admin_client, rf):
        request, view, contents, profile = self._get_request_view_and_content(rf)
        qs = view._get_contents_queryset()
        assert qs[0].id == contents[2].id
        assert qs[1].id == contents[1].id
        assert qs[2].id == contents[0].id


@pytest.mark.usefixtures("admin_client", "rf")
class TestOrganizeContentUserDetailView(object):
    def _get_request_view_and_content(self, rf, create_content=True):
        request = rf.get("/")
        request.user = UserFactory()
        profile = request.user.profile
        profile.visibility = Visibility.PUBLIC
        profile.save()

        contents = []
        if create_content:
            contents.extend([
                ContentFactory(author=profile, order=3, pinned=True),
                ContentFactory(author=profile, order=2, pinned=True),
                ContentFactory(author=profile, order=1, pinned=True),
            ])
        view = OrganizeContentProfileDetailView(request=request)
        view.object = profile
        view.target_profile = profile
        return request, view, contents, profile

    def test_view_renders(self, admin_client, rf):
        response = admin_client.get(reverse("users:profile-organize"))
        assert response.status_code == 200

    def test_save_sort_order_updates_order(self, admin_client, rf):
        request, view, contents, profile = self._get_request_view_and_content(rf)
        qs = view._get_contents_queryset()
        assert qs[0].id == contents[2].id
        assert qs[1].id == contents[1].id
        assert qs[2].id == contents[0].id
        # Run id's via str() because request.POST gives them like that
        view._save_sort_order([str(contents[0].id), str(contents[1].id), str(contents[2].id)])
        qs = view._get_contents_queryset()
        assert qs[0].id == contents[0].id
        assert qs[1].id == contents[1].id
        assert qs[2].id == contents[2].id

    def test_save_sort_order_skips_non_qs_contents(self, admin_client, rf):
        request, view, contents, profile = self._get_request_view_and_content(rf)
        other_user = UserFactory()
        other_content = ContentFactory(author=other_user.profile, order=100, pinned=True)
        view._save_sort_order([other_content.id])
        other_content.refresh_from_db()
        assert other_content.order == 100

    def test_get_success_url(self, admin_client, rf):
        request, view, contents, profile = self._get_request_view_and_content(rf)
        assert view.get_success_url() == "/"


@pytest.mark.usefixtures("admin_user", "client")
class TestProfileVisibilityForAnonymous(object):
    def test_visible_to_self_profile_requires_login_for_anonymous(self, admin_user, client):
        Profile.objects.filter(user__username=admin_user.username).update(visibility=Visibility.SELF)
        response = client.get("/u/admin/")
        assert response.status_code == 302
        response = client.get("/p/%s/" % admin_user.profile.guid)
        assert response.status_code == 302

    def test_visible_to_limited_profile_requires_login_for_anonymous(self, admin_user, client):
        Profile.objects.filter(user__username=admin_user.username).update(visibility=Visibility.LIMITED)
        response = client.get("/u/admin/")
        assert response.status_code == 302
        response = client.get("/p/%s/" % admin_user.profile.guid)
        assert response.status_code == 302

    def test_visible_to_site_profile_requires_login_for_anonymous(self, admin_user, client):
        Profile.objects.filter(user__username=admin_user.username).update(visibility=Visibility.SITE)
        response = client.get("/u/admin/")
        assert response.status_code == 302
        response = client.get("/p/%s/" % admin_user.profile.guid)
        assert response.status_code == 302

    def test_public_profile_doesnt_require_login(self, admin_user, client):
        Profile.objects.filter(user__username=admin_user.username).update(visibility=Visibility.PUBLIC)
        response = client.get("/u/admin/")
        assert response.status_code == 200
        response = client.get("/p/%s/" % admin_user.profile.guid)
        assert response.status_code == 200


@pytest.mark.usefixtures("admin_client")
class TestProfileVisibilityForLoggedInUsers(object):
    def test_visible_to_self_profile(self, admin_client):
        admin = User.objects.get(username="admin")
        Profile.objects.filter(user__username="admin").update(visibility=Visibility.SELF)
        user = UserFactory(username="foobar")
        Profile.objects.filter(user__username="foobar").update(visibility=Visibility.SELF)
        response = admin_client.get("/u/admin/")
        assert response.status_code == 200
        response = admin_client.get("/u/foobar/")
        assert response.status_code == 302
        response = admin_client.get("/p/%s/" % admin.profile.guid)
        assert response.status_code == 200
        response = admin_client.get("/p/%s/" % user.profile.guid)
        assert response.status_code == 302

    def test_visible_to_limited_profile(self, admin_client):
        admin = User.objects.get(username="admin")
        Profile.objects.filter(user__username="admin").update(visibility=Visibility.LIMITED)
        user = UserFactory(username="foobar")
        Profile.objects.filter(user__username="foobar").update(visibility=Visibility.LIMITED)
        response = admin_client.get("/u/admin/")
        assert response.status_code == 200
        response = admin_client.get("/u/foobar/")
        assert response.status_code == 302
        response = admin_client.get("/p/%s/" % admin.profile.guid)
        assert response.status_code == 200
        response = admin_client.get("/p/%s/" % user.profile.guid)
        assert response.status_code == 302

    def test_visible_to_site_profile(self, admin_client):
        admin = User.objects.get(username="admin")
        Profile.objects.filter(user__username="admin").update(visibility=Visibility.SITE)
        user = UserFactory(username="foobar")
        Profile.objects.filter(user__username="foobar").update(visibility=Visibility.SITE)
        response = admin_client.get("/u/admin/")
        assert response.status_code == 200
        response = admin_client.get("/u/foobar/")
        assert response.status_code == 200
        response = admin_client.get("/p/%s/" % admin.profile.guid)
        assert response.status_code == 200
        response = admin_client.get("/p/%s/" % user.profile.guid)
        assert response.status_code == 200

    def test_visible_to_public_profile(self, admin_client):
        admin = User.objects.get(username="admin")
        Profile.objects.filter(user__username="admin").update(visibility=Visibility.PUBLIC)
        user = UserFactory(username="foobar")
        Profile.objects.filter(user__username="foobar").update(visibility=Visibility.PUBLIC)
        response = admin_client.get("/u/admin/")
        assert response.status_code == 200
        response = admin_client.get("/u/foobar/")
        assert response.status_code == 200
        response = admin_client.get("/p/%s/" % admin.profile.guid)
        assert response.status_code == 200
        response = admin_client.get("/p/%s/" % user.profile.guid)
        assert response.status_code == 200
