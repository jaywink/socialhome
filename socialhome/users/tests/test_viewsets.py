from django.test import override_settings
from django.urls import reverse

from socialhome.enums import Visibility
from socialhome.tests.utils import SocialhomeAPITestCase
from socialhome.users.models import Profile
from socialhome.users.tasks.exports import create_user_export
from socialhome.users.tests.factories import UserFactory, ProfileFactory


class TestUserViewSet(SocialhomeAPITestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.user = UserFactory()
        cls.staff_user = UserFactory(is_staff=True)
        Profile.objects.filter(user_id__in=[cls.user.id, cls.staff_user.id]).update(visibility=Visibility.PUBLIC)

    def test_user_list(self):
        self.get("api:user-list")
        self.response_404()

        with self.login(self.user):
            self.get("api:user-list")
            self.response_404()

        with self.login(self.staff_user):
            self.get("api:user-list")
            self.response_404()

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


@override_settings(SOCIALHOME_EXPORTS_PATH='/tmp/socialhome/exports')
class TestProfileViewSet(SocialhomeAPITestCase):
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

    def test_create_export__permissions(self):
        self.post("api:profile-create-export")
        self.response_403()

        with self.login(self.user):
            self.post("api:profile-create-export")
            self.response_200()
        self.assertEqual(self.last_response.data.get('status'), 'Data export job queued.')

    def test_profile_list(self):
        self.get("api:profile-list")
        self.response_404()

        with self.login(self.user):
            self.get("api:profile-list")
            self.response_404()

        with self.login(self.staff_user):
            self.get("api:profile-list")
            self.response_404()

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
        self.assertEqual(response.status_code, 403)
        response = self.client.patch(
            reverse("api:profile-detail", kwargs={"pk": self.self_profile.id}), {"name": "foo"}
        )
        self.assertEqual(response.status_code, 403)
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
        for field in ("id", "uuid", "fid", "handle", "image_url_large", "image_url_medium", "image_url_small",
                      "is_local", "url", "home_url"):
            response = self.client.patch(reverse("api:profile-detail", kwargs={"pk": self.profile.id}), {field: "82"})
            self.assertEqual(response.data.get(field), getattr(self.profile, field))
        for field in ("name", "location", "nsfw", "visibility"):
            if field == "nsfw":
                value = not self.profile.nsfw
            elif field == "visibility":
                value = "public" if self.profile.visibility != Visibility.PUBLIC else "limited"
            else:
                value = "82"
            response = self.client.patch(
                reverse("api:profile-detail", kwargs={"pk": self.profile.id}),
                {field: value}
            )
            self.assertEqual(
                response.data.get(field), value
            )

    def test_retrieve_export(self):
        create_user_export(self.user.id)
        self.get('api:profile-retrieve-export')
        self.response_403()

        with self.login(self.user):
            self.get('api:profile-retrieve-export')
        self.response_200()

    def test_user_add_follower(self):
        # Not authenticated
        response = self.client.post(reverse("api:profile-add-follower", kwargs={"pk": self.profile.id}), {
            "guid": self.profile.uuid,
        })
        self.assertEqual(response.status_code, 403)
        # Normal user authenticated
        self.client.login(username=self.user.username, password="password")
        response = self.client.post(reverse("api:profile-add-follower", kwargs={"pk": self.staff_profile.id}), {
            "guid": self.profile.uuid,
        })
        self.assertEqual(response.status_code, 404)
        response = self.client.post(reverse("api:profile-add-follower", kwargs={"pk": self.profile.id}), {
            "guid": self.site_profile.uuid,
        })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["status"], "Follower added.")
        # Staff user authenticated
        self.client.login(username=self.staff_user.username, password="password")
        response = self.client.post(reverse("api:profile-add-follower", kwargs={"pk": self.profile.id}), {
            "guid": self.staff_profile.uuid,
        })
        self.assertEqual(response.status_code, 403)
        response = self.client.post(reverse("api:profile-add-follower", kwargs={"pk": self.staff_profile.id}), {
            "guid": self.profile.uuid,
        })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["status"], "Follower added.")

    def test_user_remove_follower(self):
        # Not authenticated
        response = self.client.post(reverse("api:profile-remove-follower", kwargs={"pk": self.profile.id}), {
            "guid": self.profile.uuid,
        })
        self.assertEqual(response.status_code, 403)
        # Normal user authenticated
        self.client.login(username=self.user.username, password="password")
        response = self.client.post(reverse("api:profile-remove-follower", kwargs={"pk": self.staff_profile.id}), {
            "guid": self.profile.uuid,
        })
        self.assertEqual(response.status_code, 404)
        response = self.client.post(reverse("api:profile-remove-follower", kwargs={"pk": self.profile.id}), {
            "guid": self.staff_profile.uuid,
        })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["status"], "Follower removed.")
        # Staff user authenticated
        self.client.login(username=self.staff_user.username, password="password")
        response = self.client.post(reverse("api:profile-remove-follower", kwargs={"pk": self.profile.id}), {
            "guid": self.staff_profile.uuid,
        })
        self.assertEqual(response.status_code, 403)
        response = self.client.post(reverse("api:profile-remove-follower", kwargs={"pk": self.staff_profile.id}), {
            "guid": self.profile.uuid,
        })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["status"], "Follower removed.")

    def test_user_following__false_when_not_logged_in(self):
        self.get("api:profile-detail", pk=self.profile.id)
        self.assertEqual(self.last_response.data['user_following'], False)

    def test_user_following__false_when_not_following(self):
        with self.login(self.staff_user):
            self.get("api:profile-detail", pk=self.profile.id)
        self.assertEqual(self.last_response.data['user_following'], False)

    def test_user_following__true_when_following(self):
        self.staff_user.profile.following.add(self.profile)
        with self.login(self.staff_user):
            self.get("api:profile-detail", pk=self.profile.id)
        self.assertEqual(self.last_response.data['user_following'], True)
