from django.urls import reverse

from socialhome.models import ImageUpload
from socialhome.tests.utils import SocialhomeAPITestCase
from socialhome.users.tests.factories import UserFactory


class TestImageUploadView(SocialhomeAPITestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.user = UserFactory()

    def test_image_upload(self):
        # Anonymous user
        response = self.client.post(reverse("api-image-upload"), {"image": self.get_temp_image()}, format="multipart")
        self.assertEqual(response.status_code, 403)
        # User
        self.client.force_authenticate(self.user)
        response = self.client.post(reverse("api-image-upload"), {"image": self.get_temp_image()}, format="multipart")
        self.assertEqual(response.status_code, 201)
        code = response.data["code"]
        url = response.data["url"]
        self.assertIn("![](http://127.0.0.1:8000/media/uploads/", code)
        self.assertIn("http://127.0.0.1:8000/media/uploads/", url)
        image_upload = ImageUpload.objects.filter(user=self.user).first()
        self.assertEqual(image_upload.image.name, url.replace("http://127.0.0.1:8000/media/", ""))
