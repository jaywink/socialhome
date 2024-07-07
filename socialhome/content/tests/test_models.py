import datetime
import pytest
from unittest.mock import Mock

from django.contrib.auth.models import AnonymousUser
from django.core.exceptions import ValidationError
from django.template.loader import render_to_string
from django.utils.text import slugify
from django.utils.timezone import make_aware
from freezegun import freeze_time

from socialhome.content.enums import ContentType
from socialhome.content.models import Content, OpenGraphCache, OEmbedCache, Tag
from socialhome.content.tests.factories import (
    ContentFactory, OEmbedCacheFactory, OpenGraphCacheFactory, LocalContentFactory)
from socialhome.enums import Visibility
from socialhome.tests.utils import SocialhomeTestCase
from socialhome.users.tests.factories import UserFactory


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
        cls.content_with_twitter_oembed = ContentFactory(text='<a href="toto" class="twitter-tweet">bla</a>')
        cls.content_with_mentions = ContentFactory(
            text="foo @%s bar @%s" % (cls.user.profile.finger, cls.remote_profile.finger),
            author=cls.local_user.profile,
        )
        cls.content_with_url = ContentFactory(
            text="<p>https://example.com/foobar yay</p>", author=cls.local_user.profile,
        )

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
        content = ContentFactory()
        assert content.uuid

    # inbound mentions are extracted by federation
    # outbound mentions are supplied by the UI
    @pytest.mark.skip
    def test_extract_mentions(self):
        self.assertEqual(
            set(self.content_with_mentions.mentions.values_list('id', flat=True)),
            {self.user.profile.id, self.remote_profile.id},
        )

    # inbound mentions are extracted by federation
    # outbound mentions are supplied by the UI
    @pytest.mark.skip
    def test_extract_mentions__removes_mentions(self):
        self.content_with_mentions.text = "foo bar @{foo; %s}" % self.remote_profile.handle
        self.content_with_mentions.save()
        self.assertEqual(
            set(self.content_with_mentions.mentions.values_list('id', flat=True)),
            {self.remote_profile.id},
        )

    def test_has_had_local_replies(self):
        self.assertFalse(self.public_content.has_had_local_replies)
        self.assertFalse(self.remote_content.has_had_local_replies)
        # Add replies
        LocalContentFactory(parent=self.public_content)
        LocalContentFactory(parent=self.remote_content)
        self.public_content.refresh_from_db()
        self.remote_content.refresh_from_db()
        self.assertTrue(self.public_content.has_had_local_replies)
        self.assertTrue(self.remote_content.has_had_local_replies)

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
        user = UserFactory()
        pinned_content_1 = ContentFactory(pinned=True, text="foobar", author=user.profile)
        pinned_content_2 = ContentFactory(pinned=True, text="foobar", author=user.profile)
        pinned_content_3 = ContentFactory(pinned=True, text="foobar", author=user.profile)

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

    def test_short_text(self):
        self.assertEqual(self.public_content.short_text, "Foobar")

    def test_short_text_inline(self):
        self.public_content.text = "foo\n\rbar"
        self.public_content.render()
        self.assertEqual(self.public_content.short_text_inline, "foo bar")

    def test_slug(self):
        self.assertEqual(self.public_content.slug, slugify(self.public_content.short_text))

    def test_slug__strips_urls_and_html(self):
        self.assertEqual(self.content_with_url.slug, 'yay')

    def test_visible_for_user_unauthenticated_user(self):
        self.assertTrue(self.public_content.visible_for_user(Mock(is_authenticated=False, profile=None)))
        self.assertFalse(self.site_content.visible_for_user(Mock(is_authenticated=False, profile=None)))
        self.assertFalse(self.self_content.visible_for_user(Mock(is_authenticated=False, profile=None)))
        self.assertFalse(self.limited_content.visible_for_user(Mock(is_authenticated=False, profile=None)))

    def test_visible_for_user_authenticated_user(self):
        user = UserFactory()
        self.assertTrue(self.public_content.visible_for_user(Mock(is_authenticated=True, profile=user.profile)))
        self.assertTrue(self.site_content.visible_for_user(Mock(is_authenticated=True, profile=user.profile)))
        self.assertFalse(self.self_content.visible_for_user(Mock(is_authenticated=True, profile=user.profile)))
        self.assertFalse(self.limited_content.visible_for_user(Mock(is_authenticated=True, profile=user.profile)))

    def test_visible_for_user_limited_content_user(self):
        profile = self.limited_content.author
        self.assertTrue(self.public_content.visible_for_user(Mock(is_authenticated=True, profile=profile)))
        self.assertTrue(self.site_content.visible_for_user(Mock(is_authenticated=True, profile=profile)))
        self.assertFalse(self.self_content.visible_for_user(Mock(is_authenticated=True, profile=profile)))
        self.assertTrue(self.limited_content.visible_for_user(Mock(is_authenticated=True, profile=profile)))

    def test_visible_for_user_limited_content__limited_visibilities(self):
        self.limited_content.limited_visibilities.set((self.public_content.author, self.site_content.author))
        self.assertTrue(
            self.limited_content.visible_for_user(Mock(is_authenticated=True, profile=self.public_content.author))
        )
        self.assertTrue(
            self.limited_content.visible_for_user(Mock(is_authenticated=True, profile=self.site_content.author))
        )
        self.assertTrue(
            self.limited_content.visible_for_user(Mock(is_authenticated=True, profile=self.limited_content.author))
        )
        self.assertFalse(
            self.limited_content.visible_for_user(Mock(is_authenticated=True, profile=self.self_content.author))
        )

    def test_visible_for_user_self_content_user(self):
        profile = self.self_content.author
        self.assertTrue(self.public_content.visible_for_user(Mock(is_authenticated=True, profile=profile)))
        self.assertTrue(self.site_content.visible_for_user(Mock(is_authenticated=True, profile=profile)))
        self.assertTrue(self.self_content.visible_for_user(Mock(is_authenticated=True, profile=profile)))
        self.assertFalse(self.limited_content.visible_for_user(Mock(is_authenticated=True, profile=profile)))

    def test_channel_group_name(self):
        self.assertEqual(
            self.public_content.channel_group_name,
            "%s_%s" % (self.public_content.id, self.public_content.uuid),
        )

    def test_reply_gets_parent_values__if_not_set(self):
        reply = ContentFactory(parent=self.public_content)
        self.assertEqual(reply.visibility, Visibility.PUBLIC)
        self.assertFalse(reply.pinned)

    def test_reply_gets_parent_values__pinned(self):
        reply = ContentFactory(parent=self.public_content, pinned=True)
        self.assertFalse(reply.pinned)

    def test_reply_gets_parent_values__visibility_is_respected_if_different(self):
        reply = ContentFactory(parent=self.public_content, visibility=Visibility.LIMITED, pinned=True)
        self.assertEqual(reply.visibility, Visibility.LIMITED)

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
        content = ContentFactory(text="# Foobar <img src='localhost'>")
        self.assertEqual(content.rendered, '<h1>Foobar <img src="localhost"/></h1>')

    def test_renders_with_oembed(self):
        content = ContentFactory(text="foobar", oembed=OEmbedCacheFactory())
        self.assertEqual(content.rendered, "<p>foobar</p><br>%s" % content.oembed.oembed)

    def test_renders_with_opengraphcache(self):
        content = ContentFactory(text="foobar", opengraph=OpenGraphCacheFactory())
        rendered_og = render_to_string("content/_og_preview.html", {"opengraph": content.opengraph})
        self.assertEqual(content.rendered, "<p>foobar</p>%s" % rendered_og)

    def test_renders_linkified_tags(self):
        content = ContentFactory(text="#tag #MiXeD")
        self.assertEqual(content.rendered, '<p><a class="hashtag" href="/streams/tag/tag/">#tag</a> '
                                           '<a class="hashtag" href="/streams/tag/mixed/">#MiXeD</a></p>')

    def test_renders_without_previews_with_show_preview_false(self):
        content = ContentFactory(
            text="foobar", oembed=OEmbedCacheFactory(), opengraph=OpenGraphCacheFactory(),
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
            text="#a!a #a#a #a$a #a%a #a^a #a&a #a*a #a+a #a.a #a,a #a@a #a£a #a(a #a)a #a=a #a?a #a`a #a'a #a\\a "
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
        self.assertEqual(tags, {'a'})

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


class TestProcessTextLinks(SocialhomeTestCase):
    @classmethod
    def setUpTestData(cls):
        super(TestProcessTextLinks, cls).setUpTestData()
        cls.content = ContentFactory(
            text="**Foobar** #tag #othertag",
            show_preview=False
        )

    def test_link_at_start_or_end(self):
        self.content.text = 'https://example.org example.org\nhttp://example.org'
        self.content.render()
        assert self.content.rendered == \
               '<p><a href="https://example.org" rel="nofollow" target="_blank">https://example.org</a> ' \
               '<a href="https://example.org" rel="nofollow" target="_blank">example.org</a>\n' \
               '<a href="http://example.org" rel="nofollow" target="_blank">http://example.org</a></p>'

    def test_existing_links_get_attrs_added(self):
        self.content.text = '<a href="https://example.org">https://example.org</a>'
        self.content.render()
        assert self.content.rendered == \
               '<p><a href="https://example.org" rel="nofollow" target="_blank">https://example.org</a></p>'

    def test_code_sections_are_skipped(self):
        self.content.text = '<code>https://example.org</code><code>\nhttps://example.org\n</code>'
        self.content.render()
        assert self.content.rendered == \
               '<p><code>https://example.org</code><code>\nhttps://example.org\n</code></p>'

    def test_emails_are_skipped(self):
        self.content.text = 'foo@example.org'
        self.content.render()
        assert self.content.rendered == '<p>foo@example.org</p>'

    def test_does_not_add_target_blank_if_link_is_internal(self):
        self.content.text = '<a href="/streams/tag/foobar">#foobar</a>'
        self.content.render()
        assert self.content.rendered == \
               '<p><a class="hashtag" href="/streams/tag/foobar/">#foobar</a></p>'

    def test_does_not_remove_mention_classes(self):
        self.content.text = '<span class="h-card"><a class="u-url mention" href="https://dev.jasonrobinson.me/u/jaywink/">' \
                            '@<span>jaywink</span></a></span> boom'
        self.content.render()
        assert self.content.rendered == \
           '<p><span class="h-card"><a class="u-url mention" href="https://dev.jasonrobinson.me/u/jaywink/" ' \
           'rel="nofollow" target="_blank">@<span>jaywink</span></a></span> boom</p>'


class TestTagModel(SocialhomeTestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.tag = Tag.objects.create(name="foobar")
        cls.tag2 = Tag.objects.create(name="f"*150)
        cls.weird_tag = Tag.objects.create(name="github...")
        cls.russian_tag = Tag.objects.create(name="тег")

    def test_get_absolute_url(self):
        self.assertEqual(self.tag.get_absolute_url(), '/streams/tag/foobar/')

    def test_get_absolute_url__survives_weird_tags(self):
        self.assertEqual(self.weird_tag.get_absolute_url(), '/streams/tag/github/')

    def test_get_absolute_url__uses_uuid_when_slugify_fails(self):
        self.assertEqual(self.russian_tag.get_absolute_url(), f'/streams/tag/uuid-{self.russian_tag.uuid}/')

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
        self.assertEqual(str(ogc), "https://example.com / %s…" % ("x"*29))


class TestOEmbedCache(SocialhomeTestCase):
    def test_str(self):
        oec = OEmbedCache(url="https://example.com", oembed="x"*200)
        self.assertEqual(str(oec), "https://example.com")
