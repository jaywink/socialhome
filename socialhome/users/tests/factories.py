import factory
from factory import fuzzy


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
