# -*- coding: utf-8 -*-
from factory import fuzzy
import factory

from socialhome.content.enums import ContentTarget
from socialhome.content.models import Post, Content
from socialhome.users.tests.factories import UserFactory


class PostFactory(factory.DjangoModelFactory):
    class Meta:
        model = Post

    text = fuzzy.FuzzyText()
    guid = fuzzy.FuzzyText()
    user = factory.SubFactory(UserFactory)


class ContentFactory(factory.DjangoModelFactory):
    class Meta:
        model = Content

    target = ContentTarget.PROFILE
    user = factory.SubFactory(UserFactory)
    content_object = factory.SubFactory(PostFactory)
