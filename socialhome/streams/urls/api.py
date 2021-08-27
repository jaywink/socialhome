from django.conf.urls import url

from socialhome.streams.viewsets import (
    FollowedStreamAPIView, PublicStreamAPIView, TagStreamAPIView, ProfileAllStreamAPIView, ProfilePinnedStreamAPIView,
    LimitedStreamAPIView, LocalStreamAPIView, TagsStreamAPIView)

app_name = 'streams'

urlpatterns = [
    url(r"^followed/$", FollowedStreamAPIView.as_view(), name="followed"),
    url(r"^limited/$", LimitedStreamAPIView.as_view(), name="limited"),
    url(r"^local/$", LocalStreamAPIView.as_view(), name="local"),
    url(r"^profile-all/(?P<uuid>[0-9a-f-]+)/$", ProfileAllStreamAPIView.as_view(), name="profile-all"),
    url(r"^profile-pinned/(?P<uuid>[0-9a-f-]+)/$", ProfilePinnedStreamAPIView.as_view(), name="profile-pinned"),
    url(r"^public/$", PublicStreamAPIView.as_view(), name="public"),
    url(r"^tag/uuid-(?P<uuid>[^/]+)/$", TagStreamAPIView.as_view(), name="tag-by-uuid"),
    url(r"^tag/(?P<name>[\w-]+)/$", TagStreamAPIView.as_view(), name="tag"),
    url(r"^tags/$", TagsStreamAPIView.as_view(), name="tags"),
]
