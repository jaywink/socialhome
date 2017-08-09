import factory
from factory import fuzzy

from federation.entities import base


class UserFactory(factory.django.DjangoModelFactory):
    username = factory.Sequence(lambda n: "user-{0}".format(n))
    email = factory.Sequence(lambda n: "user-{0}@example.com".format(n))
    password = factory.PostGenerationMethodCall("set_password", "password")

    class Meta:
        model = "users.User"


class AdminUserFactory(UserFactory):
    is_superuser = True
    is_staff = True

    username = "admin"


class ProfileFactory(factory.django.DjangoModelFactory):
    name = factory.Faker("name")
    email = factory.Sequence(lambda n: "user-{0}@example.com".format(n))
    handle = factory.SelfAttribute("email")
    guid = factory.Sequence(lambda n: "guid-{0}".format(n))

    # Dummy strings as keys since generating these is expensive
    rsa_private_key = fuzzy.FuzzyText()
    rsa_public_key = fuzzy.FuzzyText()

    # Dummy image urls
    image_url_small = "https://127.0.0.1:8000/foo/small.png"
    image_url_medium = "https://127.0.0.1:8000/foo/medium.png"
    image_url_large = "/foo/large.png"

    class Meta:
        model = "users.Profile"


class BaseProfileFactory(factory.Factory):
    class Meta:
        model = base.Profile

    handle = factory.Faker("safe_email")
    raw_content = factory.Faker("paragraphs", nb=3)
    email = factory.Faker("safe_email")
    gender = factory.Faker("job")
    location = factory.Faker("country")
    nsfw = factory.Faker("pybool")
    public_key = factory.Faker("sha1")
    public = factory.Faker("pybool")
    guid = factory.Faker("uuid4")
    image_urls = {
        "small": factory.Faker("image_url", width=30, height=30).generate({}),
        "medium": factory.Faker("image_url", width=100, height=100).generate({}),
        "large": factory.Faker("image_url", width=300, height=300).generate({}),
    }
    tag_list = factory.Faker("words", nb=4)
