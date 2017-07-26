import haystack
from django.contrib.auth.models import AnonymousUser
from django.test import RequestFactory
from django.urls import reverse

from socialhome.enums import Visibility
from socialhome.search.views import GlobalSearchView
from socialhome.tests.utils import SocialhomeCBVTestCase, SocialhomeTestCase
from socialhome.users.tests.factories import ProfileFactory, UserFactory


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

    def test_returns_a_result(self):
        self.get("%s?q=%s" % (reverse("search:global"), "foobar"))
        self.assertResponseContains(self.public_profile.name, html=False)
        self.assertResponseContains(self.public_profile.handle, html=False)
