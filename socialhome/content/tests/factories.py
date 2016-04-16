# -*- coding: utf-8 -*-
from factory import fuzzy
import factory

from socialhome.content.models import Post
from socialhome.users.tests.factories import UserFactory


class PostFactory(factory.DjangoModelFactory):
    class Meta:
        model = Post

    text = fuzzy.FuzzyText()
    guid = fuzzy.FuzzyText()
    user = factory.SubFactory(UserFactory)
