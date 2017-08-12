from django.conf.urls import url

from . import views

urlpatterns = [
    url(
        regex=r"^u/$",
        view=views.UserListView.as_view(),
        name="list"
    ),
    url(
        regex=r"^u/(?P<username>[\w.@+-]+)/all/$",
        view=views.UserAllContentView.as_view(),
        name="all-content"
    ),
    url(
        regex=r"^u/(?P<username>[\w.@+-]+)/$",
        view=views.UserDetailView.as_view(),
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
        regex=r"^p/(?P<guid>[^/]+)/all/$",
        view=views.ProfileAllContentView.as_view(),
        name="profile-all-content"
    ),
    url(
        regex=r"^p/(?P<guid>[^/]+)/$",
        view=views.ProfileDetailView.as_view(),
        name="profile-detail"
    ),
    url(
        regex=r"^contacts/$",
        view=views.ContactsFollowedView.as_view(),
        name="contacts-followed"
    ),
]
