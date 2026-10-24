from unittest.mock import patch

from socialhome.content.tests.factories import LocalContentFactory, PublicContentFactory
from socialhome.enums import Visibility
from socialhome.tests.utils import SocialhomeAPITestCase
from socialhome.users.tests.factories import UserFactory, PublicProfileFactory


class TestSearchViewSet(SocialhomeAPITestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.user = UserFactory()
        cls.local_content = LocalContentFactory(
            visibility=Visibility.PUBLIC,
        )
        cls.remote_content = PublicContentFactory(author=PublicProfileFactory())

    def test_search(self):
        self.get("api-search")
        self.response_200()

        with self.login(self.user):
            self.get("api-search")
            self.response_200()

    def test_search_returns_content(self):
        with self.login(self.user):
            results = self.get("api-search", data={"name__startswith": self.local_content.fid})
            self.assertEqual(results.json()["results"], [{"id": self.local_content.id}])
            results = self.get("api-search", data={"name__startswith": self.remote_content.fid})
            self.assertEqual(results.json()["results"], [{"id": self.remote_content.id}])

    @patch("socialhome.search.utils.retrieve_remote_content", return_value=None)
    @patch("socialhome.search.utils.retrieve_remote_profile", return_value=None)
    def test_search_fetches_remote_objects_for_authenticated_users(self, mock_retrieve_profile, mock_retrieve_content):
        url = "https://this.wont.exist.tld/foobar"
        with self.login(self.user):
            self.get("api-search", data={"name__startswith": url})
        mock_retrieve_profile.assert_called_once_with(url)
        mock_retrieve_content.assert_called_once_with(url)

    @patch("socialhome.search.utils.retrieve_remote_content", return_value=None)
    @patch("socialhome.search.utils.retrieve_remote_profile", return_value=None)
    def test_search_does_not_fetch_remote_objects_for_unauthenticated_users(self, mock_retrieve_profile, mock_retrieve_content):
        url = "https://this.wont.exist.tld/foobar"
        self.get("api-search", data={"name__startswith": url})
        mock_retrieve_profile.assert_not_called()
        mock_retrieve_content.assert_not_called()
