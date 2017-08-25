from django.contrib.auth.models import AnonymousUser

from socialhome.content.templatetags.content import has_shared
from socialhome.content.tests.factories import ContentFactory
from socialhome.tests.utils import SocialhomeTestCase
from socialhome.users.tests.factories import UserFactory


class TestHasShared(SocialhomeTestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.content = ContentFactory()
        cls.anonymous_user = AnonymousUser()
        cls.user = UserFactory()

    def test_survives_checking_anonymous_user_who_doesnt_have_a_profile(self):
        self.assertFalse(has_shared(self.content, self.anonymous_user))

    def test_returns_true_on_shared(self):
        self.content.share(self.user.profile)
        self.assertTrue(has_shared(self.content, self.user))

    def test_returns_false_on_not_shared(self):
        self.assertFalse(has_shared(self.content, self.user))
