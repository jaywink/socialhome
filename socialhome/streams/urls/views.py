from django.urls import re_path

from socialhome.streams.views import (
    PublicStreamView, TagStreamView, FollowedStreamView, LimitedStreamView, LocalStreamView, TagsStreamView)

app_name = 'streams'

urlpatterns = [
    re_path(r"^followed/$", FollowedStreamView.as_view(), name="followed"),
    re_path(r"^limited/$", LimitedStreamView.as_view(), name="limited"),
    re_path(r"^local/$", LocalStreamView.as_view(), name="local"),
    re_path(r"^public/$", PublicStreamView.as_view(), name="public"),
    re_path(r"^tag/uuid-(?P<uuid>[^/]+)/$", TagStreamView.as_view(), name="tag-by-uuid"),
    re_path(r"^tag/(?P<name>[\w-]+)/$", TagStreamView.as_view(), name="tag"),
    re_path(r"^tags/$", TagsStreamView.as_view(), name="tags"),
]
