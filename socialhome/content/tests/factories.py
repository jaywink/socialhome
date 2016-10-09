# -*- coding: utf-8 -*-
import factory
from factory import fuzzy

from socialhome.publisher.models import Content
from socialhome.users.tests.factories import ProfileFactory


class ContentFactory(factory.DjangoModelFactory):
    class Meta:
        model = Content

    text = fuzzy.FuzzyText()
    guid = fuzzy.FuzzyText()
    author = factory.SubFactory(ProfileFactory)
