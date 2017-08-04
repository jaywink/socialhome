import tempfile

from PIL import Image
from django.test import override_settings
from django.urls import reverse
from test_plus import TestCase

from socialhome.models import ImageUpload
from socialhome.tests.utils import SocialhomeAPITestCase
from socialhome.users.tests.factories import UserFactory


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
        self.assertIn("![](http://127.0.0.1:8000/media/uploads/", code)
        self.assertIn("http://127.0.0.1:8000/media/uploads/", url)
        image_upload = ImageUpload.objects.filter(user=self.user).first()
        self.assertEqual(image_upload.image.name, url.replace("http://127.0.0.1:8000/media/", ""))
