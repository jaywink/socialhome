from django.conf.urls import url

from socialhome.streams.views import PublicStreamView, TagStreamView, FollowedStreamView

urlpatterns = [
    url(r"^followed/$", FollowedStreamView.as_view(), name="followed"),
    url(r"^public/$", PublicStreamView.as_view(), name="public"),
    url(r"^tag/(?P<name>[\w-]+)/$", TagStreamView.as_view(), name="tag"),
]
