from django.contrib.auth.models import AnonymousUser

from socialhome.content.models import Content
from socialhome.content.tests.factories import ContentFactory
from socialhome.enums import Visibility
from socialhome.tests.utils import SocialhomeTestCase
from socialhome.users.models import Profile
from socialhome.users.tests.factories import UserFactory


class TestContentQuerySet(SocialhomeTestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.public_content = ContentFactory(pinned=True)
        cls.public_tags_content = ContentFactory(text="#foobar")
        cls.site_content = ContentFactory(visibility=Visibility.SITE, pinned=True)
        cls.site_tags_content = ContentFactory(visibility=Visibility.SITE, text="#foobar")
        cls.self_user = UserFactory()
        cls.self_content = ContentFactory(visibility=Visibility.SELF, author=cls.self_user.profile, pinned=True)
        cls.self_tags_content = ContentFactory(visibility=Visibility.SELF, author=cls.self_user.profile, text="#foobar")
        cls.other_user = UserFactory()
        cls.anonymous_user = AnonymousUser()
        cls.other_user.profile.following.add(cls.public_content.author, cls.self_user.profile)

    def test_visible_for_user(self):
        contents = set(Content.objects.visible_for_user(self.anonymous_user))
        self.assertEqual(contents, {self.public_content, self.public_tags_content})
        contents = set(Content.objects.visible_for_user(self.other_user))
        self.assertEqual(contents, {self.public_content, self.public_tags_content, self.site_content,
                                    self.site_tags_content})
        contents = set(Content.objects.visible_for_user(self.self_content.author.user))
        self.assertEqual(contents, {self.public_content, self.public_tags_content, self.site_content,
                                    self.site_tags_content, self.self_content, self.self_tags_content})

    def test_public(self):
        contents = set(Content.objects.public())
        self.assertEqual(contents, {self.public_content, self.public_tags_content})

    def test_tags(self):
        contents = set(Content.objects.tags("foobar", self.anonymous_user))
        self.assertEqual(contents, {self.public_tags_content})
        contents = set(Content.objects.tags("foobar", self.other_user))
        self.assertEqual(contents, {self.public_tags_content, self.site_tags_content})
        contents = set(Content.objects.tags("foobar", self.self_content.author.user))
        self.assertEqual(contents, {self.public_tags_content, self.site_tags_content, self.self_tags_content})

    def test_followed(self):
        contents = set(Content.objects.followed(self.other_user))
        self.assertEqual(contents, {self.public_content})
        contents = set(Content.objects.followed(self.self_user))
        self.assertEqual(contents, set())

    def _set_profiles_public(self):
        Profile.objects.filter(id=self.public_content.author_id).update(visibility=Visibility.PUBLIC)
        Profile.objects.filter(id=self.self_content.author_id).update(visibility=Visibility.PUBLIC)
        Profile.objects.filter(id=self.site_content.author_id).update(visibility=Visibility.PUBLIC)

    def test_profile(self):
        contents = set(Content.objects.profile(self.public_content.author.guid, self.anonymous_user))
        self.assertEqual(contents, set())
        contents = set(Content.objects.profile(self.site_content.author.guid, self.anonymous_user))
        self.assertEqual(contents, set())
        contents = set(Content.objects.profile(self.self_content.author.guid, self.anonymous_user))
        self.assertEqual(contents, set())
        contents = set(Content.objects.profile(self.public_content.author.guid, self.other_user))
        self.assertEqual(contents, set())
        contents = set(Content.objects.profile(self.site_content.author.guid, self.other_user))
        self.assertEqual(contents, set())
        contents = set(Content.objects.profile(self.self_content.author.guid, self.other_user))
        self.assertEqual(contents, set())
        contents = set(Content.objects.profile(self.public_content.author.guid, self.self_user))
        self.assertEqual(contents, set())
        contents = set(Content.objects.profile(self.site_content.author.guid, self.self_user))
        self.assertEqual(contents, set())
        contents = set(Content.objects.profile(self.self_content.author.guid, self.self_user))
        self.assertEqual(contents, {self.self_content, self.self_tags_content})

        self._set_profiles_public()
        contents = set(Content.objects.profile(self.public_content.author.guid, self.anonymous_user))
        self.assertEqual(contents, {self.public_content})
        contents = set(Content.objects.profile(self.site_content.author.guid, self.anonymous_user))
        self.assertEqual(contents, set())
        contents = set(Content.objects.profile(self.self_content.author.guid, self.anonymous_user))
        self.assertEqual(contents, set())
        contents = set(Content.objects.profile(self.public_content.author.guid, self.other_user))
        self.assertEqual(contents, {self.public_content})
        contents = set(Content.objects.profile(self.site_content.author.guid, self.other_user))
        self.assertEqual(contents, {self.site_content})
        contents = set(Content.objects.profile(self.self_content.author.guid, self.other_user))
        self.assertEqual(contents, set())
        contents = set(Content.objects.profile(self.public_content.author.guid, self.self_user))
        self.assertEqual(contents, {self.public_content})
        contents = set(Content.objects.profile(self.site_content.author.guid, self.self_user))
        self.assertEqual(contents, {self.site_content})
        contents = set(Content.objects.profile(self.self_content.author.guid, self.self_user))
        self.assertEqual(contents, {self.self_content, self.self_tags_content})

    def test_profile_pinned(self):
        contents = set(Content.objects.profile_pinned(self.public_content.author.guid, self.anonymous_user))
        self.assertEqual(contents, set())
        contents = set(Content.objects.profile_pinned(self.site_content.author.guid, self.anonymous_user))
        self.assertEqual(contents, set())
        contents = set(Content.objects.profile_pinned(self.self_content.author.guid, self.anonymous_user))
        self.assertEqual(contents, set())
        contents = set(Content.objects.profile_pinned(self.public_content.author.guid, self.other_user))
        self.assertEqual(contents, set())
        contents = set(Content.objects.profile_pinned(self.site_content.author.guid, self.other_user))
        self.assertEqual(contents, set())
        contents = set(Content.objects.profile_pinned(self.self_content.author.guid, self.other_user))
        self.assertEqual(contents, set())
        contents = set(Content.objects.profile_pinned(self.public_content.author.guid, self.self_user))
        self.assertEqual(contents, set())
        contents = set(Content.objects.profile_pinned(self.site_content.author.guid, self.self_user))
        self.assertEqual(contents, set())
        contents = set(Content.objects.profile_pinned(self.self_content.author.guid, self.self_user))
        self.assertEqual(contents, {self.self_content})

        self._set_profiles_public()
        contents = set(Content.objects.profile_pinned(self.public_content.author.guid, self.anonymous_user))
        self.assertEqual(contents, {self.public_content})
        contents = set(Content.objects.profile_pinned(self.site_content.author.guid, self.anonymous_user))
        self.assertEqual(contents, set())
        contents = set(Content.objects.profile_pinned(self.self_content.author.guid, self.anonymous_user))
        self.assertEqual(contents, set())
        contents = set(Content.objects.profile_pinned(self.public_content.author.guid, self.other_user))
        self.assertEqual(contents, {self.public_content})
        contents = set(Content.objects.profile_pinned(self.site_content.author.guid, self.other_user))
        self.assertEqual(contents, {self.site_content})
        contents = set(Content.objects.profile_pinned(self.self_content.author.guid, self.other_user))
        self.assertEqual(contents, set())
        contents = set(Content.objects.profile_pinned(self.public_content.author.guid, self.self_user))
        self.assertEqual(contents, {self.public_content})
        contents = set(Content.objects.profile_pinned(self.site_content.author.guid, self.self_user))
        self.assertEqual(contents, {self.site_content})
        contents = set(Content.objects.profile_pinned(self.self_content.author.guid, self.self_user))
        self.assertEqual(contents, {self.self_content})
