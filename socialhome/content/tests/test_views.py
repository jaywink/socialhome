import pytest
from django.contrib.auth.models import AnonymousUser
from django.core.urlresolvers import reverse
from django.test import TestCase, override_settings
from django.test.client import Client

from socialhome.enums import Visibility
from socialhome.content.forms import ContentForm
from socialhome.content.models import Content
from socialhome.content.tests.factories import ContentFactory, LocalContentFactory
from socialhome.content.views import ContentCreateView, ContentUpdateView, ContentDeleteView
from socialhome.tests.utils import SocialhomeTestCase
from socialhome.users.models import Profile
from socialhome.users.tests.factories import UserFactory, AdminUserFactory


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


@pytest.mark.usefixtures("admin_client", "rf")
class TestContentCreateView:
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
class TestContentUpdateView:
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
class TestContentDeleteView:
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


class TestContentView(SocialhomeTestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.content = LocalContentFactory(visibility=Visibility.PUBLIC)
        cls.private_content = LocalContentFactory(visibility=Visibility.LIMITED)
        cls.client = Client()

    def test_content_view_renders_json_result(self):
        response = self.client.get(
            reverse("content:view", kwargs={"pk": self.content.id}),
            HTTP_X_REQUESTED_WITH="XMLHttpRequest"
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.content.dict_for_view(AnonymousUser()), response.json())

    def test_content_view_by_guid_renders_json_result(self):
        response = self.client.get(
            reverse("content:view-by-guid", kwargs={"guid": self.content.guid}),
            HTTP_X_REQUESTED_WITH="XMLHttpRequest"
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.content.dict_for_view(AnonymousUser()), response.json())

    def test_content_view_by_slug_renders_json_result(self):
        response = self.client.get(
            reverse("content:view-by-slug", kwargs={"pk": self.content.id, "slug": self.content.slug}),
            HTTP_X_REQUESTED_WITH="XMLHttpRequest"
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.content.dict_for_view(AnonymousUser()), response.json())

    def test_content_view_redirects_to_login_for_private_content_except_if_owned(self):
        self.client.force_login(self.content.author.user)
        response = self.client.get(
            reverse("content:view", kwargs={"pk": self.private_content.id}),
            HTTP_X_REQUESTED_WITH="XMLHttpRequest"
        )
        self.assertEqual(response.status_code, 302)
        self.client.force_login(self.private_content.author.user)
        response = self.client.get(
            reverse("content:view", kwargs={"pk": self.private_content.id}),
            HTTP_X_REQUESTED_WITH="XMLHttpRequest"
        )
        self.assertEqual(response.status_code, 200)

    def test_content_view_renders(self):
        response = self.client.get(
            reverse("content:view", kwargs={"pk": self.content.id})
        )
        self.assertEqual(response.status_code, 200)

    def test_content_view_renders_by_guid(self):
        response = self.client.get(
            reverse("content:view-by-guid", kwargs={"guid": self.content.guid}),
        )
        self.assertEqual(response.status_code, 200)

    def test_content_view_renders_by_slug(self):
        response = self.client.get(
            reverse("content:view-by-slug", kwargs={"pk": self.content.id, "slug": self.content.slug})
        )
        self.assertEqual(response.status_code, 200)

    def test_content_view_content(self):
        response = self.client.get(
            reverse("content:view", kwargs={"pk": self.content.id})
        )
        self.assertNotContains(response, "modal-dialog modal-lg")
        self.assertContains(response, self.content.author.safer_image_url_small)
        self.assertContains(response, self.content.author.name)
        self.assertContains(response, self.content.author.handle)
        self.assertNotContains(response, 'data-dismiss="modal"')
        self.assertContains(response, self.content.rendered)
        self.assertContains(response, self.content.humanized_timestamp)
        self.assertContains(response, self.content.formatted_timestamp)
        self.assertContains(response, '<span id="content-bar-actions" class="hidden"')
        self.assertNotContains(response, "modal-footer")
        self.assertContains(response, 'var socialhomeStream = "content__%s' % self.content.guid)

    def test_content_view_content_as_author(self):
        self.client.force_login(self.content.author.user)
        response = self.client.get(
            reverse("content:view", kwargs={"pk": self.content.id})
        )
        self.assertNotContains(response, '<span id="content-bar-actions" class="hidden"')

    def test_content_view_guid_quoting(self):
        content = ContentFactory(guid="foo@bar", visibility=Visibility.PUBLIC)
        response = self.client.get(
            reverse("content:view", kwargs={"pk": content.id})
        )
        self.assertEqual(response.context["stream_name"], "foo%40bar")


class TestContentReplyView(TestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        user = UserFactory()
        cls.content = ContentFactory(author=user.profile)

    def setUp(self):
        super().setUp()
        self.client = Client()

    def test_view_renders(self):
        self.client.force_login(self.content.author.user)
        response = self.client.get(reverse("content:reply", kwargs={"pk": self.content.id}))
        self.assertEqual(response.status_code, 200)

    def test_redirects_to_login_if_not_logged_in(self):
        response = self.client.get(reverse("content:reply", kwargs={"pk": self.content.id}))
        self.assertEqual(response.status_code, 302)

    def test_form_valid(self):
        self.client.force_login(self.content.author.user)
        response = self.client.post(
            reverse("content:reply", kwargs={"pk": self.content.id}),
            {"text": "foobar", "visibility": 0, "pinned": False}
        )
        self.assertEqual(response.status_code, 302)
        self.content.refresh_from_db()
        self.assertEqual(self.content.children.count(), 1)
