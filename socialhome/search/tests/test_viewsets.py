from socialhome.tests.utils import SocialhomeAPITestCase
from socialhome.users.tests.factories import UserFactory


class TestSearchViewSet(SocialhomeAPITestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.user = UserFactory()

    def test_search_requires_auth(self):
        self.get("api-search")
        self.response_403()

        with self.login(self.user):
            self.get("api-search")
            self.response_200()
