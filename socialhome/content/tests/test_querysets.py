from django.contrib.auth.models import AnonymousUser

from socialhome.content.models import Content, Tag
from socialhome.content.tests.factories import (
    PublicContentFactory, LimitedContentFactory, SelfContentFactory, SiteContentFactory)
from socialhome.enums import Visibility
from socialhome.tests.utils import SocialhomeTestCase
from socialhome.users.tests.factories import UserFactory


class TestContentQuerySet(SocialhomeTestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.public_content = PublicContentFactory(pinned=True)
        cls.public_tag_content = PublicContentFactory(text="#foobar")
        cls.limited_content = LimitedContentFactory()
        cls.tag = Tag.objects.get(name="foobar")
        cls.site_content = SiteContentFactory(pinned=True)
        cls.site_tag_content = SiteContentFactory(text="#foobar")
        cls.self_user = UserFactory()
        cls.self_content = SelfContentFactory(author=cls.self_user.profile, pinned=True)
        cls.self_tag_content = SelfContentFactory(author=cls.self_user.profile, text="#foobar")
        cls.other_user = UserFactory()
        cls.anonymous_user = AnonymousUser()
        cls.other_user.profile.following.add(cls.public_content.author, cls.self_user.profile)
        cls.public_reply = PublicContentFactory(parent=cls.public_content)
        cls.limited_reply = LimitedContentFactory(parent=cls.limited_content)
        cls.self_reply = SelfContentFactory(parent=cls.self_content)
        cls.site_reply = SiteContentFactory(parent=cls.site_content)

        # TODO refactor so that all share_of is not one of the other tested content above
        cls.public_share = PublicContentFactory(share_of=cls.public_content, author=cls.self_user.profile)
        cls.limited_share = LimitedContentFactory(share_of=cls.limited_content, author=cls.self_user.profile)
        cls.self_share = SelfContentFactory(share_of=cls.self_content, author=cls.self_user.profile)
        cls.site_share = SiteContentFactory(share_of=cls.site_content, author=cls.self_user.profile)
        cls.public_share_reply = PublicContentFactory(parent=cls.public_share)
        cls.share_limited_reply = LimitedContentFactory(parent=cls.limited_share)
        cls.share_self_reply = SelfContentFactory(parent=cls.self_share)
        cls.share_site_reply = SiteContentFactory(parent=cls.site_share)

    def setUp(self):
        super().setUp()
        self.public_content.author.refresh_from_db()
        self.self_content.author.refresh_from_db()
        self.site_content.author.refresh_from_db()

    def test_visible_for_user(self):
        contents = set(Content.objects.visible_for_user(self.anonymous_user))
        self.assertEqual(contents, {self.public_content, self.public_tag_content, self.public_reply,
                                    self.public_share, self.public_share_reply})
        contents = set(Content.objects.visible_for_user(self.other_user))
        self.assertEqual(contents, {self.public_content, self.public_tag_content, self.site_content,
                                    self.site_tag_content, self.public_reply, self.site_reply, self.public_share,
                                    self.site_share, self.public_share_reply, self.share_site_reply})
        contents = set(Content.objects.visible_for_user(self.self_content.author.user))
        self.assertEqual(contents, {self.public_content, self.public_tag_content, self.site_content,
                                    self.site_tag_content, self.self_content, self.self_tag_content,
                                    self.public_reply, self.site_reply, self.public_share, self.limited_share,
                                    self.site_share, self.self_share, self.public_share_reply, self.share_site_reply})

    def test_public(self):
        contents = set(Content.objects.public())
        self.assertEqual(contents, {self.public_content, self.public_tag_content})

    def test_tag_by_name(self):
        contents = set(Content.objects.tag_by_name("foobar", self.anonymous_user))
        self.assertEqual(contents, {self.public_tag_content})
        contents = set(Content.objects.tag_by_name("foobar", self.other_user))
        self.assertEqual(contents, {self.public_tag_content, self.site_tag_content})
        contents = set(Content.objects.tag_by_name("foobar", self.self_content.author.user))
        self.assertEqual(contents, {self.public_tag_content, self.site_tag_content, self.self_tag_content})

    def test_tag(self):
        contents = set(Content.objects.tag(self.tag, self.anonymous_user))
        self.assertEqual(contents, {self.public_tag_content})
        contents = set(Content.objects.tag(self.tag, self.other_user))
        self.assertEqual(contents, {self.public_tag_content, self.site_tag_content})
        contents = set(Content.objects.tag(self.tag, self.self_content.author.user))
        self.assertEqual(contents, {self.public_tag_content, self.site_tag_content, self.self_tag_content})

    def test_followed(self):
        contents = set(Content.objects.followed(self.other_user))
        # public_content comes directly by following the author, site_content via share of a follower
        self.assertEqual(contents, {self.public_content, self.site_content})
        contents = set(Content.objects.followed(self.self_user))
        self.assertEqual(contents, set())

    def _set_profiles_public(self):
        for profile in (self.public_content.author, self.site_content.author, self.self_content.author):
            profile.visibility = Visibility.PUBLIC
            profile.save(update_fields=["visibility"])

    def test_profile_by_attr(self):
        contents = set(Content.objects.profile_by_attr("guid", self.public_content.author.guid, self.anonymous_user))
        self.assertEqual(contents, set())
        contents = set(Content.objects.profile_by_attr("guid", self.site_content.author.guid, self.anonymous_user))
        self.assertEqual(contents, set())
        contents = set(Content.objects.profile_by_attr("guid", self.self_content.author.guid, self.anonymous_user))
        self.assertEqual(contents, set())
        contents = set(Content.objects.profile_by_attr("guid", self.public_content.author.guid, self.other_user))
        self.assertEqual(contents, set())
        contents = set(Content.objects.profile_by_attr("guid", self.site_content.author.guid, self.other_user))
        self.assertEqual(contents, set())
        contents = set(Content.objects.profile_by_attr("guid", self.self_content.author.guid, self.other_user))
        self.assertEqual(contents, set())
        contents = set(Content.objects.profile_by_attr("guid", self.public_content.author.guid, self.self_user))
        self.assertEqual(contents, set())
        contents = set(Content.objects.profile_by_attr("guid", self.site_content.author.guid, self.self_user))
        self.assertEqual(contents, set())
        contents = set(Content.objects.profile_by_attr("guid", self.self_content.author.guid, self.self_user))
        self.assertEqual(contents, {self.self_content, self.self_tag_content, self.public_content, self.site_content})

        self._set_profiles_public()
        contents = set(Content.objects.profile_by_attr("guid", self.public_content.author.guid, self.anonymous_user))
        self.assertEqual(contents, {self.public_content})
        contents = set(Content.objects.profile_by_attr("guid", self.site_content.author.guid, self.anonymous_user))
        self.assertEqual(contents, set())
        contents = set(Content.objects.profile_by_attr("guid", self.self_content.author.guid, self.anonymous_user))
        self.assertEqual(contents, {self.public_content})
        contents = set(Content.objects.profile_by_attr("guid", self.public_content.author.guid, self.other_user))
        self.assertEqual(contents, {self.public_content})
        contents = set(Content.objects.profile_by_attr("guid", self.site_content.author.guid, self.other_user))
        self.assertEqual(contents, {self.site_content})
        contents = set(Content.objects.profile_by_attr("guid", self.self_content.author.guid, self.other_user))
        self.assertEqual(contents, {self.public_content, self.site_content})
        contents = set(Content.objects.profile_by_attr("guid", self.public_content.author.guid, self.self_user))
        self.assertEqual(contents, {self.public_content})
        contents = set(Content.objects.profile_by_attr("guid", self.site_content.author.guid, self.self_user))
        self.assertEqual(contents, {self.site_content})
        contents = set(Content.objects.profile_by_attr("guid", self.self_content.author.guid, self.self_user))
        self.assertEqual(contents, {self.self_content, self.self_tag_content, self.public_content, self.site_content})

    def test_profile(self):
        contents = set(Content.objects.profile(self.public_content.author, self.anonymous_user))
        self.assertEqual(contents, set())
        contents = set(Content.objects.profile(self.site_content.author, self.anonymous_user))
        self.assertEqual(contents, set())
        contents = set(Content.objects.profile(self.self_content.author, self.anonymous_user))
        self.assertEqual(contents, set())
        contents = set(Content.objects.profile(self.public_content.author, self.other_user))
        self.assertEqual(contents, set())
        contents = set(Content.objects.profile(self.site_content.author, self.other_user))
        self.assertEqual(contents, set())
        contents = set(Content.objects.profile(self.self_content.author, self.other_user))
        self.assertEqual(contents, set())
        contents = set(Content.objects.profile(self.public_content.author, self.self_user))
        self.assertEqual(contents, set())
        contents = set(Content.objects.profile(self.site_content.author, self.self_user))
        self.assertEqual(contents, set())
        contents = set(Content.objects.profile(self.self_content.author, self.self_user))
        self.assertEqual(contents, {self.self_content, self.self_tag_content, self.public_content, self.site_content})

        self._set_profiles_public()
        contents = set(Content.objects.profile(self.public_content.author, self.anonymous_user))
        self.assertEqual(contents, {self.public_content})
        contents = set(Content.objects.profile(self.site_content.author, self.anonymous_user))
        self.assertEqual(contents, set())
        contents = set(Content.objects.profile(self.self_content.author, self.anonymous_user))
        self.assertEqual(contents, {self.public_content})
        contents = set(Content.objects.profile(self.public_content.author, self.other_user))
        self.assertEqual(contents, {self.public_content})
        contents = set(Content.objects.profile(self.site_content.author, self.other_user))
        self.assertEqual(contents, {self.site_content})
        contents = set(Content.objects.profile(self.self_content.author, self.other_user))
        self.assertEqual(contents, {self.public_content, self.site_content})
        contents = set(Content.objects.profile(self.public_content.author, self.self_user))
        self.assertEqual(contents, {self.public_content})
        contents = set(Content.objects.profile(self.site_content.author, self.self_user))
        self.assertEqual(contents, {self.site_content})
        contents = set(Content.objects.profile(self.self_content.author, self.self_user))
        self.assertEqual(contents, {self.self_content, self.self_tag_content, self.public_content, self.site_content})

    def test_profile_pinned(self):
        contents = set(Content.objects.profile_pinned(self.public_content.author, self.anonymous_user))
        self.assertEqual(contents, set())
        contents = set(Content.objects.profile_pinned(self.site_content.author, self.anonymous_user))
        self.assertEqual(contents, set())
        contents = set(Content.objects.profile_pinned(self.self_content.author, self.anonymous_user))
        self.assertEqual(contents, set())
        contents = set(Content.objects.profile_pinned(self.public_content.author, self.other_user))
        self.assertEqual(contents, set())
        contents = set(Content.objects.profile_pinned(self.site_content.author, self.other_user))
        self.assertEqual(contents, set())
        contents = set(Content.objects.profile_pinned(self.self_content.author, self.other_user))
        self.assertEqual(contents, set())
        contents = set(Content.objects.profile_pinned(self.public_content.author, self.self_user))
        self.assertEqual(contents, set())
        contents = set(Content.objects.profile_pinned(self.site_content.author, self.self_user))
        self.assertEqual(contents, set())
        contents = set(Content.objects.profile_pinned(self.self_content.author, self.self_user))
        self.assertEqual(contents, {self.self_content, self.public_content, self.site_content})

        self._set_profiles_public()
        contents = set(Content.objects.profile_pinned(self.public_content.author, self.anonymous_user))
        self.assertEqual(contents, {self.public_content})
        contents = set(Content.objects.profile_pinned(self.site_content.author, self.anonymous_user))
        self.assertEqual(contents, set())
        contents = set(Content.objects.profile_pinned(self.self_content.author, self.anonymous_user))
        self.assertEqual(contents, {self.public_content})
        contents = set(Content.objects.profile_pinned(self.public_content.author, self.other_user))
        self.assertEqual(contents, {self.public_content})
        contents = set(Content.objects.profile_pinned(self.site_content.author, self.other_user))
        self.assertEqual(contents, {self.site_content})
        contents = set(Content.objects.profile_pinned(self.self_content.author, self.other_user))
        self.assertEqual(contents, {self.public_content, self.site_content})
        contents = set(Content.objects.profile_pinned(self.public_content.author, self.self_user))
        self.assertEqual(contents, {self.public_content})
        contents = set(Content.objects.profile_pinned(self.site_content.author, self.self_user))
        self.assertEqual(contents, {self.site_content})
        contents = set(Content.objects.profile_pinned(self.self_content.author, self.self_user))
        self.assertEqual(contents, {self.self_content, self.public_content, self.site_content})

    def test_profile_pinned_by_attr(self):
        contents = set(
            Content.objects.profile_pinned_by_attr("guid", self.public_content.author.guid, self.anonymous_user),
        )
        self.assertEqual(contents, set())
        contents = set(
            Content.objects.profile_pinned_by_attr("guid", self.site_content.author.guid, self.anonymous_user),
        )
        self.assertEqual(contents, set())
        contents = set(
            Content.objects.profile_pinned_by_attr("guid", self.self_content.author.guid, self.anonymous_user),
        )
        self.assertEqual(contents, set())
        contents = set(Content.objects.profile_pinned_by_attr("guid", self.public_content.author.guid, self.other_user))
        self.assertEqual(contents, set())
        contents = set(Content.objects.profile_pinned_by_attr("guid", self.site_content.author.guid, self.other_user))
        self.assertEqual(contents, set())
        contents = set(Content.objects.profile_pinned_by_attr("guid", self.self_content.author.guid, self.other_user))
        self.assertEqual(contents, set())
        contents = set(Content.objects.profile_pinned_by_attr("guid", self.public_content.author.guid, self.self_user))
        self.assertEqual(contents, set())
        contents = set(Content.objects.profile_pinned_by_attr("guid", self.site_content.author.guid, self.self_user))
        self.assertEqual(contents, set())
        contents = set(Content.objects.profile_pinned_by_attr("guid", self.self_content.author.guid, self.self_user))
        self.assertEqual(contents, {self.self_content, self.public_content, self.site_content})

        self._set_profiles_public()
        contents = set(
            Content.objects.profile_pinned_by_attr("guid", self.public_content.author.guid, self.anonymous_user),
        )
        self.assertEqual(contents, {self.public_content})
        contents = set(
            Content.objects.profile_pinned_by_attr("guid", self.site_content.author.guid, self.anonymous_user),
        )
        self.assertEqual(contents, set())
        contents = set(
            Content.objects.profile_pinned_by_attr("guid", self.self_content.author.guid, self.anonymous_user),
        )
        self.assertEqual(contents, {self.public_content})
        contents = set(Content.objects.profile_pinned_by_attr("guid", self.public_content.author.guid, self.other_user))
        self.assertEqual(contents, {self.public_content})
        contents = set(Content.objects.profile_pinned_by_attr("guid", self.site_content.author.guid, self.other_user))
        self.assertEqual(contents, {self.site_content})
        contents = set(Content.objects.profile_pinned_by_attr("guid", self.self_content.author.guid, self.other_user))
        self.assertEqual(contents, {self.public_content, self.site_content})
        contents = set(Content.objects.profile_pinned_by_attr("guid", self.public_content.author.guid, self.self_user))
        self.assertEqual(contents, {self.public_content})
        contents = set(Content.objects.profile_pinned_by_attr("guid", self.site_content.author.guid, self.self_user))
        self.assertEqual(contents, {self.site_content})
        contents = set(Content.objects.profile_pinned_by_attr("guid", self.self_content.author.guid, self.self_user))
        self.assertEqual(contents, {self.self_content, self.public_content, self.site_content})

    def test_children(self):
        contents = set(Content.objects.children(self.public_content.id, self.anonymous_user))
        self.assertEqual(contents, {self.public_reply, self.public_share_reply})
        contents = set(Content.objects.children(self.limited_content.id, self.anonymous_user))
        self.assertEqual(contents, set())
        contents = set(Content.objects.children(self.self_content.id, self.anonymous_user))
        self.assertEqual(contents, set())
        contents = set(Content.objects.children(self.site_content.id, self.anonymous_user))
        self.assertEqual(contents, set())

        contents = set(Content.objects.children(self.public_content.id, self.self_user))
        self.assertEqual(contents, {self.public_reply, self.public_share_reply})
        contents = set(Content.objects.children(self.limited_content.id, self.self_user))
        self.assertEqual(contents, set())
        contents = set(Content.objects.children(self.self_content.id, self.self_user))
        self.assertEqual(contents, set())
        contents = set(Content.objects.children(self.site_content.id, self.self_user))
        self.assertEqual(contents, {self.site_reply, self.share_site_reply})
