from django.conf.urls import url

from socialhome.streams.views import (
    PublicStreamView, TagStreamView, FollowedStreamView, LimitedStreamView, LocalStreamView, TagsStreamView)

app_name = 'streams'

urlpatterns = [
    url(r"^followed/$", FollowedStreamView.as_view(), name="followed"),
    url(r"^limited/$", LimitedStreamView.as_view(), name="limited"),
    url(r"^local/$", LocalStreamView.as_view(), name="local"),
    url(r"^public/$", PublicStreamView.as_view(), name="public"),
    url(r"^tag/uuid-(?P<uuid>[^/]+)/$", TagStreamView.as_view(), name="tag-by-uuid"),
    url(r"^tag/(?P<name>[\w-]+)/$", TagStreamView.as_view(), name="tag"),
    url(r"^tags/$", TagsStreamView.as_view(), name="tags"),
]
