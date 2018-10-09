from django.conf import settings
from django.test import override_settings
from federation.entities import base

from socialhome.content.tests.factories import PublicContentFactory
from socialhome.federate.utils import get_federable_object, get_profile, make_federable_profile
from socialhome.tests.utils import SocialhomeTestCase
from socialhome.users.tests.factories import UserFactory


class TestGetFederableObject(SocialhomeTestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.user = UserFactory()
        cls.profile = cls.user.profile
        cls.content = PublicContentFactory(author=cls.profile)

    def test_content_returned(self):
        profile = get_federable_object(self.profile.fid)
        self.assertTrue(isinstance(profile, base.Profile))
        self.assertEqual(profile.id, self.profile.fid)

    def test_profile_returned(self):
        with override_settings(SOCIALHOME_ROOT_PROFILE=self.user.username):
            profile = get_federable_object(settings.SOCIALHOME_URL)
        self.assertTrue(isinstance(profile, base.Profile))
        self.assertEqual(profile.id, self.profile.fid)

    def test_profile_returned_for_root_profile(self):
        content = get_federable_object(self.content.fid)
        self.assertTrue(isinstance(content, base.Post))
        self.assertEqual(content.id, self.content.fid)
        self.assertEqual(content.actor_id, self.profile.fid)


class TestGetProfile(SocialhomeTestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.user = UserFactory()
        cls.profile = cls.user.profile

    def test_profile_returned(self):
        returned = get_profile(fid=self.profile.fid)
        maked = make_federable_profile(self.profile)
        self.assertEqual(returned.id, maked.id)
        self.assertTrue(isinstance(returned, base.Profile))
