import tempfile

from PIL import Image
from django.test import override_settings
from django.urls import reverse
from test_plus import TestCase

from socialhome.content.models import Content
from socialhome.content.tests.factories import ContentFactory
from socialhome.enums import Visibility
from socialhome.tests.utils import SocialhomeAPITestCase
from socialhome.users.tests.factories import UserFactory, AdminUserFactory, ProfileFactory


class TestContentViewSet(SocialhomeAPITestCase, TestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.user = UserFactory()
        cls.staff_user = AdminUserFactory()
        cls.public_content = ContentFactory(visibility=Visibility.PUBLIC)
        cls.limited_content = ContentFactory(visibility=Visibility.LIMITED)
        cls.site_content = ContentFactory(visibility=Visibility.SITE)
        cls.self_content = ContentFactory(visibility=Visibility.SELF)
        cls.other_profile = ProfileFactory()

    def setUp(self):
        super().setUp()
        self.public_content.refresh_from_db()
        self.limited_content.refresh_from_db()
        self.site_content.refresh_from_db()
        self.self_content.refresh_from_db()

    def _check_result_ids(self, expected):
        ids = {result["id"] for result in self.last_response.data["results"]}
        self.assertEqual(ids, expected)

    def test_list_content(self):
        self.get("api:content-list")
        self.response_200()
        self.assertEqual(len(self.last_response.data["results"]), 1)
        self.assertEqual(self.last_response.data["results"][0]["id"], self.public_content.id)

        with self.login(self.user):
            self.get("api:content-list")
            self.response_200()
            self.assertEqual(len(self.last_response.data["results"]), 2)
            self._check_result_ids({self.public_content.id, self.site_content.id})

        with self.login(self.staff_user):
            self.get("api:content-list")
            self.response_200()
            self.assertEqual(len(self.last_response.data["results"]), 4)
            self._check_result_ids({self.public_content.id, self.site_content.id, self.limited_content.id,
                                    self.self_content.id})

    def test_detail(self):
        self.get("api:content-detail", pk=self.public_content.id)
        self.response_200()
        self.get("api:content-detail", pk=self.limited_content.id)
        self.response_404()
        self.get("api:content-detail", pk=self.site_content.id)
        self.response_404()
        self.get("api:content-detail", pk=self.self_content.id)
        self.response_404()

        with self.login(self.user):
            self.get("api:content-detail", pk=self.public_content.id)
            self.response_200()
            self.get("api:content-detail", pk=self.limited_content.id)
            self.response_404()
            self.get("api:content-detail", pk=self.site_content.id)
            self.response_200()
            self.get("api:content-detail", pk=self.self_content.id)
            self.response_404()

        with self.login(self.staff_user):
            self.get("api:content-detail", pk=self.public_content.id)
            self.response_200()
            self.get("api:content-detail", pk=self.limited_content.id)
            self.response_200()
            self.get("api:content-detail", pk=self.site_content.id)
            self.response_200()
            self.get("api:content-detail", pk=self.self_content.id)
            self.response_200()

    def test_update(self):
        self.patch("api:content-detail", data={"text": "Foobar"}, pk=self.public_content.id)
        self.response_403()
        self.patch("api:content-detail", data={"text": "Foobar"}, pk=self.limited_content.id)
        self.response_403()
        self.patch("api:content-detail", data={"text": "Foobar"}, pk=self.site_content.id)
        self.response_403()
        self.patch("api:content-detail", data={"text": "Foobar"}, pk=self.self_content.id)
        self.response_403()

        with self.login(self.user):
            self.patch("api:content-detail", data={"text": "Foobar"}, pk=self.public_content.id)
            self.response_403()
            self.patch("api:content-detail", data={"text": "Foobar"}, pk=self.limited_content.id)
            self.response_404()
            self.patch("api:content-detail", data={"text": "Foobar"}, pk=self.site_content.id)
            self.response_403()
            self.patch("api:content-detail", data={"text": "Foobar"}, pk=self.self_content.id)
            self.response_404()

        with self.login(self.staff_user):
            self.patch("api:content-detail", data={"text": "Foobar"}, pk=self.public_content.id)
            self.response_403()
            self.patch("api:content-detail", data={"text": "Foobar"}, pk=self.limited_content.id)
            self.response_403()
            self.patch("api:content-detail", data={"text": "Foobar"}, pk=self.site_content.id)
            self.response_403()
            self.patch("api:content-detail", data={"text": "Foobar"}, pk=self.self_content.id)
            self.response_403()

        # Make self.user own the content
        Content.objects.filter(id__in=[
            self.public_content.id, self.limited_content.id, self.site_content.id, self.self_content.id,
        ]).update(author_id=self.user.profile.id)
        with self.login(self.user):
            self.patch("api:content-detail", data={"text": "Foobar"}, pk=self.public_content.id)
            self.response_200()
            self.patch("api:content-detail", data={"text": "Foobar"}, pk=self.limited_content.id)
            self.response_200()
            self.patch("api:content-detail", data={"text": "Foobar"}, pk=self.site_content.id)
            self.response_200()
            self.patch("api:content-detail", data={"text": "Foobar"}, pk=self.self_content.id)
            self.response_200()

    def test_delete(self):
        self.delete("api:content-detail", pk=self.public_content.id)
        self.response_403()
        self.delete("api:content-detail", pk=self.limited_content.id)
        self.response_403()
        self.delete("api:content-detail", pk=self.site_content.id)
        self.response_403()
        self.delete("api:content-detail", pk=self.self_content.id)
        self.response_403()

        with self.login(self.user):
            self.delete("api:content-detail", pk=self.public_content.id)
            self.response_403()
            self.delete("api:content-detail", pk=self.limited_content.id)
            self.response_404()
            self.delete("api:content-detail", pk=self.site_content.id)
            self.response_403()
            self.delete("api:content-detail", pk=self.self_content.id)
            self.response_404()

        with self.login(self.staff_user):
            self.delete("api:content-detail", pk=self.public_content.id)
            self.response_403()
            self.delete("api:content-detail", pk=self.limited_content.id)
            self.response_403()
            self.delete("api:content-detail", pk=self.site_content.id)
            self.response_403()
            self.delete("api:content-detail", pk=self.self_content.id)
            self.response_403()

        # Make self.user own the content
        Content.objects.filter(id__in=[
            self.public_content.id, self.limited_content.id, self.site_content.id, self.self_content.id,
        ]).update(author_id=self.user.profile.id)
        with self.login(self.user):
            self.delete("api:content-detail", pk=self.public_content.id)
            self.assertEqual(self.last_response.status_code, 204)
            self.delete("api:content-detail", pk=self.limited_content.id)
            self.assertEqual(self.last_response.status_code, 204)
            self.delete("api:content-detail", pk=self.site_content.id)
            self.assertEqual(self.last_response.status_code, 204)
            self.delete("api:content-detail", pk=self.self_content.id)
            self.assertEqual(self.last_response.status_code, 204)

    def test_post(self):
        data = {
            "text": "Test", "pinned": False, "order": 1, "service_label": "", "visibility": Visibility.PUBLIC,
        }
        self.post("api:content-list", data=data)
        self.response_403()

        with self.login(self.user):
            data.update({"author": self.user.profile.id})
            self.post("api:content-list", data=data)
            self.response_201()

        with self.login(self.staff_user):
            data.update({"author": self.staff_user.profile.id})
            self.post("api:content-list", data=data)
            self.response_201()

    def test_post_creates_as_request_user(self):
        data = {
            "text": "Test", "pinned": False, "order": 1, "service_label": "", "visibility": Visibility.PUBLIC,
            "author": self.other_profile.id,
        }

        with self.login(self.user):
            self.post("api:content-list", data=data)
            content = Content.objects.get(id=self.last_response.data["id"])
            self.assertEqual(content.author_id, self.user.profile.id)

        with self.login(self.staff_user):
            self.post("api:content-list", data=data)
            content = Content.objects.get(id=self.last_response.data["id"])
            self.assertEqual(content.author_id, self.staff_user.profile.id)


class TestImageUploadView(SocialhomeAPITestCase, TestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.user = UserFactory()

    @override_settings(MEDIA_ROOT=tempfile.gettempdir())
    def test_image_upload(self):
        image = Image.new("RGB", (100, 100))
        tmp_file = tempfile.NamedTemporaryFile(suffix=".jpg")
        image.save(tmp_file)
        # Anonymous user
        tmp_file.seek(0)
        response = self.client.post(reverse("api-image-upload"), {"image": tmp_file}, format="multipart")
        self.assertEqual(response.status_code, 403)
        # User
        self.client.force_authenticate(self.user)
        tmp_file.seek(0)
        response = self.client.post(reverse("api-image-upload"), {"image": tmp_file}, format="multipart")
        self.assertEqual(response.status_code, 201)
        code = response.data["code"]
        url = response.data["url"]
        self.assertIn("![](http://127.0.0.1:8000/media/markdownx/", code)
        self.assertIn("http://127.0.0.1:8000/media/markdownx/", url)
