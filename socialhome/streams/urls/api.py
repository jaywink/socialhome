from django.conf.urls import url

from socialhome.streams.viewsets import FollowedStreamAPIView, PublicStreamAPIView, TagStreamAPIView

urlpatterns = [
    url(r"^followed/$", FollowedStreamAPIView.as_view(), name="followed"),
    url(r"^public/$", PublicStreamAPIView.as_view(), name="public"),
    url(r"^tag/(?P<name>[\w-]+)/$", TagStreamAPIView.as_view(), name="tag"),
]
