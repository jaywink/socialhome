# -*- coding: utf-8 -*-
from factory import fuzzy
import factory

from socialhome.content.models import Content
from socialhome.users.tests.factories import ProfileFactory


class ContentFactory(factory.DjangoModelFactory):
    class Meta:
        model = Content

    text = fuzzy.FuzzyText()
    guid = fuzzy.FuzzyText()
    author = factory.SubFactory(ProfileFactory)
