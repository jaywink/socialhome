from django.urls import reverse
from rest_framework.test import APITestCase

from socialhome.enums import Visibility
from socialhome.users.models import Profile
from socialhome.users.tests.factories import UserFactory, ProfileFactory


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
        self.assertEqual(len(response.data.get("results")), 1)
        self.assertEqual(response.data.get("results")[0]["username"], self.user.username)
        # Staff user authenticated
        self.client.login(username=self.staff_user.username, password="password")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data.get("results")), 2)

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


class TestProfileViewSet(APITestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.user = UserFactory()
        cls.profile = cls.user.profile
        cls.staff_user = UserFactory(is_staff=True)
        cls.staff_profile = cls.staff_user.profile
        cls.site_profile = ProfileFactory(visibility=Visibility.SITE)
        cls.self_profile = ProfileFactory(visibility=Visibility.SELF)
        cls.limited_profile = ProfileFactory(visibility=Visibility.LIMITED)
        Profile.objects.filter(id=cls.profile.id).update(visibility=Visibility.PUBLIC)

    def test_profile_list(self):
        url = reverse("api:profile-list")
        # Not authenticated
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data.get("results")), 1)
        self.assertEqual(response.data.get("results")[0]["handle"], self.profile.handle)
        # Normal user authenticated
        self.client.login(username=self.user.username, password="password")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data.get("results")), 2)
        for data in response.data.get("results"):
            self.assertTrue(data["handle"] in [self.profile.handle, self.site_profile.handle])
        # Staff user authenticated
        self.client.login(username=self.staff_user.username, password="password")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data.get("results")), 5)

    def test_profile_get(self):
        # Not authenticated
        response = self.client.get(reverse("api:profile-detail", kwargs={"pk": self.profile.id}))
        self.assertEqual(response.status_code, 200)
        response = self.client.get(reverse("api:profile-detail", kwargs={"pk": self.site_profile.id}))
        self.assertEqual(response.status_code, 404)
        response = self.client.get(reverse("api:profile-detail", kwargs={"pk": self.self_profile.id}))
        self.assertEqual(response.status_code, 404)
        # Normal user authenticated
        self.client.login(username=self.user.username, password="password")
        response = self.client.get(reverse("api:profile-detail", kwargs={"pk": self.profile.id}))
        self.assertEqual(response.status_code, 200)
        response = self.client.get(reverse("api:profile-detail", kwargs={"pk": self.site_profile.id}))
        self.assertEqual(response.status_code, 200)
        response = self.client.get(reverse("api:profile-detail", kwargs={"pk": self.self_profile.id}))
        self.assertEqual(response.status_code, 404)
        # Staff user authenticated
        self.client.login(username=self.staff_user.username, password="password")
        response = self.client.get(reverse("api:profile-detail", kwargs={"pk": self.profile.id}))
        self.assertEqual(response.status_code, 200)
        response = self.client.get(reverse("api:profile-detail", kwargs={"pk": self.site_profile.id}))
        self.assertEqual(response.status_code, 200)
        response = self.client.get(reverse("api:profile-detail", kwargs={"pk": self.self_profile.id}))
        self.assertEqual(response.status_code, 200)

    def test_profile_edit(self):
        # Not authenticated
        response = self.client.patch(reverse("api:profile-detail", kwargs={"pk": self.profile.id}), {"name": "foo"})
        self.assertEqual(response.status_code, 403)
        response = self.client.patch(
            reverse("api:profile-detail", kwargs={"pk": self.site_profile.id}), {"name": "foo"}
        )
        self.assertEqual(response.status_code, 404)
        response = self.client.patch(
            reverse("api:profile-detail", kwargs={"pk": self.self_profile.id}), {"name": "foo"}
        )
        self.assertEqual(response.status_code, 404)
        # Normal user authenticated
        self.client.login(username=self.user.username, password="password")
        response = self.client.patch(reverse("api:profile-detail", kwargs={"pk": self.profile.id}), {"name": "foo"})
        self.assertEqual(response.status_code, 200)
        response = self.client.patch(
            reverse("api:profile-detail", kwargs={"pk": self.site_profile.id}), {"name": "foo"}
        )
        self.assertEqual(response.status_code, 403)
        response = self.client.patch(
            reverse("api:profile-detail", kwargs={"pk": self.self_profile.id}), {"name": "foo"}
        )
        self.assertEqual(response.status_code, 404)
        # Staff user authenticated
        self.client.login(username=self.staff_user.username, password="password")
        response = self.client.patch(reverse("api:profile-detail", kwargs={"pk": self.profile.id}), {"name": "foo"})
        self.assertEqual(response.status_code, 403)
        response = self.client.patch(
            reverse("api:profile-detail", kwargs={"pk": self.site_profile.id}), {"name": "foo"}
        )
        self.assertEqual(response.status_code, 403)
        response = self.client.patch(
            reverse("api:profile-detail", kwargs={"pk": self.self_profile.id}), {"name": "foo"}
        )
        self.assertEqual(response.status_code, 403)

    def test_read_only_fields(self):
        self.client.login(username=self.user.username, password="password")
        for field in ("id", "user", "guid", "handle", "rsa_public_key", "image_url_large",
                      "image_url_medium", "image_url_small"):
            response = self.client.patch(reverse("api:profile-detail", kwargs={"pk": self.profile.id}), {field: "82"})
            self.assertEqual(response.data.get(field), getattr(self.profile, field if field != "user" else "user_id"))
        for field in ("name", "location", "nsfw"):
            response = self.client.patch(
                reverse("api:profile-detail", kwargs={"pk": self.profile.id}),
                {field: "82" if field != "nsfw" else not getattr(self.profile, "nsfw")}
            )
            self.assertEqual(
                str(response.data.get(field)), "82" if field != "nsfw" else str(not getattr(self.profile, "nsfw"))
            )

    def test_user_add_follower(self):
        # Not authenticated
        response = self.client.post(reverse("api:profile-add-follower", kwargs={"pk": self.profile.id}), {
            "guid": self.profile.guid,
        })
        self.assertEqual(response.status_code, 403)
        # Normal user authenticated
        self.client.login(username=self.user.username, password="password")
        response = self.client.post(reverse("api:profile-add-follower", kwargs={"pk": self.staff_profile.id}), {
            "guid": self.profile.guid,
        })
        self.assertEqual(response.status_code, 404)
        response = self.client.post(reverse("api:profile-add-follower", kwargs={"pk": self.profile.id}), {
            "guid": self.site_profile.guid,
        })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["status"], "Follower added.")
        # Staff user authenticated
        self.client.login(username=self.staff_user.username, password="password")
        response = self.client.post(reverse("api:profile-add-follower", kwargs={"pk": self.profile.id}), {
            "guid": self.staff_profile.guid,
        })
        self.assertEqual(response.status_code, 403)
        response = self.client.post(reverse("api:profile-add-follower", kwargs={"pk": self.staff_profile.id}), {
            "guid": self.profile.guid,
        })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["status"], "Follower added.")

    def test_user_remove_follower(self):
        # Not authenticated
        response = self.client.post(reverse("api:profile-remove-follower", kwargs={"pk": self.profile.id}), {
            "guid": self.profile.guid,
        })
        self.assertEqual(response.status_code, 403)
        # Normal user authenticated
        self.client.login(username=self.user.username, password="password")
        response = self.client.post(reverse("api:profile-remove-follower", kwargs={"pk": self.staff_profile.id}), {
            "guid": self.profile.guid,
        })
        self.assertEqual(response.status_code, 404)
        response = self.client.post(reverse("api:profile-remove-follower", kwargs={"pk": self.profile.id}), {
            "guid": self.staff_profile.guid,
        })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["status"], "Follower removed.")
        # Staff user authenticated
        self.client.login(username=self.staff_user.username, password="password")
        response = self.client.post(reverse("api:profile-remove-follower", kwargs={"pk": self.profile.id}), {
            "guid": self.staff_profile.guid,
        })
        self.assertEqual(response.status_code, 403)
        response = self.client.post(reverse("api:profile-remove-follower", kwargs={"pk": self.staff_profile.id}), {
            "guid": self.profile.guid,
        })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["status"], "Follower removed.")
