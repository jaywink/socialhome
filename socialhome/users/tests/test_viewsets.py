from django.urls import reverse
from rest_framework.test import APITestCase

from socialhome.enums import Visibility
from socialhome.users.models import Profile
from socialhome.users.tests.factories import UserFactory


class TestUserViewSet(APITestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.user = UserFactory()
        cls.staff_user = UserFactory(is_staff=True)
        Profile.objects.filter(user_id__in=[cls.user.id, cls.staff_user.id]).update(visibility=Visibility.PUBLIC)

    def test_user_list(self):
        url = reverse("api:user-list")
        # Not authenticated
        response = self.client.get(url)
        self.assertEqual(response.status_code, 403)
        # Normal user authenticated
        self.client.login(username=self.user.username, password="password")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["username"], self.user.username)
        # Staff user authenticated
        self.client.login(username=self.staff_user.username, password="password")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 2)

    def test_user_get(self):
        # Not authenticated
        response = self.client.get(reverse("api:user-detail", kwargs={"pk": self.user.id}))
        self.assertEqual(response.status_code, 403)
        # Normal user authenticated
        self.client.login(username=self.user.username, password="password")
        response = self.client.get(reverse("api:user-detail", kwargs={"pk": self.staff_user.id}))
        self.assertEqual(response.status_code, 404)
        response = self.client.get(reverse("api:user-detail", kwargs={"pk": self.user.id}))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["username"], self.user.username)
        # Staff user authenticated
        self.client.login(username=self.staff_user.username, password="password")
        response = self.client.get(reverse("api:user-detail", kwargs={"pk": self.staff_user.id}))
        self.assertEqual(response.status_code, 200)
        response = self.client.get(reverse("api:user-detail", kwargs={"pk": self.user.id}))
        self.assertEqual(response.status_code, 200)

    def test_user_add_follower(self):
        # Not authenticated
        response = self.client.post(reverse("api:user-add-follower", kwargs={"pk": self.user.id}), {
            "guid": self.user.profile.guid,
        })
        self.assertEqual(response.status_code, 403)
        # Normal user authenticated
        self.client.login(username=self.user.username, password="password")
        response = self.client.post(reverse("api:user-add-follower", kwargs={"pk": self.staff_user.id}), {
            "guid": self.user.profile.guid,
        })
        self.assertEqual(response.status_code, 404)
        response = self.client.post(reverse("api:user-add-follower", kwargs={"pk": self.user.id}), {
            "guid": self.staff_user.profile.guid,
        })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["status"], "Follower added.")
        # Staff user authenticated
        self.client.login(username=self.staff_user.username, password="password")
        response = self.client.post(reverse("api:user-add-follower", kwargs={"pk": self.user.id}), {
            "guid": self.staff_user.profile.guid,
        })
        self.assertEqual(response.status_code, 403)
        response = self.client.post(reverse("api:user-add-follower", kwargs={"pk": self.staff_user.id}), {
            "guid": self.user.profile.guid,
        })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["status"], "Follower added.")

    def test_user_remove_follower(self):
        # Not authenticated
        response = self.client.post(reverse("api:user-remove-follower", kwargs={"pk": self.user.id}), {
            "guid": self.user.profile.guid,
        })
        self.assertEqual(response.status_code, 403)
        # Normal user authenticated
        self.client.login(username=self.user.username, password="password")
        response = self.client.post(reverse("api:user-remove-follower", kwargs={"pk": self.staff_user.id}), {
            "guid": self.user.profile.guid,
        })
        self.assertEqual(response.status_code, 404)
        response = self.client.post(reverse("api:user-remove-follower", kwargs={"pk": self.user.id}), {
            "guid": self.staff_user.profile.guid,
        })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["status"], "Follower removed.")
        # Staff user authenticated
        self.client.login(username=self.staff_user.username, password="password")
        response = self.client.post(reverse("api:user-remove-follower", kwargs={"pk": self.user.id}), {
            "guid": self.staff_user.profile.guid,
        })
        self.assertEqual(response.status_code, 403)
        response = self.client.post(reverse("api:user-remove-follower", kwargs={"pk": self.staff_user.id}), {
            "guid": self.user.profile.guid,
        })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["status"], "Follower removed.")
