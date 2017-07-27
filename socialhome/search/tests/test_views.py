from unittest.mock import patch
from uuid import uuid4

import haystack
from django.contrib.auth.models import AnonymousUser
from django.test import RequestFactory
from django.urls import reverse
from federation.entities import base

from socialhome.enums import Visibility
from socialhome.search.views import GlobalSearchView
from socialhome.tests.utils import SocialhomeCBVTestCase, SocialhomeTestCase
from socialhome.users.models import Profile
from socialhome.users.tests.factories import ProfileFactory, UserFactory
from socialhome.users.views import ProfileAllContentView


class TestGlobalSearchViewQuerySet(SocialhomeCBVTestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        haystack.connections['default'].get_backend().clear()
        cls.self_profile = ProfileFactory(visibility=Visibility.SELF)
        cls.public_profile = ProfileFactory(visibility=Visibility.PUBLIC)
        cls.limited_profile = ProfileFactory(visibility=Visibility.LIMITED)
        cls.site_profile = ProfileFactory(visibility=Visibility.SITE)
        cls.staff_user = UserFactory(is_staff=True)
        cls.normal_user = UserFactory()

    def test_profile_visibility_authenticated_user(self):
        request = RequestFactory().get('/')
        request.user = self.normal_user
        view = self.get_instance(GlobalSearchView, request=request)
        queryset_pks = view.get_queryset().values_list("pk", flat=True)
        self.assertEqual(
            set(queryset_pks),
            {str(self.public_profile.pk), str(self.site_profile.pk)},
        )

    def test_profile_visibility_authenticated_staff_user(self):
        request = RequestFactory().get('/')
        request.user = self.staff_user
        view = self.get_instance(GlobalSearchView, request=request)
        queryset_pks = view.get_queryset().values_list("pk", flat=True)
        self.assertEqual(
            set(queryset_pks),
            {str(self.public_profile.pk), str(self.site_profile.pk), str(self.limited_profile.pk)},
        )

    def test_profile_visibility_anonymous_user(self):
        request = RequestFactory().get('/')
        request.user = AnonymousUser()
        view = self.get_instance(GlobalSearchView, request=request)
        queryset_pks = view.get_queryset().values_list("pk", flat=True)
        self.assertEqual(
            set(queryset_pks), {str(self.public_profile.pk)},
        )


class TestGlobalSearchView(SocialhomeTestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.public_profile = ProfileFactory(name="Foobar", visibility=Visibility.PUBLIC)

    def test_view_renders(self):
        self.get("search:global")
        self.response_200()
        self.assertResponseContains("Search", html=False)

    def test_returns_a_result(self):
        self.get("%s?q=%s" % (reverse("search:global"), "foobar"))
        self.assertResponseContains("Results", html=False)
        self.assertResponseContains(self.public_profile.name, html=False)
        self.assertResponseContains(self.public_profile.username_part, html=False)

    def test_direct_profile_match_goes_to_profile_view(self):
        self.get("%s?q=%s" % (reverse("search:global"), self.public_profile.handle), follow=True)
        self.assertResponseNotContains("Results", html=False)
        self.assertEqual(self.context["view"].__class__, ProfileAllContentView)
        self.assertEqual(self.context["object"], self.public_profile)

    @patch("socialhome.search.views.retrieve_remote_profile")
    def test_search_by_handle_fetches_unknown_profile(self, mock_retrieve):
        guid = str(uuid4())
        mock_retrieve.return_value = base.Profile(
            name="I don't exist locally",
            handle="i-dont-exist-locally@example.com",
            guid=guid,
            public=True,
        )
        self.get("%s?q=%s" % (reverse("search:global"), "i-dont-exist-locally@example.com"), follow=True)
        profile = Profile.objects.get(guid=guid)
        self.assertResponseNotContains("Results", html=False)
        self.assertEqual(self.context["view"].__class__, ProfileAllContentView)
        self.assertEqual(self.context["object"], profile)
