import factory
from django.conf import settings

from socialhome.content.models import Content, OEmbedCache, OpenGraphCache, Tag
from socialhome.enums import Visibility
from socialhome.users.tests.factories import ProfileFactory, UserFactory, PublicProfileFactory, SiteProfileFactory, \
    LimitedProfileFactory, SelfProfileFactory


class TagFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Tag

    name = factory.Faker("user_name")


class ContentFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Content

    author = factory.SubFactory(ProfileFactory)
    fid = factory.LazyAttribute(lambda o: f"{settings.SOCIALHOME_URL}/content/{o.uuid}/")
    text = factory.Faker("text")
    uuid = factory.Faker('uuid4')


class PublicContentFactory(ContentFactory):
    visibility = Visibility.PUBLIC
    author = factory.SubFactory(PublicProfileFactory)


class LimitedContentFactory(ContentFactory):
    visibility = Visibility.LIMITED
    author = factory.SubFactory(LimitedProfileFactory)


class LimitedContentWithRecipientsFactory(ContentFactory):
    visibility = Visibility.LIMITED
    author = factory.SubFactory(LimitedProfileFactory)

    @classmethod
    def _generate(cls, strategy, params):
        recipients = params.pop("recipients", None)
        content = super()._generate(strategy, params)

        if recipients is not None:
            content.limited_visibilities.clear()
            content.limited_visibilities.set(recipients)
        else:
            recipient1 = PublicProfileFactory()
            recipient2 = PublicProfileFactory()
            content.limited_visibilities.clear()
            content.limited_visibilities.set([recipient1, recipient2])

        return content


class SiteContentFactory(ContentFactory):
    visibility = Visibility.SITE
    author = factory.SubFactory(SiteProfileFactory)


class SelfContentFactory(ContentFactory):
    visibility = Visibility.SELF
    author = factory.SubFactory(SelfProfileFactory)


class LocalContentFactory(ContentFactory):
    @factory.post_generation
    def set_profile_with_user(self, create, extracted, **kwargs):
        user = UserFactory()
        self.author = user.profile
        self.save()


class OEmbedCacheFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = OEmbedCache

    url = factory.Faker("url")
    oembed = factory.Faker("text")


class OpenGraphCacheFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = OpenGraphCache

    url = factory.Faker("url")
    title = factory.Faker("sentence", nb_words=3)
    description = factory.Faker("text")
    image = factory.Faker("url")
