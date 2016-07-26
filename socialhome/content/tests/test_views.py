import pytest
from django.core.urlresolvers import reverse

from socialhome.content.enums import ContentTarget
from socialhome.enums import Visibility
from socialhome.content.forms import PostForm
from socialhome.content.models import Content, Post
from socialhome.content.tests.factories import ContentFactory
from socialhome.content.views import ContentCreateView, ContentUpdateView, ContentDeleteView
from socialhome.users.models import User
from socialhome.users.tests.factories import UserFactory, ProfileFactory


@pytest.mark.usefixtures("admin_client", "settings")
class TestRootProfile(object):
    def test_home_view_rendered_without_root_profile(self, admin_client, settings):
        settings.SOCIALHOME_ROOT_PROFILE = None
        ProfileFactory(nickname="admin", user=User.objects.get(username="admin"))
        response = admin_client.get("/")
        assert response.templates[0].name == "pages/home.html"

    def test_home_view_rendered_with_root_profile(self, admin_client, settings):
        settings.SOCIALHOME_ROOT_PROFILE = "admin"
        ProfileFactory(nickname="admin", user=User.objects.get(username="admin"))
        response = admin_client.get("/")
        assert response.templates[0].name == "users/profile_detail.html"


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
        profile = ProfileFactory(nickname=request.user.username, user=request.user)
        form = PostForm(data={"text": "barfoo", "public": True}, user=request.user)
        response = view.form_valid(form)
        assert response.status_code == 302
        content = Content.objects.first()
        assert content.target == ContentTarget.PROFILE
        assert content.author == profile
        assert content.visibility == Visibility.PUBLIC
        post = content.content_object
        assert post.text == "barfoo"
        assert post.author == profile
        assert post.public == True

    def test_get_success_url(self, admin_client, rf):
        request, view = self._get_request_and_view(rf)
        profile = ProfileFactory(nickname=request.user.username, user=request.user)
        assert view.get_success_url() == "/u/%s/" % profile.nickname

    def test_create_view_renders(self, admin_client, rf):
        response = admin_client.get(reverse("content:create", kwargs={"location": "profile"}))
        assert response.status_code == 200

    def test_untrusted_editor_text_is_cleaned(self, admin_client, rf):
        request, view = self._get_request_and_view(rf)
        ProfileFactory(nickname=request.user.username, user=request.user)
        request.user.trusted_editor = False
        request.user.save()
        form = PostForm(data={"text": "<script>console.log</script>", "public": True}, user=request.user)
        form.full_clean()
        assert form.cleaned_data["text"] == "&lt;script&gt;console.log&lt;/script&gt;"


@pytest.mark.usefixtures("admin_client", "rf")
class TestContentUpdateView(object):
    def _get_request_view_and_content(self, rf):
        request = rf.get("/")
        request.user = UserFactory()
        profile = ProfileFactory(nickname=request.user.username, user=request.user)
        content = ContentFactory(author=profile, content_object__author=profile)
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
        form = PostForm(data={"text": "barfoo", "public": True}, instance=content.content_object, user=request.user)
        response = view.form_valid(form)
        assert response.status_code == 302
        content = Content.objects.first()
        assert content.target == ContentTarget.PROFILE
        assert content.author == request.user.profile
        assert content.visibility == Visibility.PUBLIC
        post = content.content_object
        assert post.text == "barfoo"
        assert post.author == request.user.profile
        assert post.public == True

    def test_get_success_url(self, admin_client, rf):
        request, view, content = self._get_request_view_and_content(rf)
        assert view.get_success_url() == "/u/%s/" % request.user.profile.nickname

    def test_update_view_renders(self, admin_client, rf):
        admin = User.objects.get(username="admin")
        profile = ProfileFactory(nickname=admin.username, user=admin)
        content = ContentFactory(author=profile, content_object__author=profile)
        response = admin_client.get(reverse("content:update", kwargs={"pk": content.id}))
        assert response.status_code == 200

    def test_update_view_raises_if_user_does_not_own_content(self, admin_client, rf):
        user = UserFactory()
        profile = ProfileFactory(nickname=user.username, user=user)
        admin = User.objects.get(username="admin")
        ProfileFactory(nickname=admin.username, user=admin)
        content = ContentFactory(author=profile, content_object__author=profile)
        response = admin_client.post(reverse("content:update", kwargs={"pk": content.id}), {
            "text": "foobar",
            "public": False,
        })
        assert response.status_code == 404

    def test_update_view_updates_content(self, admin_client, rf):
        admin = User.objects.get(username="admin")
        profile = ProfileFactory(nickname=admin.username, user=admin)
        content = ContentFactory(author=profile, content_object__author=profile)
        response = admin_client.post(reverse("content:update", kwargs={"pk": content.id}), {
            "text": "foobar",
            "public": False,
        })
        assert response.status_code == 302
        content.refresh_from_db()
        assert content.content_object.text == "foobar"
        assert not content.content_object.public

    def test_untrusted_editor_text_is_cleaned(self, admin_client, rf):
        request, view, content = self._get_request_view_and_content(rf)
        request.user.trusted_editor = False
        request.user.save()
        form = PostForm(
            data={"text": "<script>console.log</script>", "public": True}, instance=content.content_object,
            user=request.user
        )
        form.full_clean()
        assert form.cleaned_data["text"] == "&lt;script&gt;console.log&lt;/script&gt;"


@pytest.mark.usefixtures("admin_client", "rf")
class TestContentDeleteView(object):
    def _get_request_view_and_content(self, rf):
        request = rf.get("/")
        request.user = UserFactory()
        profile = ProfileFactory(nickname=request.user.username, user=request.user)
        content = ContentFactory(author=profile, content_object__author=profile)
        view = ContentDeleteView(request=request, kwargs={"pk": content.id})
        view.object = content
        return request, view, content

    def test_get_success_url(self, admin_client, rf):
        request, view, content = self._get_request_view_and_content(rf)
        assert view.get_success_url() == "/u/%s/" % request.user.profile.nickname

    def test_delete_view_renders(self, admin_client, rf):
        admin = User.objects.get(username="admin")
        profile = ProfileFactory(nickname=admin.username, user=admin)
        content = ContentFactory(author=profile, content_object__author=profile)
        response = admin_client.get(reverse("content:delete", kwargs={"pk": content.id}))
        assert response.status_code == 200

    def test_delete_deletes_content(self, admin_client, rf):
        admin = User.objects.get(username="admin")
        profile = ProfileFactory(nickname=admin.username, user=admin)
        content = ContentFactory(author=profile, content_object__author=profile)
        request = rf.post("/")
        request.user = admin
        response = admin_client.post(reverse("content:delete", kwargs={"pk": content.id}))
        assert response.status_code == 302
        assert Content.objects.count() == 0
        assert Post.objects.count() == 0

    def test_delete_view_raises_if_user_does_not_own_content(self, admin_client, rf):
        user = UserFactory()
        profile = ProfileFactory(nickname=user.username, user=user)
        content = ContentFactory(author=profile, content_object__author=profile)
        admin = User.objects.get(username="admin")
        ProfileFactory(nickname=admin.username, user=admin)
        response = admin_client.post(reverse("content:delete", kwargs={"pk": content.id}))
        assert response.status_code == 404
