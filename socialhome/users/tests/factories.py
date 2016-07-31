import factory
from factory import fuzzy


class UserFactory(factory.django.DjangoModelFactory):
    username = factory.Sequence(lambda n: 'user-{0}'.format(n))
    email = factory.Sequence(lambda n: 'user-{0}@example.com'.format(n))
    password = factory.PostGenerationMethodCall('set_password', 'password')

    class Meta:
        model = 'users.User'
        django_get_or_create = ('username', )


class ProfileFactory(factory.django.DjangoModelFactory):
    email = factory.Sequence(lambda n: 'user-{0}@example.com'.format(n))
    handle = factory.SelfAttribute("email")
    guid = factory.Sequence(lambda n: 'guid-{0}'.format(n))

    # Dummy strings as keys since generating these is expensive
    rsa_private_key = fuzzy.FuzzyText()
    rsa_public_key = fuzzy.FuzzyText()

    class Meta:
        model = 'users.Profile'
