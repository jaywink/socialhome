from django.conf.urls import url

from socialhome.streams.views import (
    PublicStreamView, TagStreamView, FollowedStreamView, LimitedStreamView, LocalStreamView)

app_name = 'streams'

urlpatterns = [
    url(r"^followed/$", FollowedStreamView.as_view(), name="followed"),
    url(r"^limited/$", LimitedStreamView.as_view(), name="limited"),
    url(r"^local/$", LocalStreamView.as_view(), name="local"),
    url(r"^public/$", PublicStreamView.as_view(), name="public"),
    url(r"^tag/(?P<name>[\w-]+)/$", TagStreamView.as_view(), name="tag"),
]
