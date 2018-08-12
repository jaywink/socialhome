from federation.entities import base

from socialhome.federate.utils import get_profile, make_federable_profile
from socialhome.tests.utils import SocialhomeTestCase
from socialhome.users.tests.factories import UserFactory


class TestGetProfile(SocialhomeTestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.user = UserFactory()
        cls.profile = cls.user.profile

    def test_profile_returned(self):
        returned = get_profile(fid=self.profile.fid)
        maked = make_federable_profile(self.profile)
        self.assertEqual(returned.id, maked.id)
        self.assertTrue(isinstance(returned, base.Profile))
