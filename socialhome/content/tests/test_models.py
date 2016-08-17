# -*- coding: utf-8 -*-
import pytest
from django.contrib.auth.models import AnonymousUser
from django.db import IntegrityError, transaction
from test_plus import TestCase

from socialhome.content.models import Content
from socialhome.content.tests.factories import ContentFactory
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
        content = Content.objects.create(text="# Foobar", guid="barfoo", author=ProfileFactory())
        assert content.render() == "<h1>Foobar</h1>"
        assert content.rendered == "<h1>Foobar</h1>"

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
