import datetime
from unittest.mock import Mock

from django.contrib.auth.models import AnonymousUser
from django.core.exceptions import ValidationError
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils.text import slugify
from django.utils.timezone import make_aware
from django_extensions.utils.text import truncate_letters
from freezegun import freeze_time

from socialhome.content.enums import ContentType
from socialhome.content.models import Content, OpenGraphCache, OEmbedCache, Tag
from socialhome.content.tests.factories import (
    ContentFactory, OEmbedCacheFactory, OpenGraphCacheFactory, LocalContentFactory)
from socialhome.enums import Visibility
from socialhome.tests.utils import SocialhomeTestCase
from socialhome.users.models import Profile
from socialhome.users.tests.factories import ProfileFactory, UserFactory


@freeze_time("2017-03-11")
class TestContentModel(SocialhomeTestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.create_local_and_remote_user()
        cls.user2 = AnonymousUser()
        cls.local_user = UserFactory()
        cls.public_content = ContentFactory(
            visibility=Visibility.PUBLIC, text="**Foobar**", author=cls.profile,
        )
        cls.site_content = ContentFactory(
            visibility=Visibility.SITE, text="_Foobar_"
        )
        cls.limited_content = ContentFactory(visibility=Visibility.LIMITED)
        cls.self_content = ContentFactory(visibility=Visibility.SELF)
        cls.remote_content = ContentFactory(
            visibility=Visibility.PUBLIC, remote_created=make_aware(datetime.datetime(2015, 1, 1)),
            author=cls.remote_profile,
        )
        cls.ids = [
            cls.public_content.id, cls.site_content.id, cls.limited_content.id, cls.self_content.id
        ]
        cls.set = {
            cls.public_content, cls.site_content, cls.limited_content, cls.self_content
        }
        cls.content_with_twitter_oembed = ContentFactory(text='class="twitter-tweet"')

    def setUp(self):
        super().setUp()
        self.public_content.refresh_from_db()
        try:
            del self.public_content.short_text
        except AttributeError:
            pass
        try:
            del self.public_content.slug
        except AttributeError:
            pass
        self.site_content.refresh_from_db()

    def test_create(self):
        content = Content.objects.create(text="foobar", author=ProfileFactory())
        assert content.guid

    def test_get_rendered_contents(self):
        qs = Content.objects.filter(id__in=[self.public_content.id, self.site_content.id])
        contents = Content.get_rendered_contents(qs, self.user2)
        self.assertEqual(contents, [
            {
                "author": self.public_content.author_id,
                "author_guid": self.public_content.author.guid,
                "author_handle": self.public_content.author.handle,
                "author_home_url": self.public_content.author.home_url,
                "author_image": self.public_content.author.safer_image_url_small,
                "author_is_local": bool(self.public_content.author.user),
                "author_name": self.public_content.author.handle,
                "author_profile_url": self.public_content.author.get_absolute_url(),
                "content_type": self.public_content.content_type.string_value,
                "delete_url": "",
                "detail_url": self.public_content.get_absolute_url(),
                "formatted_timestamp": self.public_content.timestamp,
                "guid": self.public_content.guid,
                "has_shared": False,
                "humanized_timestamp": self.public_content.humanized_timestamp,
                "id": self.public_content.id,
                "is_authenticated": False,
                "is_author": False,
                "is_following_author": False,
                "parent": "",
                "profile_id": "",
                "rendered": "<p><strong>Foobar</strong></p>",
                "reply_count": 0,
                "reply_url": "",
                "shares_count": 0,
                "slug": self.public_content.slug,
                "through": self.public_content.id,
                "update_url": "",
            },
            {
                "author": self.site_content.author_id,
                "author_guid": self.site_content.author.guid,
                "author_handle": self.site_content.author.handle,
                "author_home_url": self.site_content.author.home_url,
                "author_image": self.site_content.author.safer_image_url_small,
                "author_is_local": bool(self.site_content.author.user),
                "author_name": self.site_content.author.name,
                "author_profile_url": self.site_content.author.get_absolute_url(),
                "content_type": self.site_content.content_type.string_value,
                "delete_url": "",
                "detail_url": self.site_content.get_absolute_url(),
                "formatted_timestamp": self.site_content.timestamp,
                "guid": self.site_content.guid,
                "has_shared": False,
                "humanized_timestamp": self.site_content.humanized_timestamp,
                "id": self.site_content.id,
                "is_authenticated": False,
                "is_author": False,
                "is_following_author": False,
                "parent": "",
                "profile_id": "",
                "rendered": "<p><em>Foobar</em></p>",
                "reply_count": 0,
                "reply_url": "",
                "shares_count": 0,
                "slug": self.site_content.slug,
                "through": self.site_content.id,
                "update_url": "",
            }
        ])

    def test_get_rendered_contents__with_throughs(self):
        qs = Content.objects.filter(id__in=[self.public_content.id, self.site_content.id])
        contents = Content.get_rendered_contents(qs, self.user2, throughs={self.site_content.id: 123})
        self.assertEqual(contents[0].get("through"), self.public_content.id)
        self.assertEqual(contents[1].get("through"), 123)

    def test_has_shared(self):
        self.assertFalse(Content.has_shared(self.public_content.id, self.local_user.profile.id))
        # Do a share
        self.public_content.share(self.local_user.profile)
        self.assertTrue(Content.has_shared(self.public_content.id, self.local_user.profile.id))

    def test_has_twitter_oembed__no_oembed(self):
        self.assertFalse(self.public_content.has_twitter_oembed)

    def test_has_twitter_oembed__contains_oembed(self):
        self.assertTrue(self.content_with_twitter_oembed.has_twitter_oembed)

    def test_is_local(self):
        self.assertFalse(self.site_content.local)
        self.site_content.author = self.profile
        self.site_content.save()
        self.assertTrue(self.site_content.local)

    def test_root(self):
        self.assertEqual(self.public_content.root, self.public_content)
        reply = ContentFactory(parent=self.public_content)
        self.assertEqual(reply.root, self.public_content)
        reply_of_reply = ContentFactory(parent=reply)
        self.assertEqual(reply_of_reply.root, self.public_content)
        share = ContentFactory(share_of=self.public_content)
        self.assertEqual(share.root, self.public_content)
        share_reply = ContentFactory(parent=share)
        self.assertEqual(share_reply.root, self.public_content)
        share_reply_of_reply = ContentFactory(parent=share_reply)
        self.assertEqual(share_reply_of_reply.root, self.public_content)

    def test_save_calls_fix_local_uploads(self):
        self.public_content.fix_local_uploads = Mock()
        self.public_content.save()
        self.public_content.fix_local_uploads.assert_called_once_with()

    def test_share_raises_on_non_content_content_type(self):
        with self.assertRaises(ValidationError):
            LocalContentFactory(parent=self.public_content, author=self.local_user.profile).share(self.profile)

    def test_share_raises_if_shared_before(self):
        self.public_content.share(self.local_user.profile)
        with self.assertRaises(ValidationError):
            self.public_content.share(self.local_user.profile)

    def test_share_raises_if_sharing_own_content(self):
        with self.assertRaises(ValidationError):
            self.public_content.share(self.profile)

    def test_share_raises_if_content_not_visible(self):
        with self.assertRaises(ValidationError):
            self.self_content.share(self.profile)

    def test_share(self):
        share = self.public_content.share(self.local_user.profile)
        self.assertEqual(share.share_of, self.public_content)
        self.assertNotEqual(share.id, self.public_content.id)
        self.assertEqual(share.author, self.local_user.profile)

    def test_unshare_raises_if_no_share_exists(self):
        with self.assertRaises(ValidationError):
            self.public_content.unshare(self.profile)

    def test_unshare_removes_a_share(self):
        self.public_content.share(self.local_user.profile)
        assert Content.has_shared(self.public_content.id, self.local_user.profile.id)
        self.public_content.unshare(self.local_user.profile)
        self.assertFalse(Content.has_shared(self.public_content.id, self.local_user.id))

    def test_fix_local_uploads(self):
        self.public_content.text = "foobar ![](/media/uploads/12345.jpg) barfoo"
        self.public_content.save()
        self.assertEqual(
            self.public_content.text,
            "foobar ![](http://127.0.0.1:8000/media/uploads/12345.jpg) barfoo"
        )

    def test_effective_modified(self):
        self.assertEqual(self.public_content.effective_modified, self.public_content.created)
        self.assertIsNone(self.public_content.remote_created)
        self.assertEqual(self.remote_content.effective_modified, self.remote_content.remote_created)
        self.assertIsNotNone(self.remote_content.remote_created)

    def test_content_saved_in_correct_order(self):
        profile = ProfileFactory(guid="1234")
        pinned_content_1 = ContentFactory(pinned=True, text="foobar", author=profile)
        pinned_content_2 = ContentFactory(pinned=True, text="foobar", author=profile)
        pinned_content_3 = ContentFactory(pinned=True, text="foobar", author=profile)

        self.assertEqual([pinned_content_1.order, pinned_content_2.order, pinned_content_3.order], [1, 2, 3])

    def test_edited_is_false_for_newly_created_content(self):
        self.assertFalse(self.public_content.edited)

    def test_edited_is_false_for_newly_created_content_within_15_minutes_grace_period(self):
        with freeze_time(self.public_content.created + datetime.timedelta(minutes=14)):
            self.public_content.save()
            self.assertFalse(self.public_content.edited)

    def test_edited_is_true_for_newly_created_content_after_15_minutes_grace_period(self):
        with freeze_time(self.public_content.created + datetime.timedelta(minutes=16)):
            self.public_content.save()
            self.assertTrue(self.public_content.edited)

    def test_dict_for_view(self):
        self.assertEqual(self.public_content.dict_for_view(self.user2), {
            "author": self.public_content.author_id,
            "author_guid": self.public_content.author.guid,
            "author_handle": self.public_content.author.handle,
            "author_home_url": self.public_content.author.home_url,
            "author_image": self.public_content.author.safer_image_url_small,
            "author_is_local": bool(self.public_content.author.user),
            "author_name": self.public_content.author.handle,
            "author_profile_url": self.public_content.author.get_absolute_url(),
            "content_type": self.public_content.content_type.string_value,
            "delete_url": "",
            "detail_url": self.public_content.get_absolute_url(),
            "formatted_timestamp": self.public_content.timestamp,
            "guid": self.public_content.guid,
            "has_shared": False,
            "humanized_timestamp": self.public_content.humanized_timestamp,
            "id": self.public_content.id,
            "is_authenticated": False,
            "is_author": False,
            "is_following_author": False,
            "parent": "",
            "profile_id": "",
            "rendered": self.public_content.rendered,
            "reply_count": 0,
            "reply_url": "",
            "shares_count": 0,
            "slug": self.public_content.slug,
            "through": self.public_content.id,
            "update_url": "",
        })

        # Add a share
        ContentFactory(share_of=self.public_content)
        dict_for_view = self.public_content.dict_for_view(self.user2)
        self.assertEqual(dict_for_view.get("shares_count"), 1)

    def test_dict_for_view_for_author(self):
        Profile.objects.filter(id=self.profile.id).update(name="Foo Bar")
        self.assertEqual(self.public_content.dict_for_view(self.user), {
            "author": self.public_content.author_id,
            "author_guid": self.public_content.author.guid,
            "author_handle": self.public_content.author.handle,
            "author_home_url": self.public_content.author.home_url,
            "author_image": self.public_content.author.safer_image_url_small,
            "author_is_local": bool(self.public_content.author.user),
            "author_name": self.public_content.author.handle,
            "author_profile_url": self.public_content.author.get_absolute_url(),
            "content_type": self.public_content.content_type.string_value,
            "delete_url": reverse("content:delete", kwargs={"pk": self.public_content.id}),
            "detail_url": self.public_content.get_absolute_url(),
            "formatted_timestamp": self.public_content.timestamp,
            "guid": self.public_content.guid,
            "has_shared": False,
            "humanized_timestamp": self.public_content.humanized_timestamp,
            "id": self.public_content.id,
            "is_authenticated": True,
            "is_author": True,
            "is_following_author": False,
            "parent": "",
            "profile_id": self.public_content.author.id,
            "rendered": self.public_content.rendered,
            "reply_count": 0,
            "reply_url": reverse("content:reply", kwargs={"pk": self.public_content.id}),
            "shares_count": 0,
            "slug": self.public_content.slug,
            "through": self.public_content.id,
            "update_url": reverse("content:update", kwargs={"pk": self.public_content.id}),
        })

    def test_dict_for_view_edited_post(self):
        with freeze_time(self.public_content.created + datetime.timedelta(minutes=16)):
            self.public_content.save()
            self.assertEqual(self.public_content.dict_for_view(self.user), {
                "author": self.public_content.author_id,
                "author_guid": self.public_content.author.guid,
                "author_handle": self.public_content.author.handle,
                "author_home_url": self.public_content.author.home_url,
                "author_image": self.public_content.author.safer_image_url_small,
                "author_is_local": bool(self.public_content.author.user),
                "author_name": self.public_content.author.handle,
                "author_profile_url": self.public_content.author.get_absolute_url(),
                "content_type": self.public_content.content_type.string_value,
                "delete_url": reverse("content:delete", kwargs={"pk": self.public_content.id}),
                "detail_url": self.public_content.get_absolute_url(),
                "formatted_timestamp": self.public_content.timestamp,
                "guid": self.public_content.guid,
                "has_shared": False,
                "humanized_timestamp": "%s (edited)" % self.public_content.humanized_timestamp,
                "id": self.public_content.id,
                "is_authenticated": True,
                "is_author": True,
                "is_following_author": False,
                "parent": "",
                "profile_id": self.public_content.author.id,
                "rendered": self.public_content.rendered,
                "reply_count": 0,
                "reply_url": reverse("content:reply", kwargs={"pk": self.public_content.id}),
                "shares_count": 0,
                "slug": self.public_content.slug,
                "through": self.public_content.id,
                "update_url": reverse("content:update", kwargs={"pk": self.public_content.id}),
            })

    def test_short_text(self):
        self.assertEqual(self.public_content.short_text, truncate_letters(self.public_content.text, 50))

    def test_short_text_inline(self):
        self.public_content.text = "foo\n\rbar"
        self.assertEqual(self.public_content.short_text_inline, "foo bar")

    def test_slug(self):
        self.assertEqual(self.public_content.slug, slugify(self.public_content.short_text))

    def test_visible_for_user_unauthenticated_user(self):
        self.assertTrue(self.public_content.visible_for_user(Mock(is_authenticated=False)))
        self.assertFalse(self.site_content.visible_for_user(Mock(is_authenticated=False)))
        self.assertFalse(self.self_content.visible_for_user(Mock(is_authenticated=False)))
        self.assertFalse(self.limited_content.visible_for_user(Mock(is_authenticated=False)))

    def test_visible_for_user_authenticated_user(self):
        self.assertTrue(self.public_content.visible_for_user(Mock(is_authenticated=True)))
        self.assertTrue(self.site_content.visible_for_user(Mock(is_authenticated=True)))
        self.assertFalse(self.self_content.visible_for_user(Mock(is_authenticated=True)))
        self.assertFalse(self.limited_content.visible_for_user(Mock(is_authenticated=True)))

    def test_visible_for_user_limited_content_user(self):
        profile = self.limited_content.author
        self.assertTrue(self.public_content.visible_for_user(Mock(is_authenticated=True, profile=profile)))
        self.assertTrue(self.site_content.visible_for_user(Mock(is_authenticated=True, profile=profile)))
        self.assertFalse(self.self_content.visible_for_user(Mock(is_authenticated=True, profile=profile)))
        self.assertTrue(self.limited_content.visible_for_user(Mock(is_authenticated=True, profile=profile)))

    def test_visible_for_user_self_content_user(self):
        profile = self.self_content.author
        self.assertTrue(self.public_content.visible_for_user(Mock(is_authenticated=True, profile=profile)))
        self.assertTrue(self.site_content.visible_for_user(Mock(is_authenticated=True, profile=profile)))
        self.assertTrue(self.self_content.visible_for_user(Mock(is_authenticated=True, profile=profile)))
        self.assertFalse(self.limited_content.visible_for_user(Mock(is_authenticated=True, profile=profile)))

    def test_channel_group_name(self):
        self.assertEquals(
            self.public_content.channel_group_name,
            "%s_%s" % (self.public_content.id, slugify(self.public_content.guid)),
        )
        long_non_ascii_guid_content = ContentFactory(guid="ä"*150)
        self.assertEquals(
            long_non_ascii_guid_content.channel_group_name, "%s_%s" % (
                long_non_ascii_guid_content.id, "a"*(79-len(str(long_non_ascii_guid_content.id)))
            )
        )

    def test_reply_gets_parent_values(self):
        # Try with other values
        reply = ContentFactory(parent=self.public_content, visibility=Visibility.SELF, pinned=True)
        self.assertEqual(reply.visibility, Visibility.PUBLIC)
        self.assertFalse(reply.pinned)

    def test_get_absolute_url(self):
        self.assertEqual(self.public_content.get_absolute_url(),
                         "/content/%s/%s/" % (self.public_content.id, self.public_content.slug))
        self.public_content.text = "बियर राम्रो छ"
        self.public_content.save()
        del self.public_content.slug
        del self.public_content.short_text
        self.assertEqual(self.public_content.get_absolute_url(), "/content/%s/" % self.public_content.id)

    def test_save_raises_if_parent_and_share_of(self):
        with self.assertRaises(ValueError):
            ContentFactory(parent=ContentFactory(), share_of=ContentFactory())

    def test_save_sets_correct_content_type(self):
        self.assertEqual(self.public_content.content_type, ContentType.CONTENT)
        reply = ContentFactory(parent=ContentFactory())
        self.assertEqual(reply.content_type, ContentType.REPLY)
        share = ContentFactory(share_of=ContentFactory())
        self.assertEqual(share.content_type, ContentType.SHARE)


class TestContentRendered(SocialhomeTestCase):
    def test_renders(self):
        content = Content.objects.create(text="# Foobar <img src='localhost'>", guid="barfoo", author=ProfileFactory())
        self.assertEqual(content.rendered, '<h1>Foobar <img src="localhost"></h1>')

    def test_renders_with_nsfw_shield(self):
        content = Content.objects.create(
            text="<img src='localhost'> #nsfw", guid="barfoo", author=ProfileFactory()
        )
        self.assertEqual(content.rendered, '<p><img class="nsfw" src="localhost"/> '
                                           '<a href="/streams/tag/nsfw/">#nsfw</a></p>')

    def test_renders_with_oembed(self):
        content = Content.objects.create(
            text="foobar", guid="barfoo", author=ProfileFactory(),
            oembed=OEmbedCacheFactory()
        )
        self.assertEqual(content.rendered, "<p>foobar</p><br>%s" % content.oembed.oembed)

    def test_renders_with_opengraphcache(self):
        content = Content.objects.create(
            text="foobar", guid="barfoo", author=ProfileFactory(),
            opengraph=OpenGraphCacheFactory()
        )
        rendered_og = render_to_string("content/_og_preview.html", {"opengraph": content.opengraph})
        self.assertEqual(content.rendered, "<p>foobar</p>%s" % rendered_og)

    def test_renders_linkified_tags(self):
        content = ContentFactory(text="#tag #MiXeD")
        self.assertEqual(content.rendered, '<p><a href="/streams/tag/tag/">#tag</a> '
                                           '<a href="/streams/tag/mixed/">#MiXeD</a></p>')

    def test_renders_without_previews_with_show_preview_false(self):
        content = Content.objects.create(
            text="foobar", guid="barfoo", author=ProfileFactory(),
            oembed=OEmbedCacheFactory(), opengraph=OpenGraphCacheFactory(),
            show_preview=False,
        )
        self.assertEqual(content.rendered, "<p>foobar</p>")

class TestContentSaveTags(SocialhomeTestCase):
    @classmethod
    def setUpTestData(cls):
        super(TestContentSaveTags, cls).setUpTestData()
        cls.content = ContentFactory(
            text="**Foobar** #tag #othertag"
        )
        cls.text = ContentFactory(
            text="#starting and #MixED with some #line\nendings also tags can\n#start on new line"
        )
        cls.invalid = ContentFactory(
            text="#a!a #a#a #a$a #a%a #a^a #a&a #a*a #a+a #a.a #a,a #a@a #a£a #a/a #a(a #a)a #a=a #a?a #a`a #a'a #a\\a "
                 "#a{a #a[a #a]a #a}a #a~a #a;a #a:a #a\"a #a’a #a”a #\xa0cd"
        )
        cls.endings = ContentFactory(text="#parenthesis) #exp! #list]")
        cls.prefixed = ContentFactory(text="(#foo [#bar")
        cls.postfixed = ContentFactory(text="#foo) #bar] #hoo, #hee.")
        cls.code = ContentFactory(text="foo\n```\n#code\n```\n#notcode\n\n    #alsocode\n")

    def test_factory_instance_has_tags(self):
        self.assertTrue(Tag.objects.filter(name="tag").exists())
        self.assertTrue(Tag.objects.filter(name="othertag").exists())
        self.assertEqual(self.content.tags.count(), 2)
        tags = set(self.content.tags.values_list("name", flat=True))
        self.assertEqual(tags, {"tag", "othertag"})

    def test_extract_tags_adds_new_tags(self):
        self.content.text = "#post **Foobar** #tag #OtherTag #third\n#fourth"
        self.content.save()
        self.assertTrue(Tag.objects.filter(name="third").exists())
        self.assertTrue(Tag.objects.filter(name="post").exists())
        self.assertTrue(Tag.objects.filter(name="fourth").exists())
        self.assertEqual(self.content.tags.count(), 5)
        tags = set(self.content.tags.values_list("name", flat=True))
        self.assertEqual(tags, {"tag", "othertag", "third", "post", "fourth"})

    def test_extract_tags_removes_old_tags(self):
        self.content.text = "**Foobar** #tag #third"
        self.content.save()
        self.assertEqual(self.content.tags.count(), 2)
        tags = set(self.content.tags.values_list("name", flat=True))
        self.assertEqual(tags, {"tag", "third"})

    def test_all_tags_are_parsed_from_text(self):
        tags = set(self.text.tags.values_list("name", flat=True))
        self.assertEqual(
            tags,
            {"starting", "mixed", "line", "start"}
        )

    def test_invalid_text_returns_no_tags(self):
        tags = set(self.invalid.tags.values_list("name", flat=True))
        self.assertEqual(tags, set())

    def test_endings_are_filtered_out(self):
        tags = set(self.endings.tags.values_list("name", flat=True))
        self.assertEqual(
            tags,
            {"parenthesis", "exp", "list"}
        )

    def test_prefixed_tags(self):
        tags = set(self.prefixed.tags.values_list("name", flat=True))
        self.assertEqual(
            tags,
            {"foo", "bar"}
        )

    def test_postfixed_tags(self):
        tags = set(self.postfixed.tags.values_list("name", flat=True))
        self.assertEqual(
            tags,
            {"foo", "bar", "hoo", "hee"}
        )

    def test_code_block_tags_ignored(self):
        tags = set(self.code.tags.values_list("name", flat=True))
        self.assertEqual(
            tags,
            {"notcode"}
        )


class TestTagModel(SocialhomeTestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.tag = Tag.objects.create(name="foobar")
        cls.tag2 = Tag.objects.create(name="f"*150)

    def test_tag_instance_created(self):
        self.assertTrue(Tag.objects.filter(name="foobar").exists())

    def test_cleaned_name_filter(self):
        self.assertTrue(Tag.objects.exists_by_cleaned_name(" FooBaR "))
        tag = Tag.objects.get_by_cleaned_name(" FooBaR ")
        self.assertEqual(tag.name, "foobar")

    def test_channel_group_name(self):
        self.assertEqual(self.tag.channel_group_name, "%s_%s" % (self.tag.id, self.tag.name))
        self.assertEqual(self.tag2.channel_group_name, ("%s_%s" % (self.tag2.id, self.tag2.name))[:80])


class TestOpenGraphCache(SocialhomeTestCase):
    def test_str(self):
        ogc = OpenGraphCache(url="https://example.com", title="x"*200, description="bar", image="https://example.com")
        self.assertEqual(str(ogc), "https://example.com / %s..." % ("x"*30))


class TestOEmbedCache(SocialhomeTestCase):
    def test_str(self):
        oec = OEmbedCache(url="https://example.com", oembed="x"*200)
        self.assertEqual(str(oec), "https://example.com")
