import pytest
from django.test import RequestFactory
from test_plus.test import TestCase

from socialhome.content.tests.factories import ContentFactory
from socialhome.users.tests.factories import UserFactory
from socialhome.users.views import UserRedirectView, UserUpdateView, UserDetailView


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
        request.user = UserFactory()
        contents = []
        if create_content:
            contents.extend([
                ContentFactory(user=request.user, content_object__user=request.user),
                ContentFactory(user=request.user, content_object__user=request.user),
                ContentFactory(user=request.user, content_object__user=request.user),
            ])
        view = UserDetailView(request=request, kwargs={"username": request.user.username})
        view.object = request.user
        return request, view, contents

    def test_get_context_data_contains_content_objects(self, admin_client, rf):
        request, view, contents = self._get_request_view_and_content(rf)
        context = view.get_context_data()
        assert len(context["contents"]) == 3
        for i in range(3):
            assert context["contents"][i]["content"] == contents[i].content_object.render()
            assert context["contents"][i]["obj"] == contents[i]

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
