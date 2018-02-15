from socialhome.federate.utils.generic import get_diaspora_profile_id_by_handle
from socialhome.tests.utils import SocialhomeTestCase
from socialhome.users.tests.factories import ProfileFactory


class TestGetDiasporaProfileIDByHandle(SocialhomeTestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.profile = ProfileFactory(handle="foobar@example.com", guid="5"*16)

    def test_id_returned(self):
        self.assertEqual(
            get_diaspora_profile_id_by_handle(self.profile.handle),
            "diaspora://foobar@example.com/profile/%s" % ("5"*16)
        )
