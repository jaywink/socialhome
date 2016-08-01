# -*- coding: utf-8 -*-
import pytest
from django.db import IntegrityError

from socialhome.content.models import Content
from socialhome.users.tests.factories import ProfileFactory


@pytest.mark.usefixtures("db")
class TestContentModel(object):
    def test_create(self):
        Content.objects.create(text="foobar", guid="barfoo", author=ProfileFactory())

    def test_gets_guid_on_save_with_user(self):
        content = Content(text="foobar")
        content.save(author=ProfileFactory())
        assert content.guid

    def test_raises_on_save_without_user(self):
        content = Content(text="foobar")
        with pytest.raises(IntegrityError):
            content.save()

    def test_renders(self):
        content = Content.objects.create(text="# Foobar", guid="barfoo", author=ProfileFactory())
        assert content.render() == "<h1>Foobar</h1>"
        assert content.rendered == "<h1>Foobar</h1>"
