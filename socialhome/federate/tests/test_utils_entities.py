from django.conf import settings
from django.test import override_settings, RequestFactory
from federation.entities import base

from socialhome.content.tests.factories import PublicContentFactory, SiteContentFactory, ContentFactory
from socialhome.federate.utils import (
    get_federable_object, get_profile, make_federable_profile, make_federable_retraction,
)
from socialhome.tests.utils import SocialhomeTestCase
from socialhome.users.tests.factories import UserFactory, PublicUserFactory, SiteUserFactory


class TestGetFederableObject(SocialhomeTestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.user = PublicUserFactory()
        cls.profile = cls.user.profile
        cls.site_user = SiteUserFactory()
        cls.site_profile = cls.site_user.profile
        cls.content = PublicContentFactory(author=cls.profile)
        cls.site_content = SiteContentFactory(author=cls.profile)

    def test_content_returned(self):
        request = RequestFactory().get(
            self.content.fid.replace(settings.SOCIALHOME_URL, ""),
            HTTP_HOST="127.0.0.1:8000",
        )
        content = get_federable_object(request)
        self.assertTrue(isinstance(content, base.Post))
        self.assertEqual(content.id, self.content.fid)
        self.assertEqual(content.actor_id, self.profile.fid)

    def test_content_returned__site_content(self):
        request = RequestFactory().get(
            self.site_content.fid.replace(settings.SOCIALHOME_URL, ""),
            HTTP_HOST="127.0.0.1:8000",
        )
        request.user = self.site_user
        content = get_federable_object(request)
        self.assertTrue(isinstance(content, base.Post))
        self.assertEqual(content.id, self.site_content.fid)
        self.assertEqual(content.actor_id, self.profile.fid)

    def test_content_not_returned__site_content_anonymous_user(self):
        request = RequestFactory().get(
            self.site_content.fid.replace(settings.SOCIALHOME_URL, ""),
            HTTP_HOST="127.0.0.1:8000",
        )
        content = get_federable_object(request)
        self.assertIsNone(content)

    def test_profile_not_returned__site_user_anonymous_user(self):
        request = RequestFactory().get(
            self.site_profile.fid.replace(settings.SOCIALHOME_URL, ""),
            HTTP_HOST="127.0.0.1:8000",
        )
        profile = get_federable_object(request)
        self.assertIsNone(profile)

    def test_profile_returned(self):
        request = RequestFactory().get(
            self.profile.fid.replace(settings.SOCIALHOME_URL, ""),
            HTTP_HOST="127.0.0.1:8000",
        )
        profile = get_federable_object(request)
        self.assertTrue(isinstance(profile, base.Profile))
        self.assertEqual(profile.id, self.profile.fid)

    def test_profile_returned__site_user(self):
        request = RequestFactory().get(
            self.site_profile.fid.replace(settings.SOCIALHOME_URL, ""),
            HTTP_HOST="127.0.0.1:8000",
        )
        request.user = self.user
        profile = get_federable_object(request)
        self.assertTrue(isinstance(profile, base.Profile))
        self.assertEqual(profile.id, self.site_profile.fid)

    def test_profile_returned_for_root_profile(self):
        request = RequestFactory().get("/", HTTP_HOST="127.0.0.1:8000")
        with override_settings(SOCIALHOME_ROOT_PROFILE=self.user.username):
            profile = get_federable_object(request)
        self.assertTrue(isinstance(profile, base.Profile))
        self.assertEqual(profile.id, self.profile.fid)


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


class TestMakeFederableRetraction(SocialhomeTestCase):
    @classmethod
    def setUpTestData(cls) -> None:
        super().setUpTestData()
        cls.create_local_and_remote_user()
        cls.content = ContentFactory(author=cls.remote_profile)
        cls.share = ContentFactory(share_of=cls.content, author=cls.profile)

    def test_target_id_correct_for_share(self):
        obj = make_federable_retraction(self.share, author=self.profile)
        self.assertEqual(obj.target_id, self.share.share_of.fid)
