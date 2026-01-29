from django.urls import path, re_path
from django.views.decorators.csrf import csrf_exempt

from . import views

app_name = 'users'

urlpatterns = [
    re_path(
        r"^u/(?P<username>[\w.@+-]+)/all/$",
        view=views.UserAllContentView.as_view(),
        name="all-content"
    ),
    re_path(
        r"^u/(?P<username>[\w.@+-]+)/",
        # CSRF exempt needed for POST to work for ActivityPub object inboxes
        view=csrf_exempt(views.UserDetailView.as_view()),
        name="detail"
    ),
    re_path(
        r"^u/~update-picture/$",
        view=views.UserPictureUpdateView.as_view(),
        name="picture-update"
    ),
    re_path(
        r"^u/~api-token/$",
        view=views.UserAPITokenView.as_view(),
        name="api-token",
    ),
    re_path(
        r"^p/~organize/$",
        view=views.OrganizeContentProfileDetailView.as_view(),
        name="profile-organize"
    ),
    re_path(
        r"^p/~update/$",
        view=views.ProfileUpdateView.as_view(),
        name="profile-update"
    ),
    re_path(
        r"^p/~following/$",
        view=views.ContactsFollowingView.as_view(),
        name="contacts-following"
    ),
    re_path(
        r"^p/~followers/$",
        view=views.ContactsFollowersView.as_view(),
        name="contacts-followers"
    ),
    re_path(
        r"^p/(?P<uuid>[^/]+)/all/$",
        view=views.ProfileAllContentView.as_view(),
        name="profile-all-content"
    ),
    re_path(
        r"^p/(?P<uuid>[^/]+)/",
        view=views.ProfileDetailView.as_view(),
        name="profile-detail"
    ),
    path('delete-account/', views.DeleteAccountView.as_view(), name="delete-account"),
]
