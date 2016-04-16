# -*- coding: utf-8 -*-
import pytest

from socialhome.content.models import Post
from socialhome.users.tests.factories import UserFactory


@pytest.mark.usefixtures("db")
class TestPostModel(object):
    def test_post_model_create(self):
        post = Post.objects.create(text="foobar", guid="barfoo", user=UserFactory())
