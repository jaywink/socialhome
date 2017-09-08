from unittest.mock import Mock

from django.contrib.auth.models import AnonymousUser

from socialhome.content.serializers import ContentSerializer
from socialhome.content.tests.factories import PublicContentFactory
from socialhome.tests.utils import SocialhomeTestCase


class ContentSerializerTestCase(SocialhomeTestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.create_local_and_remote_user()
        cls.content = PublicContentFactory(author=cls.remote_profile)
        cls.user_content = PublicContentFactory(author=cls.profile)

    def setUp(self):
        super().setUp()
        try:
            del self.profile.following_ids
        except AttributeError:
            pass

    def test_serializes_author(self):
        serializer = ContentSerializer(self.content)
        data = serializer.data["author"]
        self.assertEqual(data["guid"], self.remote_profile.guid)
        self.assertEqual(data["handle"], self.remote_profile.handle)
        self.assertEqual(data["home_url"], self.remote_profile.home_url)
        self.assertEqual(data["id"], self.remote_profile.id)
        self.assertEqual(data["image_url_small"], self.remote_profile.image_url_small)
        self.assertEqual(data["is_local"], self.remote_profile.is_local)
        self.assertEqual(data["name"], self.remote_profile.name)
        self.assertEqual(data["url"], self.remote_profile.url)

    def test_user_following_author_false_if_no_request(self):
        serializer = ContentSerializer()
        self.assertFalse(serializer.get_user_following_author(None))

    def test_user_following_author_false_if_not_authenticated(self):
        serializer = ContentSerializer(context={"request": Mock(user=AnonymousUser())})
        self.assertFalse(serializer.get_user_following_author(None))

    def test_user_following_author_false_if_not_following(self):
        serializer = ContentSerializer(context={"request": Mock(user=self.user)})
        self.assertFalse(serializer.get_user_following_author(self.content))

    def test_user_following_author_true_if_following(self):
        self.profile.following.add(self.remote_profile)
        serializer = ContentSerializer(context={"request": Mock(user=self.user)})
        self.assertTrue(serializer.get_user_following_author(self.content))

    def test_user_is_author_false_if_no_request(self):
        serializer = ContentSerializer()
        self.assertFalse(serializer.get_user_is_author(None))

    def test_user_is_author_false_if_not_authenticated(self):
        serializer = ContentSerializer(context={"request": Mock(user=AnonymousUser())})
        self.assertFalse(serializer.get_user_is_author(None))

    def test_user_is_author_false_if_not_author(self):
        serializer = ContentSerializer(context={"request": Mock(user=self.user)})
        self.assertFalse(serializer.get_user_is_author(self.content))

    def test_user_is_author_true_if_author(self):
        serializer = ContentSerializer(context={"request": Mock(user=self.user)})
        self.assertTrue(serializer.get_user_is_author(self.user_content))

    def test_user_has_shared_false_if_no_request(self):
        serializer = ContentSerializer()
        self.assertFalse(serializer.get_user_has_shared(None))

    def test_user_has_shared_false_if_anonymous_user(self):
        serializer = ContentSerializer(context={"request": Mock(user=AnonymousUser())})
        self.assertFalse(serializer.get_user_has_shared(None))

    def test_user_has_shared_false_if_not_shared(self):
        serializer = ContentSerializer(context={"request": Mock(user=self.user)})
        self.assertFalse(serializer.get_user_has_shared(self.content))

    def test_user_has_shared_true_if_shared(self):
        self.content.share(self.profile)
        serializer = ContentSerializer(context={"request": Mock(user=self.user)})
        self.assertTrue(serializer.get_user_has_shared(self.content))
