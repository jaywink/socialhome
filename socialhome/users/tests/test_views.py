import pytest
from django.contrib.auth.models import AnonymousUser
from django.contrib.sites.shortcuts import get_current_site
from django.urls import reverse
from django.test import RequestFactory
from rest_framework.authtoken.models import Token

from socialhome.content.models import Content
from socialhome.content.tests.factories import ContentFactory, PublicContentFactory
from socialhome.enums import Visibility
from socialhome.streams.enums import StreamType
from socialhome.tests.utils import SocialhomeTestCase
from socialhome.users.models import User, Profile
from socialhome.users.tables import FollowedTable
from socialhome.users.tests.factories import (
    UserFactory, AdminUserFactory, ProfileFactory, PublicUserFactory, PublicProfileFactory)
from socialhome.users.views import (
    ProfileUpdateView, ProfileDetailView, OrganizeContentProfileDetailView, ProfileAllContentView)


class TestDeleteAccountView(SocialhomeTestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.user = UserFactory()

    def test_delete_confirm_renders(self):
        with self.login(self.user):
            self.get('users:delete-account')
        self.response_200()

    def test_delete_succeeds(self):
        with self.login(self.user):
            self.post('users:delete-account')
        self.response_302()
        self.assertTrue(User.objects.filter(id=self.user.id).exists() is False)


class TestProfileUpdateView(SocialhomeTestCase):
    def setUp(self):
        super().setUp()
        self.user = self.make_user()
        self.profile = self.user.profile
        self.factory = RequestFactory()
        self.view = ProfileUpdateView()
        request = self.factory.get('/fake-url')
        request.user = self.user
        self.view.request = request

    def test_get_success_url(self):
        # Expect: '/users/testuser/', as that is the default username for
        #   self.make_user()
        self.assertEqual(
            self.view.get_success_url(),
            '/u/testuser/'
        )

    def test_get_object(self):
        # Expect: self.user, as that is the request's user object
        self.assertEqual(
            self.view.get_object(),
            self.user.profile
        )

    def test_updates_name(self):
        with self.login(self.user):
            self.post("users:profile-update", data={
                "name": "updated name", "visibility": self.profile.visibility.value
            })
            self.response_302()
            self.profile.refresh_from_db()
            self.assertEqual(self.profile.name, "updated name")
            # Try a bad name
            self.post("users:profile-update", data={
                "name": '<script>alert("such hack");</script>', "visibility": self.profile.visibility.value
            })
            self.profile.refresh_from_db()
            self.assertEqual(self.profile.name, 'alert("such hack");')


class TestProfileDetailView(SocialhomeTestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.admin_user = AdminUserFactory()
        cls.user = PublicUserFactory()
        cls.profile = PublicProfileFactory()

    def _get_request_view_and_content(self, create_content=True, anonymous_user=False):
        request = self.client.get("/")
        request.site = get_current_site(request)
        if anonymous_user:
            request.user = AnonymousUser()
            profile = self.profile
        else:
            request.user = self.user
            profile = self.user.profile
        contents = []
        if create_content:
            contents.extend([
                ContentFactory(author=profile, order=3, pinned=True),
                ContentFactory(author=profile, order=2, pinned=True),
                ContentFactory(author=profile, order=1, pinned=True),
            ])
            Content.objects.filter(id=contents[0].id).update(order=3)
            Content.objects.filter(id=contents[1].id).update(order=2)
            Content.objects.filter(id=contents[2].id).update(order=1)
        view = ProfileDetailView(request=request, kwargs={"uuid": profile.uuid})
        view.object = profile
        view.set_object_and_data()
        return request, view, contents, profile

    def test_get_json_context(self):
        request, view, contents, profile = self._get_request_view_and_content(create_content=False)
        self.assertEqual(
            view.get_json_context(),
            {
                "currentBrowsingProfileId": profile.id,
                "streamName": view.stream_name,
                "isUserAuthenticated": True,
                "profile": {
                    "id": profile.id,
                    "uuid": profile.uuid,
                    "fid": profile.fid,
                    "followers_count": 0,
                    "following_count": profile.following.count(),
                    "handle": profile.handle,
                    "has_pinned_content": Content.objects.profile_pinned(profile, request.user).exists(),
                    "home_url": profile.home_url,
                    "image_url_large": profile.image_url_large,
                    "image_url_medium": profile.image_url_medium,
                    "image_url_small": profile.image_url_small,
                    "is_local": profile.is_local,
                    "location": profile.location,
                    "name": profile.name,
                    "nsfw": profile.nsfw,
                    "stream_type": view.profile_stream_type,
                    "url": profile.url,
                    "user_following": False,
                    "visibility": str(profile.visibility).lower(),
                },
            },
        )
        request, view, contents, profile = self._get_request_view_and_content(anonymous_user=True, create_content=False)
        self.assertEqual(
            view.get_json_context(),
            {
                "currentBrowsingProfileId": None,
                "streamName": view.stream_name,
                "isUserAuthenticated": False,
                "profile": {
                    "id": profile.id,
                    "uuid": profile.uuid,
                    "fid": profile.fid,
                    "followers_count": 0,
                    "following_count": profile.following.count(),
                    "handle": profile.handle,
                    "has_pinned_content": Content.objects.profile_pinned(profile, request.user).exists(),
                    "home_url": profile.home_url,
                    "image_url_large": profile.image_url_large,
                    "image_url_medium": profile.image_url_medium,
                    "image_url_small": profile.image_url_small,
                    "is_local": profile.is_local,
                    "location": profile.location,
                    "name": profile.name,
                    "nsfw": profile.nsfw,
                    "stream_type": view.profile_stream_type,
                    "url": profile.url,
                    "user_following": False,
                    "visibility": str(profile.visibility).lower(),
                },
            },
        )

    def test_detail_view_renders(self):
        request, view, contents, profile = self._get_request_view_and_content()
        with self.login(username=self.admin_user.username):
            response = self.client.get(profile.get_absolute_url())
        assert response.status_code == 200

    def test_stream_name(self):
        request, view, contents, profile = self._get_request_view_and_content(create_content=False)
        self.assertEqual(view.stream_type_value, StreamType.PROFILE_PINNED.value)


class TestOrganizeContentUserDetailView(SocialhomeTestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.user = PublicUserFactory()

    def _get_request_view_and_content(self, create_content=True):
        request = RequestFactory().get("/")
        request.user = self.user
        profile = self.user.profile

        contents = []
        if create_content:
            contents.extend([
                ContentFactory(author=profile, order=3, pinned=True),
                ContentFactory(author=profile, order=2, pinned=True),
                ContentFactory(author=profile, order=1, pinned=True),
            ])
            Content.objects.filter(id=contents[0].id).update(order=3)
            Content.objects.filter(id=contents[1].id).update(order=2)
            Content.objects.filter(id=contents[2].id).update(order=1)
        view = OrganizeContentProfileDetailView(request=request)
        view.profile = profile
        view.kwargs = {"uuid": profile.uuid}
        return request, view, contents, profile

    def test_view_renders(self):
        with self.login(self.user):
            self.get("users:profile-organize")
        self.response_200()

    def test_save_sort_order_updates_order(self):
        request, view, contents, profile = self._get_request_view_and_content()
        qs = view.get_queryset()
        self.assertEqual(qs[0].id, contents[2].id)
        self.assertEqual(qs[1].id, contents[1].id)
        self.assertEqual(qs[2].id, contents[0].id)
        # Run id's via str() because request.POST gives them like that
        view._save_sort_order([str(contents[0].id), str(contents[1].id), str(contents[2].id)])
        qs = view.get_queryset()
        self.assertEqual(qs[0].id, contents[0].id)
        self.assertEqual(qs[1].id, contents[1].id)
        self.assertEqual(qs[2].id, contents[2].id)

    def test_save_sort_order_skips_non_qs_contents(self):
        request, view, contents, profile = self._get_request_view_and_content()
        other_user = UserFactory()
        other_content = ContentFactory(author=other_user.profile, pinned=True)
        Content.objects.filter(id=other_content.id).update(order=100)
        view._save_sort_order([other_content.id])
        other_content.refresh_from_db()
        assert other_content.order == 100

    def test_get_success_url(self):
        request, view, contents, profile = self._get_request_view_and_content()
        assert view.get_success_url() == "/u/%s/" % profile.user.username


@pytest.mark.usefixtures("admin_user", "client")
class TestProfileVisibilityForAnonymous:
    def test_visible_to_self_profile_requires_login_for_anonymous(self, admin_user, client):
        Profile.objects.filter(user__username=admin_user.username).update(visibility=Visibility.SELF)
        response = client.get("/u/admin/")
        assert response.status_code == 302
        response = client.get("/p/%s/" % admin_user.profile.uuid)
        assert response.status_code == 302

    def test_visible_to_limited_profile_requires_login_for_anonymous(self, admin_user, client):
        Profile.objects.filter(user__username=admin_user.username).update(visibility=Visibility.LIMITED)
        response = client.get("/u/admin/")
        assert response.status_code == 302
        response = client.get("/p/%s/" % admin_user.profile.uuid)
        assert response.status_code == 302

    def test_visible_to_site_profile_requires_login_for_anonymous(self, admin_user, client):
        Profile.objects.filter(user__username=admin_user.username).update(visibility=Visibility.SITE)
        response = client.get("/u/admin/")
        assert response.status_code == 302
        response = client.get("/p/%s/" % admin_user.profile.uuid)
        assert response.status_code == 302

    def test_public_profile_doesnt_require_login(self, admin_user, client):
        Profile.objects.filter(user__username=admin_user.username).update(visibility=Visibility.PUBLIC)
        response = client.get("/u/admin/")
        assert response.status_code == 200
        response = client.get("/p/%s/" % admin_user.profile.uuid)
        assert response.status_code == 200


@pytest.mark.usefixtures("admin_client")
class TestProfileVisibilityForLoggedInUsers:
    def test_visible_to_self_profile(self, admin_client):
        admin = User.objects.get(username="admin")
        Profile.objects.filter(user__username="admin").update(visibility=Visibility.SELF)
        user = UserFactory(username="foobar")
        Profile.objects.filter(user__username="foobar").update(visibility=Visibility.SELF)
        response = admin_client.get("/u/admin/")
        assert response.status_code == 200
        response = admin_client.get("/u/foobar/")
        assert response.status_code == 403
        response = admin_client.get("/p/%s/" % admin.profile.uuid)
        assert response.status_code == 200
        response = admin_client.get("/p/%s/" % user.profile.uuid)
        assert response.status_code == 403

    def test_visible_to_limited_profile(self, admin_client):
        admin = User.objects.get(username="admin")
        Profile.objects.filter(user__username="admin").update(visibility=Visibility.LIMITED)
        user = UserFactory(username="foobar")
        Profile.objects.filter(user__username="foobar").update(visibility=Visibility.LIMITED)
        response = admin_client.get("/u/admin/")
        assert response.status_code == 200
        response = admin_client.get("/u/foobar/")
        assert response.status_code == 200
        response = admin_client.get("/p/%s/" % admin.profile.uuid)
        assert response.status_code == 200
        response = admin_client.get("/p/%s/" % user.profile.uuid)
        assert response.status_code == 200

    def test_visible_to_site_profile(self, admin_client):
        admin = User.objects.get(username="admin")
        Profile.objects.filter(user__username="admin").update(visibility=Visibility.SITE)
        user = UserFactory(username="foobar")
        Profile.objects.filter(user__username="foobar").update(visibility=Visibility.SITE)
        response = admin_client.get("/u/admin/")
        assert response.status_code == 200
        response = admin_client.get("/u/foobar/")
        assert response.status_code == 200
        response = admin_client.get("/p/%s/" % admin.profile.uuid)
        assert response.status_code == 200
        response = admin_client.get("/p/%s/" % user.profile.uuid)
        assert response.status_code == 200

    def test_visible_to_public_profile(self, admin_client):
        admin = User.objects.get(username="admin")
        Profile.objects.filter(user__username="admin").update(visibility=Visibility.PUBLIC)
        user = UserFactory(username="foobar")
        Profile.objects.filter(user__username="foobar").update(visibility=Visibility.PUBLIC)
        response = admin_client.get("/u/admin/")
        assert response.status_code == 200
        response = admin_client.get("/u/foobar/")
        assert response.status_code == 200
        response = admin_client.get("/p/%s/" % admin.profile.uuid)
        assert response.status_code == 200
        response = admin_client.get("/p/%s/" % user.profile.uuid)
        assert response.status_code == 200


class TestUserAllContentView(SocialhomeTestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.user = UserFactory()
        Profile.objects.filter(user__username=cls.user.username).update(visibility=Visibility.PUBLIC)

    def test_all_content_view_renders_right_view(self):
        response = self.get("users:all-content", username=self.user.username)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context_data.get("view").__class__, ProfileAllContentView)
        self.assertEqual(response.context_data.get("object"), self.user.profile)


class TestProfileAllContentView(SocialhomeTestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.user = PublicUserFactory()
        cls.user_content = PublicContentFactory(author=cls.user.profile)
        cls.profile = PublicProfileFactory()
        cls.profile_content = PublicContentFactory(author=cls.profile)

    def _get_request_view_and_content(self, create_content=True, anonymous_user=False):
        request = self.client.get("/")
        if anonymous_user:
            request.user = AnonymousUser()
            profile = self.profile
        else:
            request.user = self.user
            profile = self.user.profile
        contents = []
        if create_content:
            contents.extend([
                ContentFactory(author=profile, order=3, pinned=True),
                ContentFactory(author=profile, order=2, pinned=True),
                ContentFactory(author=profile, order=1, pinned=True),
            ])
            Content.objects.filter(id=contents[0].id).update(order=3)
            Content.objects.filter(id=contents[1].id).update(order=2)
            Content.objects.filter(id=contents[2].id).update(order=1)
        view = ProfileDetailView(request=request, kwargs={"uuid": profile.uuid})
        view.object = profile
        view.set_object_and_data()
        return request, view, contents, profile

    def test_get_json_context(self):
        request, view, contents, profile = self._get_request_view_and_content(create_content=False)
        self.assertEqual(
            view.get_json_context(),
            {
                "currentBrowsingProfileId": profile.id,
                "streamName": view.stream_name,
                "isUserAuthenticated": True,
                "profile": {
                    "id": profile.id,
                    "uuid": profile.uuid,
                    "fid": profile.fid,
                    "followers_count": 0,
                    "following_count": profile.following.count(),
                    "has_pinned_content": Content.objects.profile_pinned(profile, request.user).exists(),
                    "home_url": profile.home_url,
                    "image_url_large": profile.image_url_large,
                    "image_url_medium": profile.image_url_medium,
                    "image_url_small": profile.image_url_small,
                    "is_local": profile.is_local,
                    "location": profile.location,
                    "name": profile.name,
                    "nsfw": profile.nsfw,
                    "stream_type": view.profile_stream_type,
                    "url": profile.url,
                    "user_following": False,
                    "visibility": str(profile.visibility).lower(),
                },
            },
        )
        request, view, contents, profile = self._get_request_view_and_content(anonymous_user=True, create_content=False)
        self.assertEqual(
            view.get_json_context(),
            {
                "currentBrowsingProfileId": None,
                "streamName": view.stream_name,
                "isUserAuthenticated": False,
                "profile": {
                    "id": profile.id,
                    "uuid": profile.uuid,
                    "fid": profile.fid,
                    "followers_count": 0,
                    "following_count": profile.following.count(),
                    "handle": profile.handle,
                    "has_pinned_content": Content.objects.profile_pinned(profile, request.user).exists(),
                    "home_url": profile.home_url,
                    "image_url_large": profile.image_url_large,
                    "image_url_medium": profile.image_url_medium,
                    "image_url_small": profile.image_url_small,
                    "is_local": profile.is_local,
                    "location": profile.location,
                    "name": profile.name,
                    "nsfw": profile.nsfw,
                    "stream_type": view.profile_stream_type,
                    "url": profile.url,
                    "user_following": False,
                    "visibility": str(profile.visibility).lower(),
                },
            },
        )

    def test_renders_for_user(self):
        response = self.get("users:profile-all-content", uuid=self.user.profile.uuid)
        self.assertEqual(response.status_code, 200)

    def test_renders_for_remote_profile(self):
        response = self.get("users:profile-all-content", uuid=self.profile.uuid)
        self.assertEqual(response.status_code, 200)

    def test_stream_name(self):
        self.get("users:profile-all-content", uuid=self.profile.uuid)
        self.assertEqual(self.last_response.context["json_context"]["streamName"],
                         "%s__%s" % (StreamType.PROFILE_ALL.value, self.profile.id))


class TestContactsFollowedView(SocialhomeTestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.user = UserFactory()
        cls.profile = ProfileFactory()
        cls.user.profile.following.add(cls.profile)

    def test_login_required(self):
        # Not logged in, redirects to login
        self.get("users:contacts-followed")
        self.response_302()
        # Logged in
        with self.login(self.user):
            self.get("users:contacts-followed")
        self.response_200()

    def test_contains_table_object(self):
        with self.login(self.user):
            self.get("users:contacts-followed")
        self.assertTrue(isinstance(self.context["followed_table"], FollowedTable))
        self.assertContext("profile", self.user.profile)


class TestUserAPITokenView(SocialhomeTestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.user = UserFactory()

    def test_view_renders(self):
        with self.login(self.user):
            self.get("users:api-token")
        self.response_200()
        token = Token.objects.get(user=self.user)
        self.assertContext("token", token)

    def test_regenerate_token(self):
        old_token, _created = Token.objects.get_or_create(user=self.user)
        with self.login(self.user):
            self.post("users:api-token", data={"regenerate": "regenerate"}, follow=True)
        self.response_200()
        new_token = Token.objects.get(user=self.user)
        self.assertNotEqual(new_token.key, old_token.key)


class TestUserPictureUpdateView(SocialhomeTestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.user = UserFactory()

    def test_login_required_and_view_responds_with_correct_object(self):
        # Not logged in, redirects to login
        self.get("users:picture-update")
        self.response_302()
        # Logged in
        with self.login(self.user):
            self.get("users:picture-update")
        self.response_200()
        self.assertContext("user", self.user)

    def test_profile_picture_change(self):
        self.client.force_login(self.user)
        temp_image = self.get_temp_image()
        response = self.client.post(
            reverse("users:picture-update"),
            {"picture_0": temp_image, "picture_1": "0.5x0.5"},
            format="multipart",
        )
        self.assertEqual(response.status_code, 302)
        self.user.refresh_from_db()
        self.assertEqual(self.user.picture.name, temp_image.name.replace("/tmp/", "profiles/"))
