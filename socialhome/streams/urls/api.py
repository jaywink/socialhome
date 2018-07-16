from django.conf.urls import url

from socialhome.streams.viewsets import (
    FollowedStreamAPIView, PublicStreamAPIView, TagStreamAPIView, ProfileAllStreamAPIView, ProfilePinnedStreamAPIView,
    LimitedStreamAPIView, LocalStreamAPIView)

app_name = 'streams'

urlpatterns = [
    url(r"^followed/$", FollowedStreamAPIView.as_view(), name="followed"),
    url(r"^limited/$", LimitedStreamAPIView.as_view(), name="limited"),
    url(r"^local/$", LocalStreamAPIView.as_view(), name="local"),
    url(r"^profile-all/(?P<id>[0-9]+)/$", ProfileAllStreamAPIView.as_view(), name="profile-all"),
    url(r"^profile-pinned/(?P<id>[0-9]+)/$", ProfilePinnedStreamAPIView.as_view(), name="profile-pinned"),
    url(r"^public/$", PublicStreamAPIView.as_view(), name="public"),
    url(r"^tag/(?P<name>[\w-]+)/$", TagStreamAPIView.as_view(), name="tag"),
]
