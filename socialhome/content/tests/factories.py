from factory import (
    SubFactory, fuzzy, DjangoModelFactory, post_generation
)

from socialhome.content.models import Content
from socialhome.users.tests.factories import ProfileFactory, UserFactory


class ContentFactory(DjangoModelFactory):
    class Meta:
        model = Content

    text = fuzzy.FuzzyText()
    guid = fuzzy.FuzzyText()
    author = SubFactory(ProfileFactory)


class LocalContentFactory(ContentFactory):
    @post_generation
    def set_profile_with_user(self, create, extracted, **kwargs):
        user = UserFactory()
        self.author = user.profile
        self.save()
