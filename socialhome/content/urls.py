from django.conf.urls import url

from socialhome.content.views import ContentCreateView, ContentUpdateView, ContentDeleteView

urlpatterns = [
    url(r"^create/(?P<location>[\w]+)$", ContentCreateView.as_view(), name="create"),
    url(r"^edit/(?P<pk>[0-9]+)$", ContentUpdateView.as_view(), name="update"),
    url(r"^delete/(?P<pk>[0-9]+)$", ContentDeleteView.as_view(), name="delete"),
]
