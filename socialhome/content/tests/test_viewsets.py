from socialhome.content.models import Content
from socialhome.content.tests.factories import PublicContentFactory, TagFactory
from socialhome.enums import Visibility
from socialhome.tests.utils import SocialhomeAPITestCase
from socialhome.users.tests.factories import UserFactory, AdminUserFactory, ProfileFactory


class TestContentViewSet(SocialhomeAPITestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.user = UserFactory()
        cls.staff_user = AdminUserFactory()
        cls.create_content_set()
        cls.other_profile = ProfileFactory()
        cls.reply = PublicContentFactory(parent=cls.public_content)
        cls.share = PublicContentFactory(share_of=cls.public_content)
        cls.share_reply = PublicContentFactory(parent=cls.share)

    def setUp(self):
        super().setUp()
        self.public_content.refresh_from_db()
        self.limited_content.refresh_from_db()
        self.site_content.refresh_from_db()
        self.self_content.refresh_from_db()

    def _check_result_ids(self, expected):
        ids = {result["id"] for result in self.last_response.data["results"]}
        self.assertEqual(ids, expected)

    def _detail_access_tests(self, url):
        self.get(url, pk=self.public_content.id)
        self.response_200()
        self.get(url, pk=self.limited_content.id)
        self.response_404()
        self.get(url, pk=self.site_content.id)
        self.response_404()
        self.get(url, pk=self.self_content.id)
        self.response_404()

        with self.login(self.user):
            self.get(url, pk=self.public_content.id)
            self.response_200()
            self.get(url, pk=self.limited_content.id)
            self.response_404()
            self.get(url, pk=self.site_content.id)
            self.response_200()
            self.get(url, pk=self.self_content.id)
            self.response_404()

        with self.login(self.staff_user):
            self.get(url, pk=self.public_content.id)
            self.response_200()
            self.get(url, pk=self.limited_content.id)
            self.response_200()
            self.get(url, pk=self.site_content.id)
            self.response_200()
            self.get(url, pk=self.self_content.id)
            self.response_200()

    def test_list_content(self):
        self.get("api:content-list")
        self.response_405()

        with self.login(self.user):
            self.get("api:content-list")
            self.response_405()

        with self.login(self.staff_user):
            self.get("api:content-list")
            self.response_405()

    def test_detail(self):
        self._detail_access_tests("api:content-detail")

    def test_update(self):
        self.patch("api:content-detail", data={"text": "Foobar"}, pk=self.public_content.id)
        self.response_403()
        self.patch("api:content-detail", data={"text": "Foobar"}, pk=self.limited_content.id)
        self.response_403()
        self.patch("api:content-detail", data={"text": "Foobar"}, pk=self.site_content.id)
        self.response_403()
        self.patch("api:content-detail", data={"text": "Foobar"}, pk=self.self_content.id)
        self.response_403()

        with self.login(self.user):
            self.patch("api:content-detail", data={"text": "Foobar"}, pk=self.public_content.id)
            self.response_403()
            self.patch("api:content-detail", data={"text": "Foobar"}, pk=self.limited_content.id)
            self.response_404()
            self.patch("api:content-detail", data={"text": "Foobar"}, pk=self.site_content.id)
            self.response_403()
            self.patch("api:content-detail", data={"text": "Foobar"}, pk=self.self_content.id)
            self.response_404()

        with self.login(self.staff_user):
            self.patch("api:content-detail", data={"text": "Foobar"}, pk=self.public_content.id)
            self.response_403()
            self.patch("api:content-detail", data={"text": "Foobar"}, pk=self.limited_content.id)
            self.response_403()
            self.patch("api:content-detail", data={"text": "Foobar"}, pk=self.site_content.id)
            self.response_403()
            self.patch("api:content-detail", data={"text": "Foobar"}, pk=self.self_content.id)
            self.response_403()

        # Make self.user own the content
        Content.objects.filter(id__in=[
            self.public_content.id, self.limited_content.id, self.site_content.id, self.self_content.id,
        ]).update(author_id=self.user.profile.id)
        with self.login(self.user):
            self.patch("api:content-detail", data={"text": "Foobar"}, pk=self.public_content.id)
            self.response_200()
            self.patch("api:content-detail", data={"text": "Foobar"}, pk=self.limited_content.id)
            self.response_200()
            self.patch("api:content-detail", data={"text": "Foobar"}, pk=self.site_content.id)
            self.response_200()
            self.patch("api:content-detail", data={"text": "Foobar"}, pk=self.self_content.id)
            self.response_200()

    def test_delete(self):
        self.delete("api:content-detail", pk=self.public_content.id)
        self.response_403()
        self.delete("api:content-detail", pk=self.limited_content.id)
        self.response_403()
        self.delete("api:content-detail", pk=self.site_content.id)
        self.response_403()
        self.delete("api:content-detail", pk=self.self_content.id)
        self.response_403()

        with self.login(self.user):
            self.delete("api:content-detail", pk=self.public_content.id)
            self.response_403()
            self.delete("api:content-detail", pk=self.limited_content.id)
            self.response_404()
            self.delete("api:content-detail", pk=self.site_content.id)
            self.response_403()
            self.delete("api:content-detail", pk=self.self_content.id)
            self.response_404()

        with self.login(self.staff_user):
            self.delete("api:content-detail", pk=self.public_content.id)
            self.response_403()
            self.delete("api:content-detail", pk=self.limited_content.id)
            self.response_403()
            self.delete("api:content-detail", pk=self.site_content.id)
            self.response_403()
            self.delete("api:content-detail", pk=self.self_content.id)
            self.response_403()

        # Make self.user own the content
        Content.objects.filter(id__in=[
            self.public_content.id, self.limited_content.id, self.site_content.id, self.self_content.id,
        ]).update(author_id=self.user.profile.id)
        with self.login(self.user):
            self.delete("api:content-detail", pk=self.public_content.id)
            self.assertEqual(self.last_response.status_code, 204)
            self.delete("api:content-detail", pk=self.limited_content.id)
            self.assertEqual(self.last_response.status_code, 204)
            self.delete("api:content-detail", pk=self.site_content.id)
            self.assertEqual(self.last_response.status_code, 204)
            self.delete("api:content-detail", pk=self.self_content.id)
            self.assertEqual(self.last_response.status_code, 204)

    def test_post(self):
        data = {
            "text": "Test", "pinned": False, "order": 1, "service_label": "", "visibility": Visibility.PUBLIC,
        }
        self.post("api:content-list", data=data)
        self.response_403()

        with self.login(self.user):
            data.update({"author": self.user.profile.id})
            self.post("api:content-list", data=data)
            self.response_201()

        with self.login(self.staff_user):
            data.update({"author": self.staff_user.profile.id})
            self.post("api:content-list", data=data)
            self.response_201()

    def test_post___limited(self):
        data = {
            "text": "Test", "pinned": False, "order": 1, "service_label": "", "visibility": Visibility.LIMITED,
            "author": self.user.profile.id,
        }
        with self.login(self.user):
            self.post("api:content-list", data=data)
            self.response_201()

    def test_post_creates_as_request_user(self):
        data = {
            "text": "Test", "pinned": False, "order": 1, "service_label": "", "visibility": Visibility.PUBLIC,
            "author": self.other_profile.id,
        }

        with self.login(self.user):
            self.post("api:content-list", data=data)
            content = Content.objects.get(id=self.last_response.data["id"])
            self.assertEqual(content.author_id, self.user.profile.id)

        with self.login(self.staff_user):
            self.post("api:content-list", data=data)
            content = Content.objects.get(id=self.last_response.data["id"])
            self.assertEqual(content.author_id, self.staff_user.profile.id)

    def test_replies_access(self):
        self._detail_access_tests("api:content-replies")

    def test_replies_results(self):
        self.get("api:content-replies", pk=self.public_content.id)
        self.assertEqual(len(self.last_response.data), 2)
        self.assertEqual(self.last_response.data[0].get("id"), self.reply.id)
        self.assertEqual(self.last_response.data[1].get("id"), self.share_reply.id)

    def test_share(self):
        self.post("api:content-share", pk=self.public_content.id)
        self.response_403()
        self.post("api:content-share", pk=self.site_content.id)
        self.response_403()
        self.post("api:content-share", pk=self.limited_content.id)
        self.response_403()
        self.post("api:content-share", pk=self.self_content.id)
        self.response_403()
        self.delete("api:content-share", pk=self.public_content.id)
        self.response_403()
        self.delete("api:content-share", pk=self.site_content.id)
        self.response_403()
        self.delete("api:content-share", pk=self.limited_content.id)
        self.response_403()
        self.delete("api:content-share", pk=self.self_content.id)
        self.response_403()

        with self.login(self.user):
            self.post("api:content-share", pk=self.public_content.id)
            self.response_201()
            self.post("api:content-share", pk=self.site_content.id)
            self.response_201()
            self.post("api:content-share", pk=self.limited_content.id)
            self.response_404()
            self.post("api:content-share", pk=self.self_content.id)
            self.response_404()
            self.delete("api:content-share", pk=self.public_content.id)
            self.assertEqual(self.last_response.status_code, 204)
            self.delete("api:content-share", pk=self.site_content.id)
            self.assertEqual(self.last_response.status_code, 204)
            self.delete("api:content-share", pk=self.limited_content.id)
            self.response_404()
            self.delete("api:content-share", pk=self.self_content.id)
            self.response_404()

        with self.login(self.staff_user):
            self.post("api:content-share", pk=self.public_content.id)
            self.response_201()
            self.post("api:content-share", pk=self.site_content.id)
            self.response_201()
            self.post("api:content-share", pk=self.limited_content.id)
            self.response_400()
            self.post("api:content-share", pk=self.self_content.id)
            self.response_400()
            self.delete("api:content-share", pk=self.public_content.id)
            self.assertEqual(self.last_response.status_code, 204)
            self.delete("api:content-share", pk=self.site_content.id)
            self.assertEqual(self.last_response.status_code, 204)
            self.delete("api:content-share", pk=self.limited_content.id)
            self.response_400()
            self.delete("api:content-share", pk=self.self_content.id)
            self.response_400()

    def test_shares_access(self):
        self._detail_access_tests("api:content-shares")

    def test_shares_results(self):
        self.get("api:content-shares", pk=self.public_content.id)
        self.assertEqual(len(self.last_response.data), 1)
        self.assertEqual(self.last_response.data[0].get("id"), self.share.id)


class TestTagViewset(SocialhomeAPITestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.user = UserFactory()
        cls.profile = cls.user.profile
        cls.tag = TagFactory()
        cls.tag2 = TagFactory()

    def test_create(self):
        with self.login(self.user):
            self.post("api:tag-list", data={"name": "creatingatag"})
        self.response_405()

    def test_delete(self):
        with self.login(self.user):
            self.delete("api:tag-detail", uuid=self.tag.uuid)
        self.response_405()

    def test_detail(self):
        self.get("api:tag-detail", uuid=self.tag.uuid)
        self.response_200()
        self.assertEqual(self.last_response.data["name"], self.tag.name)
        self.assertEqual(self.last_response.data["uuid"], str(self.tag.uuid))

    def test_follow(self):
        self.post("api:tag-follow", uuid=self.tag.uuid)
        self.response_401()

        with self.login(self.user):
            self.post("api:tag-follow", uuid=self.tag.uuid)
        self.response_200()
        self.assertEqual(self.profile.followed_tags.count(), 1)
        self.assertEqual(self.profile.followed_tags.first(), self.tag)

    def test_list(self):
        self.get("api:tag-list")
        self.response_200()
        self.assertEqual(len(self.last_response.data["results"]), 2)

    def test_unfollow(self):
        self.profile.followed_tags.add(self.tag)

        self.post("api:tag-unfollow", uuid=self.tag.uuid)
        self.response_401()

        with self.login(self.user):
            self.post("api:tag-unfollow", uuid=self.tag.uuid)
        self.response_200()
        self.assertEqual(self.profile.followed_tags.count(), 0)

        # Second unfollow fails silently
        with self.login(self.user):
            self.post("api:tag-unfollow", uuid=self.tag.uuid)
        self.response_200()

    def test_update(self):
        with self.login(self.user):
            self.patch("api:tag-detail", uuid=self.tag.uuid, data={"name": "newnameyo"})
        self.response_405()
