from unittest.mock import patch

import haystack
from django.contrib.auth.models import AnonymousUser
from django.test import RequestFactory
from django.urls import reverse
from federation.entities import base
from federation.utils.diaspora import parse_profile_diaspora_id

from socialhome.content.tests.factories import ContentFactory
from socialhome.enums import Visibility
from socialhome.search.views import GlobalSearchView
from socialhome.streams.views import TagStreamView
from socialhome.tests.utils import SocialhomeCBVTestCase, SocialhomeTestCase
from socialhome.users.models import Profile
from socialhome.users.tests.factories import ProfileFactory, UserFactory, PublicProfileFactory, BaseProfileFactory
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
        cls.public_profile = PublicProfileFactory(name="Foobar", diaspora=True)
        cls.content = ContentFactory(text='#barfoo')
        cls.tag = cls.content.tags.first()

    def test_view_renders(self):
        self.get("search:global")
        self.response_200()
        self.assertResponseContains("Search", html=False)

    def test_returns_a_result__profile(self):
        self.get("%s?q=%s" % (reverse("search:global"), "foobar"))
        self.assertResponseContains("Profiles", html=False)
        self.assertResponseContains(self.public_profile.name, html=False)
        self.assertResponseContains(self.public_profile.username_part, html=False)

    def test_returns_a_result__tag(self):
        self.get("%s?q=%s" % (reverse("search:global"), "barfoo"))
        self.assertResponseContains("Tags", html=False)
        self.assertResponseContains(self.tag.name, html=False)

    def test_direct_profile_match_goes_to_profile_view(self):
        handle, _guid = parse_profile_diaspora_id(self.public_profile.fid)
        self.get("%s?q=%s" % (reverse("search:global"), handle), follow=True)
        self.assertResponseNotContains("Profiles", html=False)
        self.assertEqual(self.context["view"].__class__, ProfileAllContentView)
        self.assertEqual(self.context["object"], self.public_profile)

    def test_direct_tag_match_goes_to_tag_stream(self):
        self.get("%s?q=%s" % (reverse("search:global"), '%23barfoo'), follow=True)
        self.assertResponseNotContains("Tags", html=False)
        self.assertEqual(self.context["view"].__class__, TagStreamView)
        self.assertEqual(self.context["name"], self.tag.name)

    @patch("socialhome.search.views.retrieve_remote_profile", autospec=True)
    def test_search_by_handle_fetches_unknown_profile(self, mock_retrieve):
        fid = "diaspora://i-dont-exist-locally@example.com/profile/1234"
        mock_retrieve.return_value = base.Profile(
            name="I don't exist locally",
            id=fid,
            public=True,
        )
        self.get("%s?q=%s" % (reverse("search:global"), "i-dont-exist-locally@example.com"), follow=True)
        profile = Profile.objects.get(fid=fid)
        self.assertResponseNotContains("Profiles", html=False)
        self.assertEqual(self.context["view"].__class__, ProfileAllContentView)
        self.assertEqual(self.context["object"], profile)

        # Survives extra spaces around
        self.get("%s?q=%s" % (reverse("search:global"), "%20i-dont-exist-locally@example.com%20"), follow=True)
        self.assertResponseNotContains("Profiles", html=False)
        self.assertEqual(self.context["view"].__class__, ProfileAllContentView)
        self.assertEqual(self.context["object"], profile)

    @patch("socialhome.search.views.retrieve_remote_profile", autospec=True)
    def test_search_by_handle_lowercases_before_fetching(self, mock_retrieve):
        mock_retrieve.return_value = BaseProfileFactory()
        self.get("%s?q=%s" % (reverse("search:global"), "i-dont-EXIST-locally@eXample.com"), follow=True)
        mock_retrieve.assert_called_once_with("diaspora://i-dont-exist-locally@example.com/profile/")
