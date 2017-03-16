from django.conf.urls import url

from socialhome.content.views import ContentCreateView, ContentUpdateView, ContentDeleteView, ContentView

urlpatterns = [
    url(r"^(?P<pk>[0-9]+)$", ContentView.as_view(), name="view"),
    url(r"^(?P<guid>[^/]+)$", ContentView.as_view(), name="view-by-guid"),
    url(r"^create/$", ContentCreateView.as_view(), name="create"),
    url(r"^edit/(?P<pk>[0-9]+)$", ContentUpdateView.as_view(), name="update"),
    url(r"^delete/(?P<pk>[0-9]+)$", ContentDeleteView.as_view(), name="delete"),
]
