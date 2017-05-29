from django.conf.urls import url

from . import views

urlpatterns = [
    url(
        regex=r"^u/$",
        view=views.UserListView.as_view(),
        name="list"
    ),
    url(
        regex=r"^u/~redirect/$",
        view=views.UserRedirectView.as_view(),
        name="redirect"
    ),
    url(
        regex=r"^u/(?P<username>[\w.@+-]+)/$",
        view=views.UserDetailView.as_view(),
        name="detail"
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
        regex=r"^p/(?P<guid>[^/]+)/$",
        view=views.ProfileDetailView.as_view(),
        name="profile-detail"
    ),
]
