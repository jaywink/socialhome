from unittest.mock import Mock

from django.test import TestCase

from socialhome.enums import Visibility
from socialhome.users.models import Profile
from socialhome.users.tests.factories import ProfileFactory


class TestProfileQuerySet(TestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.public_profile = ProfileFactory(visibility=Visibility.PUBLIC)
        cls.site_profile = ProfileFactory(visibility=Visibility.SITE)
        cls.profile = ProfileFactory()
        cls.profile2 = ProfileFactory()

    def test_unauthenticated_user(self):
        self.assertEqual(set(Profile.objects.visible_for_user(Mock(is_authenticated=False))), {self.public_profile})

    def test_authenticated_user(self):
        self.assertEqual(
            set(Profile.objects.visible_for_user(
                Mock(is_authenticated=True, profile=Mock(id=self.profile.id), is_staff=False)
            )),
            {self.public_profile, self.site_profile, self.profile}
        )

    def test_staff_user(self):
        self.assertEqual(
            set(Profile.objects.visible_for_user(
                Mock(is_authenticated=True, is_staff=True)
            )),
            {self.public_profile, self.site_profile, self.profile, self.profile2}
        )
