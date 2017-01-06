import datetime
from unittest.mock import Mock, patch, call

import pytest
from django.contrib.auth.models import AnonymousUser
from django.db import IntegrityError, transaction
from django.template.loader import render_to_string
from django.utils.timezone import make_aware
from test_plus import TestCase

from socialhome.content.models import Content, OpenGraphCache, OEmbedCache
from socialhome.content.tests.factories import ContentFactory, OEmbedCacheFactory, OpenGraphCacheFactory
from socialhome.enums import Visibility
from socialhome.users.tests.factories import ProfileFactory


@pytest.mark.usefixtures("db")
class TestContentModel(TestCase):
    @classmethod
    def setUpTestData(cls):
        super(TestContentModel, cls).setUpTestData()
        cls.public_content = ContentFactory(
            visibility=Visibility.PUBLIC, text="**Foobar**"
        )
        cls.site_content = ContentFactory(
            visibility=Visibility.SITE, text="_Foobar_"
        )
        cls.limited_content = ContentFactory(visibility=Visibility.LIMITED)
        cls.self_content = ContentFactory(visibility=Visibility.SELF)
        cls.remote_content = ContentFactory(
            visibility=Visibility.PUBLIC, remote_created=make_aware(datetime.datetime(2015, 1, 1))
        )
        cls.ids = [
            cls.public_content.id, cls.site_content.id, cls.limited_content.id, cls.self_content.id
        ]
        cls.set = {
            cls.public_content, cls.site_content, cls.limited_content, cls.self_content
        }

    def test_create(self):
        Content.objects.create(text="foobar", guid="barfoo", author=ProfileFactory())

    def test_gets_guid_on_save_with_user(self):
        content = Content(text="foobar")
        content.save(author=ProfileFactory())
        assert content.guid

    def test_raises_on_save_without_user(self):
        content = Content(text="foobar")
        with transaction.atomic(), self.assertRaises(IntegrityError):
            content.save()

    def test_renders(self):
        content = Content.objects.create(text="# Foobar <img src='localhost'>", guid="barfoo", author=ProfileFactory())
        self.assertEqual(content.render(), "<h1>Foobar <img src='localhost'></h1>")
        self.assertEqual(content.rendered, "<h1>Foobar <img src='localhost'></h1>")

    def test_renders_with_nsfw_shield(self):
        content = Content.objects.create(
            text="<img src='localhost'> #nsfw", guid="barfoo", author=ProfileFactory()
        )
        self.assertEqual(content.render(), '<p><img class="nsfw" src="localhost"/> #nsfw</p>')
        self.assertEqual(content.rendered, '<p><img class="nsfw" src="localhost"/> #nsfw</p>')

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

    def test_get_contents_for_unauthenticated_user(self):
        user = AnonymousUser()
        contents = Content.get_contents_for_user(self.ids, user)
        self.assertEqual(set(contents), {self.public_content})

    def test_get_contents_for_self(self):
        user = self.make_user()
        user.profile = self.self_content.author
        user.save()
        contents = Content.get_contents_for_user(self.ids, user)
        self.assertEqual(set(contents), self.set - {self.limited_content})

    def test_get_contents_for_authenticated_other_user(self):
        user = self.make_user()
        contents = Content.get_contents_for_user(self.ids, user)
        self.assertEqual(set(contents), self.set - {self.self_content, self.limited_content})

    def test_get_rendered_contents_for_user(self):
        user = self.make_user()
        contents = Content.get_rendered_contents_for_user(
            [self.public_content.id, self.site_content.id],
            user
        )
        self.assertEqual(contents, [
            {
                "id": self.public_content.id,
                "author": self.public_content.author_id,
                "rendered": "<p><strong>Foobar</strong></p>",
            },
            {
                "id": self.site_content.id,
                "author": self.site_content.author_id,
                "rendered": "<p><em>Foobar</em></p>",
            }
        ])

    def test_busts_cache_on_save(self):
        self.public_content.bust_cache = Mock()
        self.public_content.save()
        self.public_content.bust_cache.assert_called_once_with()

    @patch("socialhome.content.models.safe_clear_cached_property")
    def test_bust_cache_calls_safe_cache_clearer(self, mock_clear):
        self.public_content.bust_cache()
        self.assertEqual(mock_clear.call_args_list, [
            call(self.public_content, "is_nsfw"), call(self.public_content, "rendered")
        ])

    def test_is_local(self):
        self.assertFalse(self.public_content.is_local)
        user = self.make_user()
        user.profile = self.public_content.author
        user.save()
        self.assertTrue(self.public_content.is_local)

    def test_save_calls_fix_local_uploads(self):
        self.public_content.fix_local_uploads = Mock()
        self.public_content.save()
        self.public_content.fix_local_uploads.assert_called_once_with()

    def test_fix_local_uploads(self):
        self.public_content.text = "foobar ![](/media/markdownx/12345.jpg) barfoo"
        self.public_content.save()
        self.public_content.refresh_from_db()
        self.assertEqual(
            self.public_content.text,
            "foobar ![](http://127.0.0.1:8000/media/markdownx/12345.jpg) barfoo"
        )

    def test_effective_created(self):
        self.assertEqual(self.public_content.effective_created, self.public_content.created)
        self.assertIsNone(self.public_content.remote_created)
        self.assertEqual(self.remote_content.effective_created, self.remote_content.remote_created)
        self.assertIsNotNone(self.remote_content.remote_created)


class TestOpenGraphCache(TestCase):
    def test_str(self):
        ogc = OpenGraphCache(url="https://example.com", title="x"*200, description="bar", image="https://example.com")
        self.assertEqual(str(ogc), "https://example.com / %s..." % ("x"*30))


class TestOEmbedCache(TestCase):
    def test_str(self):
        oec = OEmbedCache(url="https://example.com", oembed="x"*200)
        self.assertEqual(str(oec), "https://example.com")
