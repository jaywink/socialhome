from django.urls import reverse
from rest_framework.authtoken.models import Token

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


class TestObtainSocialhomeAuthToken(SocialhomeAPITestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.user = UserFactory()

    def test_user_missing(self):
        response = self.post(reverse("api-token-auth"))
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data["username"], ["This field is required."])

    def test_password_missing(self):
        response = self.post(reverse("api-token-auth"))
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data["password"], ["This field is required."])

    def test_unable_to_login(self):
        response = self.post(reverse("api-token-auth"),
                             data={"username": self.user.username, "password": "lol"})
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data, {'non_field_errors': ['Unable to log in with provided credentials.']})

    def test_authentication(self):
        response = self.post(reverse("api-token-auth"),
                             data={"username": self.user.username, "password": "password"})
        self.assertEqual(response.data,
                         {"uuid": str(self.user.profile.uuid),
                          "handle": self.user.profile.handle,
                          "home_url": self.user.profile.home_url,
                          "id": self.user.profile.id,
                          "fid": self.user.profile.fid,
                          "image_url_small": self.user.profile.safer_image_url_small,
                          "is_local": self.user.profile.is_local,
                          "name": self.user.profile.name,
                          "url": self.user.profile.url,
                          "token": Token.objects.get(user=self.user).key})
