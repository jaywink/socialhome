from django.conf.urls import url

from socialhome.streams.views import PublicStreamView, TagStreamView

urlpatterns = [
    url(r"^public/$", PublicStreamView.as_view(), name="public"),
    url(r"^tags/(?P<name>[\w-]+)/$", TagStreamView.as_view(), name="tags"),
]
