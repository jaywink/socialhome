from django.urls import reverse

from socialhome.federate.utils.generic import get_diaspora_profile_by_handle
from socialhome.tests.utils import SocialhomeTestCase
from socialhome.users.tests.factories import UserFactory


class TestGetDiasporaProfileIDByHandle(SocialhomeTestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.user = UserFactory()
        cls.profile = cls.user.profile

    def test_id_returned(self):
        profile_path = reverse("users:detail", kwargs={"username": self.user.username})
        self.assertEqual(
            get_diaspora_profile_by_handle(self.profile.handle),
            {
                "id": "diaspora://%s/profile/%s" % (self.profile.handle, self.profile.guid),
                "profile_path": profile_path,
                "atom_path": profile_path,
            }
        )
