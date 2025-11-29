from django.urls import re_path

from socialhome.streams.viewsets import (
    FollowedStreamAPIView, PublicStreamAPIView, TagStreamAPIView, ProfileAllStreamAPIView, ProfilePinnedStreamAPIView,
    LimitedStreamAPIView, LocalStreamAPIView, TagsStreamAPIView)

app_name = 'streams'

urlpatterns = [
    re_path(r"^followed/$", FollowedStreamAPIView.as_view(), name="followed"),
    re_path(r"^limited/$", LimitedStreamAPIView.as_view(), name="limited"),
    re_path(r"^local/$", LocalStreamAPIView.as_view(), name="local"),
    re_path(r"^profile-all/(?P<uuid>[0-9a-f-]+)/$", ProfileAllStreamAPIView.as_view(), name="profile-all"),
    re_path(r"^profile-pinned/(?P<uuid>[0-9a-f-]+)/$", ProfilePinnedStreamAPIView.as_view(), name="profile-pinned"),
    re_path(r"^public/$", PublicStreamAPIView.as_view(), name="public"),
    re_path(r"^tag/uuid-(?P<uuid>[^/]+)/$", TagStreamAPIView.as_view(), name="tag-by-uuid"),
    re_path(r"^tag/(?P<name>[\w-]+)/$", TagStreamAPIView.as_view(), name="tag"),
    re_path(r"^tags/$", TagsStreamAPIView.as_view(), name="tags"),
]
