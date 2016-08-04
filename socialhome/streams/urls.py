from django.conf.urls import url

from socialhome.streams.views import PublicStreamView

urlpatterns = [
    url(r"^public/$", PublicStreamView.as_view(), name="public"),
]
