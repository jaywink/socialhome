import pytest
from django.contrib.auth.models import AnonymousUser
from django.core.urlresolvers import reverse
from django.test import RequestFactory
from test_plus.test import TestCase

from socialhome.content.tests.factories import ContentFactory
from socialhome.enums import Visibility
from socialhome.users.models import User
from socialhome.users.tests.factories import UserFactory
from socialhome.users.views import UserRedirectView, UserUpdateView, UserDetailView, OrganizeContentUserDetailView


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


class TestUserUpdateView(BaseUserTestCase):
    def setUp(self):
        # call BaseUserTestCase.setUp()
        super(TestUserUpdateView, self).setUp()
        # Instantiate the view directly. Never do this outside a test!
        self.view = UserUpdateView()
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
            self.user
        )


@pytest.mark.usefixtures("admin_client", "rf")
class TestUserDetailView(object):
    def _get_request_view_and_content(self, rf, create_content=True):
        request = rf.get("/")
        request.user = UserFactory(visibility=Visibility.PUBLIC)
        contents = []
        if create_content:
            contents.extend([
                ContentFactory(user=request.user, content_object__user=request.user, order=3),
                ContentFactory(user=request.user, content_object__user=request.user, order=2),
                ContentFactory(user=request.user, content_object__user=request.user, order=1),
            ])
        view = UserDetailView(request=request, kwargs={"username": request.user.username})
        view.object = request.user
        view.target_user = request.user
        return request, view, contents

    def test_get_context_data_contains_content_objects(self, admin_client, rf):
        request, view, contents = self._get_request_view_and_content(rf)
        context = view.get_context_data()
        assert len(context["contents"]) == 3
        context_content = {content["content"] for content in context["contents"]}
        rendered = {content.content_object.render() for content in contents}
        assert context_content == rendered
        context_objs = {content["obj"] for content in context["contents"]}
        objs = set(contents)
        assert context_objs == objs

    def test_get_context_data_does_not_contain_content_for_other_users(self, admin_client, rf):
        request, view, contents = self._get_request_view_and_content(rf, create_content=False)
        user = UserFactory(); ContentFactory(user=user, content_object__user=user)
        user = UserFactory(); ContentFactory(user=user, content_object__user=user)
        user = UserFactory(); ContentFactory(user=user, content_object__user=user)
        context = view.get_context_data()
        assert len(context["contents"]) == 0

    def test_detail_view_renders(self, admin_client, rf):
        request, view, contents = self._get_request_view_and_content(rf)
        response = admin_client.get(request.user.get_absolute_url())
        assert response.status_code == 200

    def test_contents_queryset_returns_public_only_for_unauthenticated(self, admin_client, rf):
        request, view, contents = self._get_request_view_and_content(rf, create_content=False)
        ContentFactory(user=request.user, content_object__user=request.user, visibility=Visibility.SITE)
        ContentFactory(user=request.user, content_object__user=request.user, visibility=Visibility.SELF)
        ContentFactory(user=request.user, content_object__user=request.user, visibility=Visibility.LIMITED)
        public = ContentFactory(user=request.user, content_object__user=request.user, visibility=Visibility.PUBLIC)
        request.user = AnonymousUser()
        qs = view._get_contents_queryset()
        assert qs.count() == 1
        assert qs.first() == public

    def test_contents_queryset_returns_public_or_site_only_for_authenticated(self, admin_client, rf):
        request, view, contents = self._get_request_view_and_content(rf, create_content=False)
        site = ContentFactory(user=request.user, content_object__user=request.user, visibility=Visibility.SITE)
        ContentFactory(user=request.user, content_object__user=request.user, visibility=Visibility.SELF)
        ContentFactory(user=request.user, content_object__user=request.user, visibility=Visibility.LIMITED)
        public = ContentFactory(user=request.user, content_object__user=request.user, visibility=Visibility.PUBLIC)
        request.user = User.objects.get(username="admin")
        qs = view._get_contents_queryset()
        assert qs.count() == 2
        assert set(qs) == {public, site}

    def test_contents_queryset_returns_all_for_self(self, admin_client, rf):
        request, view, contents = self._get_request_view_and_content(rf, create_content=False)
        site = ContentFactory(user=request.user, content_object__user=request.user, visibility=Visibility.SITE)
        selff = ContentFactory(user=request.user, content_object__user=request.user, visibility=Visibility.SELF)
        limited = ContentFactory(user=request.user, content_object__user=request.user, visibility=Visibility.LIMITED)
        public = ContentFactory(user=request.user, content_object__user=request.user, visibility=Visibility.PUBLIC)
        qs = view._get_contents_queryset()
        assert qs.count() == 4
        assert set(qs) == {public, site, selff, limited}

    def test_contents_queryset_returns_content_in_correct_order(self, admin_client, rf):
        request, view, contents = self._get_request_view_and_content(rf)
        qs = view._get_contents_queryset()
        assert qs[0].id == contents[2].id
        assert qs[1].id == contents[1].id
        assert qs[2].id == contents[0].id


