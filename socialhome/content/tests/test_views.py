import pytest
from django.urls import reverse
from django.template.loader import render_to_string
from django.test.client import Client, RequestFactory

from socialhome.content.enums import ContentType
from socialhome.content.forms import ContentForm
from socialhome.content.models import Content
from socialhome.content.tests.factories import ContentFactory, LocalContentFactory, PublicContentFactory, \
    LimitedContentFactory
from socialhome.content.views import ContentCreateView, ContentUpdateView, ContentDeleteView
from socialhome.enums import Visibility
from socialhome.tests.utils import SocialhomeTestCase, SocialhomeCBVTestCase
from socialhome.users.models import Profile
from socialhome.users.tests.factories import UserFactory


class TestContentCreateView(SocialhomeCBVTestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.user = UserFactory()

    def setUp(self):
        super().setUp()
        self.req = RequestFactory().get("/")
        self.req.user = self.user

    def test_view_renders(self):
        with self.login(self.user):
            response = self.client.get(reverse("content:create"))
        assert response.status_code == 200

    def test_untrusted_editor_text_is_cleaned(self):
        self.user.trusted_editor = False
        self.user.save()
        form = ContentForm(data={"text": "<script>console.log</script>"}, user=self.user)
        form.full_clean()
        assert form.cleaned_data["text"] == "&lt;script&gt;console.log&lt;/script&gt;"

    def test_has_bookmarklet_in_context(self):
        with self.login(self.user):
            response = self.client.get(reverse("content:create"))
        self.assertIsNotNone(response.context["bookmarklet"])


class TestContentBookmarkletView(SocialhomeTestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.user = UserFactory()

    def test_view_renders(self):
        with self.login(self.user):
            self.get("content:bookmarklet")
            self.get("bookmarklet")
        self.response_200()


class TestContentUpdateViewCBV(SocialhomeCBVTestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.user = UserFactory()
        cls.content = ContentFactory(author=cls.user.profile)

    def setUp(self):
        super().setUp()
        self.request = RequestFactory().get("/")
        self.request.user = self.user
        self.view = self.get_instance(ContentUpdateView, request=self.request, pk=self.content.id)
        self.view.object = self.content

    def test_untrusted_editor_text_is_cleaned(self):
        self.user.trusted_editor = False
        self.user.save()
        form = ContentForm(
            data={"text": "<script>console.log</script>", "visibility": Visibility.PUBLIC.value},
            instance=self.content,
            user=self.user,
        )
        form.full_clean()
        self.assertEqual(form.cleaned_data["text"], "&lt;script&gt;console.log&lt;/script&gt;")


class TestContentUpdateView(SocialhomeTestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.user = UserFactory()
        cls.other_user = UserFactory()
        cls.content = ContentFactory(author=cls.user.profile)
        cls.limited_content = LimitedContentFactory(author=cls.user.profile)
        cls.limited_content.limited_visibilities.add(cls.other_user.profile)

    def test_limited_visibilities_keep_in_edit(self):
        with self.login(self.user):
            self.get("content:update", pk=self.limited_content.id)
        self.limited_content.refresh_from_db()
        self.assertEqual(self.limited_content.limited_visibilities.count(), 1)
        self.assertEqual(self.limited_content.limited_visibilities.first(), self.other_user.profile)

    def test_update_view_renders(self):
        with self.login(self.user):
            self.get("content:update", pk=self.content.id)
        self.response_200()

    def test_update_view_raises_if_user_does_not_own_content(self):
        with self.login(self.other_user):
            self.get("content:update", pk=self.content.id)
        self.response_404()

        with self.login(self.other_user):
            self.post(
                "content:update",
                data={
                    "text": "foobar",
                    "visibility": Visibility.PUBLIC.value,
                },
                pk=self.content.id,
            )
        self.response_404()


@pytest.mark.usefixtures("admin_client", "rf")
class TestContentDeleteView:
    def _get_request_view_and_content(self, rf, next=False):
        if next:
            request = rf.get("/?next=/foobar")
        else:
            request = rf.get("/")
        request.user = UserFactory()
        content = ContentFactory(author=request.user.profile)
        view = ContentDeleteView(request=request, kwargs={"pk": content.id})
        view.object = content
        return request, view, content

    def test_get_success_url(self, admin_client, rf):
        request, view, content = self._get_request_view_and_content(rf)
        assert view.get_success_url() == "/"
        request, view, content = self._get_request_view_and_content(rf, next=True)
        assert view.get_success_url() == "/foobar"

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
        cls.reply = PublicContentFactory(parent=cls.content)
        cls.share = PublicContentFactory(share_of=cls.content)
        cls.user = cls.content.author.user
        cls.profile = cls.content.author

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

    def test_content_view_renders_by_uuid(self):
        response = self.client.get(
            reverse("content:view-by-uuid", kwargs={"uuid": self.content.uuid}),
        )
        self.assertEqual(response.status_code, 200)

    def test_content_view_renders_by_slug(self):
        response = self.client.get(
            reverse("content:view-by-slug", kwargs={"pk": self.content.id, "slug": self.content.slug})
        )
        self.assertEqual(response.status_code, 200)

    def test_redirects_by_content_type(self):
        self.get("content:view", pk=self.content.id)
        self.response_200()
        self.get("content:view", pk=self.reply.id)
        self.response_302()
        self.get("content:view", pk=self.share.id)
        self.response_302()

    def test_has_json_context(self):
        self.get("content:view", pk=self.content.id)
        self.assertEqual(self.context["json_context"]["currentBrowsingProfileId"], None)
        self.assertEqual(self.context["json_context"]["isUserAuthenticated"], False)
        self.assertEqual(self.context["json_context"]["streamName"], "content__%s_%s" % (
            self.content.id, self.content.uuid))
        self.assertEqual(self.context["json_context"]["content"]["id"], self.content.id)

        # Authenticated
        with self.login(self.user):
            self.get("content:view", pk=self.content.id)
            self.assertEqual(self.context["json_context"]["currentBrowsingProfileId"], self.profile.id)
            self.assertEqual(self.context["json_context"]["isUserAuthenticated"], True)
            self.assertEqual(self.context["json_context"]["streamName"], "content__%s_%s" % (
                self.content.id, self.content.uuid))
            self.assertEqual(self.context["json_context"]["content"]["id"], self.content.id)


class TestContentReplyView(SocialhomeTestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.user = UserFactory()
        cls.content = ContentFactory(author=cls.user.profile)
        cls.limited_content = LimitedContentFactory(author=cls.user.profile)
        cls.limited_content.limited_visibilities.add(cls.user.profile)

    def test_view_renders(self):
        with self.login(self.content.author.user):
            response = self.client.get(reverse("content:reply", kwargs={"pk": self.content.id}))
        self.assertEqual(response.status_code, 200)

    def test_redirects_to_login_if_not_logged_in(self):
        response = self.client.get(reverse("content:reply", kwargs={"pk": self.content.id}))
        self.assertEqual(response.status_code, 302)
