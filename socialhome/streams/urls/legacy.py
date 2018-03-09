from django.conf.urls import url

from socialhome.streams.views import PublicStreamView, TagStreamView, FollowedStreamView

# This file contains legacy versions of the stream URL's that were in effect before the changes introduced
# on 4th September 2017. Remove these if they are required for something else in the future, but notice there
# will be some content linking to these pre this change.

app_name = 'streams'

urlpatterns = [
    url(r"^followed/$", FollowedStreamView.as_view(), name="followed"),
    url(r"^public/$", PublicStreamView.as_view(), name="public"),
    url(r"^tags/(?P<name>[\w-]+)/$", TagStreamView.as_view(), name="tag"),
]
