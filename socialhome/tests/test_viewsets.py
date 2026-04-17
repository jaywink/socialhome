from django.urls import reverse
from rest_framework.authtoken.models import Token

from socialhome.tests.utils import SocialhomeAPITestCase
from socialhome.users.tests.factories import UserFactory


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
                          "finger": self.user.profile.finger,
                          "image_url_large": self.user.profile.safer_image_url_large,
                          "image_url_medium": self.user.profile.safer_image_url_medium,
                          "image_url_small": self.user.profile.safer_image_url_small,
                          "is_local": self.user.profile.is_local,
                          "name": self.user.profile.name,
                          "url": self.user.profile.url,
                          "avatar_url": self.user.profile.avatar_url,
                          "protocols": ["activitypub", "diaspora"],
                          "user_following": False,
                          "token": Token.objects.get(user=self.user).key})
