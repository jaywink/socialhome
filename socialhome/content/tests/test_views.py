import pytest
from django.core.urlresolvers import reverse

from socialhome.enums import Visibility
from socialhome.content.forms import ContentForm
from socialhome.content.models import Content
from socialhome.content.tests.factories import ContentFactory
from socialhome.content.views import ContentCreateView, ContentUpdateView, ContentDeleteView
from socialhome.users.models import Profile
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
        assert response.templates[0].name == "streams/profile.html"


@pytest.mark.usefixtures("admin_client", "rf")
class TestContentCreateView(object):
    def _get_request_and_view(self, rf):
        request = rf.get("/")
        request.user = UserFactory()
        view = ContentCreateView(request=request)
        return request, view

    def test_form_valid(self, admin_client, rf):
        request, view = self._get_request_and_view(rf)
        form = ContentForm(data={"text": "barfoo", "visibility": Visibility.PUBLIC.value}, user=request.user)
        response = view.form_valid(form)
        assert response.status_code == 302
        content = Content.objects.first()
        assert content.text == "barfoo"
        assert content.author == request.user.profile
        assert content.visibility == Visibility.PUBLIC

    def test_get_success_url(self, admin_client, rf):
        request, view = self._get_request_and_view(rf)
        assert view.get_success_url() == "/"

    def test_create_view_renders(self, admin_client, rf):
        response = admin_client.get(reverse("content:create"))
        assert response.status_code == 200

    def test_untrusted_editor_text_is_cleaned(self, admin_client, rf):
        request, view = self._get_request_and_view(rf)
        request.user.trusted_editor = False
        request.user.save()
        form = ContentForm(data={"text": "<script>console.log</script>"}, user=request.user)
        form.full_clean()
        assert form.cleaned_data["text"] == "&lt;script&gt;console.log&lt;/script&gt;"


@pytest.mark.usefixtures("admin_client", "rf")
class TestContentUpdateView(object):
    def _get_request_view_and_content(self, rf):
        request = rf.get("/")
        request.user = UserFactory()
        content = ContentFactory(author=request.user.profile)
        view = ContentUpdateView(request=request, kwargs={"pk": content.id})
        view.object = content
        return request, view, content

    def test_get_form_kwargs(self, admin_client, rf):
        request, view, content = self._get_request_view_and_content(rf)
        kwargs = view.get_form_kwargs()
        assert kwargs["instance"] == content

    def test_form_valid(self, admin_client, rf):
        request, view, content = self._get_request_view_and_content(rf)
        form = ContentForm(data={"text": "barfoo", "visibility": Visibility.PUBLIC.value},
                           instance=content, user=request.user)
        response = view.form_valid(form)
        assert response.status_code == 302
        content = Content.objects.first()
        assert content.author == request.user.profile
        assert content.visibility == Visibility.PUBLIC
        assert content.text == "barfoo"

    def test_get_success_url(self, admin_client, rf):
        request, view, content = self._get_request_view_and_content(rf)
        assert view.get_success_url() == "/"

    def test_update_view_renders(self, admin_client, rf):
        profile = Profile.objects.get(user__username="admin")
        content = ContentFactory(author=profile)
        response = admin_client.get(reverse("content:update", kwargs={"pk": content.id}))
        assert response.status_code == 200

    def test_update_view_raises_if_user_does_not_own_content(self, admin_client, rf):
        user = UserFactory()
        content = ContentFactory(author=user.profile)
        response = admin_client.post(reverse("content:update", kwargs={"pk": content.id}), {
            "text": "foobar",
            "visibility": Visibility.PUBLIC.value,
        })
        assert response.status_code == 404

    def test_update_view_updates_content(self, admin_client, rf):
        profile = Profile.objects.get(user__username="admin")
        content = ContentFactory(author=profile)
        response = admin_client.post(reverse("content:update", kwargs={"pk": content.id}), {
            "text": "foobar",
            "visibility": Visibility.SITE.value,
        })
        assert response.status_code == 302
        content.refresh_from_db()
        assert content.text == "foobar"
        assert content.visibility == Visibility.SITE

    def test_untrusted_editor_text_is_cleaned(self, admin_client, rf):
        request, view, content = self._get_request_view_and_content(rf)
        request.user.trusted_editor = False
        request.user.save()
        form = ContentForm(
            data={"text": "<script>console.log</script>", "visibility": Visibility.PUBLIC.value},
            instance=content,
            user=request.user
        )
        form.full_clean()
        assert form.cleaned_data["text"] == "&lt;script&gt;console.log&lt;/script&gt;"


@pytest.mark.usefixtures("admin_client", "rf")
class TestContentDeleteView(object):
    def _get_request_view_and_content(self, rf):
        request = rf.get("/")
        request.user = UserFactory()
        content = ContentFactory(author=request.user.profile)
        view = ContentDeleteView(request=request, kwargs={"pk": content.id})
        view.object = content
        return request, view, content

    def test_get_success_url(self, admin_client, rf):
        request, view, content = self._get_request_view_and_content(rf)
        assert view.get_success_url() == "/"

    def test_delete_view_renders(self, admin_client, rf):
        profile = Profile.objects.get(user__username="admin")
        content = ContentFactory(author=profile)
        response = admin_client.get(reverse("content:delete", kwargs={"pk": content.id}))
        assert response.status_code == 200

    def test_delete_deletes_content(self, admin_client, rf):
        profile = Profile.objects.get(user__username="admin")
        content = ContentFactory(author=profile)
        request = rf.post("/")
        request.user = profile.user
        response = admin_client.post(reverse("content:delete", kwargs={"pk": content.id}))
        assert response.status_code == 302
        assert Content.objects.count() == 0

    def test_delete_view_raises_if_user_does_not_own_content(self, admin_client, rf):
        user = UserFactory()
        content = ContentFactory(author=user.profile)
        response = admin_client.post(reverse("content:delete", kwargs={"pk": content.id}))
        assert response.status_code == 404
