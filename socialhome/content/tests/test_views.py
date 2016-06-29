import pytest

from socialhome.content.enums import ContentTarget, Visibility
from socialhome.content.forms import PostForm
from socialhome.content.models import Content
from socialhome.content.tests.factories import ContentFactory
from socialhome.content.views import ContentCreateView, ContentUpdateView
from socialhome.users.tests.factories import UserFactory


@pytest.mark.usefixtures("admin_client", "settings")
class TestRootProfile(object):
    def test_home_view_rendered_without_root_profile(self, admin_client, settings):
        settings.SOCIALHOME_ROOT_PROFILE = None
        response = admin_client.get("/")
        assert response.templates[0].name == "pages/home.html"

    def test_home_view_rendered_with_root_profile(self, admin_client, settings):
        settings.SOCIALHOME_ROOT_PROFILE = "admin"
        response = admin_client.get("/")
        assert response.templates[0].name == "users/user_detail.html"


@pytest.mark.usefixtures("admin_client", "rf")
class TestContentCreateView(object):
    def _get_request_and_view(self, rf):
        request = rf.get("/")
        request.user = UserFactory()
        view = ContentCreateView(request=request, kwargs={"location": "profile"})
        return request, view

    def test_get_form_class(self, admin_client, rf):
        view = ContentCreateView()
        form = view.get_form_class()
        assert form == PostForm

    def test_form_valid(self, admin_client, rf):
        request, view = self._get_request_and_view(rf)
        form = PostForm(data={"text": "barfoo", "public": True})
        response = view.form_valid(form)
        assert response.status_code == 302
        content = Content.objects.first()
        assert content.target == ContentTarget.PROFILE
        assert content.user == request.user
        assert content.visibility == Visibility.PUBLIC
        post = content.content_object
        assert post.text == "barfoo"
        assert post.user == request.user
        assert post.public == True

    def test_get_success_url(self, admin_client, rf):
        request, view = self._get_request_and_view(rf)
        assert view.get_success_url() == "/u/%s/" % request.user.username


@pytest.mark.usefixtures("admin_client", "rf")
class TestContentUpdateView(object):
    def _get_request_view_and_content(self, rf):
        request = rf.get("/")
        request.user = UserFactory()
        content = ContentFactory(user=request.user, content_object__user=request.user)
        view = ContentUpdateView(request=request, kwargs={"pk": content.id})
        view.object = content
        return request, view, content

    def test_get_form_class(self, admin_client, rf):
        request, view, content = self._get_request_view_and_content(rf)
        form = view.get_form_class()
        assert form == PostForm

    def test_get_form_kwargs(self, admin_client, rf):
        request, view, content = self._get_request_view_and_content(rf)
        kwargs = view.get_form_kwargs()
        assert kwargs["instance"] == content.content_object

    def test_form_valid(self, admin_client, rf):
        request, view, content = self._get_request_view_and_content(rf)
        form = PostForm(data={"text": "barfoo", "public": True}, instance=content.content_object)
        response = view.form_valid(form)
        assert response.status_code == 302
        content = Content.objects.first()
        assert content.target == ContentTarget.PROFILE
        assert content.user == request.user
        assert content.visibility == Visibility.PUBLIC
        post = content.content_object
        assert post.text == "barfoo"
        assert post.user == request.user
        assert post.public == True

    def test_get_success_url(self, admin_client, rf):
        request, view, content = self._get_request_view_and_content(rf)
        assert view.get_success_url() == "/u/%s/" % request.user.username
