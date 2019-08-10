from django.conf.urls import url
from django.urls import path
from django.views.decorators.csrf import csrf_exempt

from . import views

app_name = 'users'

urlpatterns = [
    url(
        regex=r"^u/(?P<username>[\w.@+-]+)/all/$",
        view=views.UserAllContentView.as_view(),
        name="all-content"
    ),
    url(
        regex=r"^u/(?P<username>[\w.@+-]+)/",
        # CSRF exempt needed for POST to work for ActivityPub object inboxes
        view=csrf_exempt(views.UserDetailView.as_view()),
        name="detail"
    ),
    url(
        regex=r"^u/~update-picture/$",
        view=views.UserPictureUpdateView.as_view(),
        name="picture-update"
    ),
    url(
        regex=r"^u/~api-token/$",
        view=views.UserAPITokenView.as_view(),
        name="api-token",
    ),
    url(
        regex=r"^p/~organize/$",
        view=views.OrganizeContentProfileDetailView.as_view(),
        name="profile-organize"
    ),
    url(
        regex=r"^p/~update/$",
        view=views.ProfileUpdateView.as_view(),
        name="profile-update"
    ),
    url(
        regex=r"^p/~following/$",
        view=views.ContactsFollowingView.as_view(),
        name="contacts-following"
    ),
    url(
        regex=r"^p/~followers/$",
        view=views.ContactsFollowersView.as_view(),
        name="contacts-followers"
    ),
    url(
        regex=r"^p/(?P<uuid>[^/]+)/all/$",
        view=views.ProfileAllContentView.as_view(),
        name="profile-all-content"
    ),
    url(
        regex=r"^p/(?P<uuid>[^/]+)/",
        view=views.ProfileDetailView.as_view(),
        name="profile-detail"
    ),
    path('delete-account/', views.DeleteAccountView.as_view(), name="delete-account"),
]
