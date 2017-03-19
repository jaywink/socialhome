from django.conf.urls import url

from socialhome.content.views import ContentCreateView, ContentUpdateView, ContentDeleteView, ContentView

urlpatterns = [
    url(r"^create/$", ContentCreateView.as_view(), name="create"),
    url(r"^(?P<pk>[0-9]+)/~edit/$", ContentUpdateView.as_view(), name="update"),
    url(r"^(?P<pk>[0-9]+)/~delete/$", ContentDeleteView.as_view(), name="delete"),

    # Content detail works with three different versions
    # /content/123/  # pk
    # /content/123/slug/  # pk + slug
    # /content/abcd-edfg-ffff-aaaa/  # guid
    url(r"^(?P<pk>[0-9]+)/$", ContentView.as_view(), name="view"),
    url(r"^(?P<pk>[0-9]+)/(?P<slug>[-\w]+)/$", ContentView.as_view(), name="view-by-slug"),
    url(r"^(?P<guid>[^/]+)/$", ContentView.as_view(), name="view-by-guid"),
]
