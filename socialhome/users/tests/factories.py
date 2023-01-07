from random import randint

import factory
from allauth.account.models import EmailAddress
from django.conf import settings
from factory import fuzzy
from faker import Faker

from federation.entities import base

from socialhome.enums import Visibility


def get_random_image_url(width: int, height: int) -> str:
    # Faker.seed(0)
    fake = Faker()
    return fake.image_url(width=width, height=height)


class UserFactory(factory.django.DjangoModelFactory):
    username = factory.Sequence(lambda n: "user-{0}".format(n))
    email = factory.Sequence(lambda n: "user-{0}@example.com".format(n))
    password = factory.PostGenerationMethodCall("set_password", "password")

    class Meta:
        model = "users.User"

    @factory.post_generation
    def with_verified_email(self, create, extracted, **kwargs):
        if not create or not extracted:
            return

        EmailAddress.objects.create(
            user=self,
            email=self.email,
            verified=True,
        )


class LimitedUserFactory(UserFactory):
    @classmethod
    def _generate(cls, create, attrs):
        user = super(UserFactory, cls)._generate(create, attrs)
        user.profile.visibility = Visibility.LIMITED
        user.profile.save(update_fields=["visibility"])
        return user


class PublicUserFactory(UserFactory):
    @classmethod
    def _generate(cls, create, attrs):
        user = super(UserFactory, cls)._generate(create, attrs)
        user.profile.visibility = Visibility.PUBLIC
        user.profile.save(update_fields=["visibility"])
        return user


class SiteUserFactory(UserFactory):
    @classmethod
    def _generate(cls, create, attrs):
        user = super(UserFactory, cls)._generate(create, attrs)
        user.profile.visibility = Visibility.SITE
        user.profile.save(update_fields=["visibility"])
        return user


class SelfUserFactory(UserFactory):
    @classmethod
    def _generate(cls, create, attrs):
        user = super(UserFactory, cls)._generate(create, attrs)
        user.profile.visibility = Visibility.SELF
        user.profile.save(update_fields=["visibility"])
        return user


class UserWithKeyFactory(UserFactory):
    @classmethod
    def _generate(cls, create, attrs):
        user = super(UserFactory, cls)._generate(create, attrs)
        user.profile.generate_new_rsa_key(bits=1024)
        return user


class AdminUserFactory(UserFactory):
    is_superuser = True
    is_staff = True

    username = "admin"


class UserWithContactFactory(UserFactory):
    @classmethod
    def _generate(cls, create, attrs):
        count_following = attrs.pop("count_following", 3) if isinstance(attrs, dict) else 3
        count_followers = attrs.pop("count_followers", 3) if isinstance(attrs, dict) else 3
        following = [ProfileFactory() for _ in range(count_following)]
        followers = [ProfileFactory() for _ in range(count_followers)]

        user = super(UserWithContactFactory, cls)._generate(create, attrs)
        user.profile.following.set(following)
        user.profile.followers.set(followers)
        return user


class ProfileFactory(factory.django.DjangoModelFactory):
    email = factory.Faker("safe_email")
    fid = "placeholder"
    finger = factory.Faker("safe_email")
    name = factory.Faker("name")

    # Dummy strings as keys since generating these is expensive
    rsa_private_key = fuzzy.FuzzyText()
    rsa_public_key = fuzzy.FuzzyText()

    # Dummy image urls
    image_url_small = "https://127.0.0.1:8000/static/images/pony50.png"
    image_url_medium = "https://127.0.0.1:8000/static/images/pony100.png"
    image_url_large = "/static/images/pony300.png"

    uuid = factory.Faker('uuid4')

    class Meta:
        model = "users.Profile"

    class Params:
        diaspora = factory.Trait(
            handle=factory.lazy_attribute(lambda x: x.email),
            guid=factory.Faker('uuid4'),
        )

    
    @factory.post_generation
    def set_fid(self, extracted, created, **kwargs):
        if self.fid == "placeholder":
            self.fid = f"{settings.SOCIALHOME_URL}/u/{self.user.username}/" \
                if self.user else f"{settings.SOCIALHOME_URL}/p/{self.uuid}/"

    # noinspection PyAttributeOutsideInit
    @factory.post_generation
    def set_handle(self, extracted, created, **kwargs):
        if extracted is False or self.handle:
            return

        # Set handle sometimes, sometimes not, but also allow passing in True to force
        if extracted is True or randint(0, 100) > 50:
            self.handle = self.finger

    @factory.post_generation
    def with_key(self, extracted, created, **kwargs):
        if not extracted:
            return

        self.generate_new_rsa_key(bits=1024)


class PublicProfileFactory(ProfileFactory):
    visibility = Visibility.PUBLIC


class SiteProfileFactory(ProfileFactory):
    visibility = Visibility.SITE


class LimitedProfileFactory(ProfileFactory):
    visibility = Visibility.LIMITED


class SelfProfileFactory(ProfileFactory):
    visibility = Visibility.SELF


class BaseProfileFactory(factory.Factory):
    class Meta:
        model = base.Profile

    id = factory.Faker('uri')
    raw_content = factory.Faker("paragraphs", nb=3)
    email = factory.Faker("safe_email")
    gender = factory.Faker("job")
    location = "internet"
    nsfw = factory.Faker("pybool")
    public_key = factory.Faker("sha1")
    public = factory.Faker("pybool")
    image_urls = {
        "small": get_random_image_url(width=30, height=30),
        "medium": get_random_image_url(width=100, height=100),
        "large": get_random_image_url(width=300, height=300),
    }
    tag_list = factory.Faker("words", nb=4)


class BaseShareFactory(factory.Factory):
    class Meta:
        model = base.Share

    id = factory.Faker('uri')
    actor_id = factory.Faker('uri')
    target_id = factory.Faker('uri')
    public = factory.Faker("pybool")