@pytest.mark.usefixtures("admin_client", "rf")
class TestOrganizeContentUserDetailView(object):
    def _get_request_view_and_content(self, rf, create_content=True):
        request = rf.get("/")
        request.user = UserFactory(visibility=Visibility.PUBLIC)
        contents = []
        if create_content:
            contents.extend([
                ContentFactory(user=request.user, content_object__user=request.user, order=3),
                ContentFactory(user=request.user, content_object__user=request.user, order=2),
                ContentFactory(user=request.user, content_object__user=request.user, order=1),
            ])
        view = OrganizeContentUserDetailView(request=request, kwargs={"username": request.user.username})
        view.object = request.user
        view.target_user = request.user
        return request, view, contents

    def test_view_renders(self, admin_client, rf):
        request, view, contents = self._get_request_view_and_content(rf)
        response = admin_client.get(reverse("users:detail-organize", kwargs={"username": request.user.username}))
        assert response.status_code == 200

    def test_save_sort_order_updates_order(self, admin_client, rf):
        request, view, contents = self._get_request_view_and_content(rf)
        qs = view._get_contents_queryset()
        assert qs[0].id == contents[2].id
        assert qs[1].id == contents[1].id
        assert qs[2].id == contents[0].id
        view._save_sort_order([contents[0].id, contents[1].id, contents[2].id])
        qs = view._get_contents_queryset()
        assert qs[0].id == contents[0].id
        assert qs[1].id == contents[1].id
        assert qs[2].id == contents[2].id

    def test_save_sort_order_skips_non_qs_contents(self, admin_client, rf):
        request, view, contents = self._get_request_view_and_content(rf)
        other_user = UserFactory()
        other_content = ContentFactory(user=other_user, content_object__user=other_user, order=100)
        view._save_sort_order([other_content.id])
        other_content.refresh_from_db()
        assert other_content.order == 100


@pytest.mark.usefixtures("admin_user", "client")
class TestProfileVisibilityForAnonymous(object):
    def test_visible_to_self_profile_requires_login_for_anonymous(self, admin_user, client):
        admin_user.visibility = Visibility.SELF
        admin_user.save()
        response = client.get("/u/admin/")
        assert response.status_code == 302

    def test_visible_to_limited_profile_requires_login_for_anonymous(self, admin_user, client):
        admin_user.visibility = Visibility.LIMITED
        admin_user.save()
        response = client.get("/u/admin/")
        assert response.status_code == 302

    def test_visible_to_site_profile_requires_login_for_anonymous(self, admin_user, client):
        admin_user.visibility = Visibility.SITE
        admin_user.save()
        response = client.get("/u/admin/")
        assert response.status_code == 302

    def test_public_profile_doesnt_require_login(self, admin_user, client):
        admin_user.visibility = Visibility.PUBLIC
        admin_user.save()
        response = client.get("/u/admin/")
        assert response.status_code == 200


@pytest.mark.usefixtures("admin_client")
class TestProfileVisibilityForLoggedInUsers(object):
    def test_visible_to_self_profile(self, admin_client):
        User.objects.filter(username="admin").update(visibility=Visibility.SELF)
        UserFactory(username="foobar", visibility=Visibility.SELF)
        response = admin_client.get("/u/admin/")
        assert response.status_code == 200
        response = admin_client.get("/u/foobar/")
        assert response.status_code == 302

    def test_visible_to_limited_profile(self, admin_client):
        User.objects.filter(username="admin").update(visibility=Visibility.LIMITED)
        UserFactory(username="foobar", visibility=Visibility.LIMITED)
        response = admin_client.get("/u/admin/")
        assert response.status_code == 200
        response = admin_client.get("/u/foobar/")
        assert response.status_code == 302

    def test_visible_to_site_profile(self, admin_client):
        User.objects.filter(username="admin").update(visibility=Visibility.SITE)
        UserFactory(username="foobar", visibility=Visibility.SITE)
        response = admin_client.get("/u/admin/")
        assert response.status_code == 200
        response = admin_client.get("/u/foobar/")
        assert response.status_code == 200

    def test_visible_to_public_profile(self, admin_client):
        User.objects.filter(username="admin").update(visibility=Visibility.PUBLIC)
        UserFactory(username="foobar", visibility=Visibility.PUBLIC)
        response = admin_client.get("/u/admin/")
        assert response.status_code == 200
        response = admin_client.get("/u/foobar/")
        assert response.status_code == 200
