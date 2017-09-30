import factory
from factory import fuzzy

from socialhome.content.models import Content, OEmbedCache, OpenGraphCache, Tag
from socialhome.enums import Visibility
from socialhome.users.tests.factories import ProfileFactory, UserFactory


class TagFactory(factory.DjangoModelFactory):
    class Meta:
        model = Tag

    name = factory.Faker("user_name")


class ContentFactory(factory.DjangoModelFactory):
    class Meta:
        model = Content

    text = fuzzy.FuzzyText()
    guid = fuzzy.FuzzyText()
    author = factory.SubFactory(ProfileFactory)


class PublicContentFactory(ContentFactory):
    text = fuzzy.FuzzyText(prefix="Public ")
    visibility = Visibility.PUBLIC


class LimitedContentFactory(ContentFactory):
    text = fuzzy.FuzzyText(prefix="Limited ")
    visibility = Visibility.LIMITED


class SiteContentFactory(ContentFactory):
    text = fuzzy.FuzzyText(prefix="Site ")
    visibility = Visibility.SITE


class SelfContentFactory(ContentFactory):
    text = fuzzy.FuzzyText(prefix="Self ")
    visibility = Visibility.SELF


class LocalContentFactory(ContentFactory):
    @factory.post_generation
    def set_profile_with_user(self, create, extracted, **kwargs):
        user = UserFactory()
        self.author = user.profile
        self.save()


class OEmbedCacheFactory(factory.DjangoModelFactory):
    class Meta:
        model = OEmbedCache

    url = factory.Faker("url")
    oembed = factory.Faker("text")


class OpenGraphCacheFactory(factory.DjangoModelFactory):
    class Meta:
        model = OpenGraphCache

    url = factory.Faker("url")
    title = factory.Faker("sentence", nb_words=3)
    description = factory.Faker("text")
    image = factory.Faker("url")
