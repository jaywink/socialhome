from django.conf.urls import url

from socialhome.content import views

app_name = 'content'

urlpatterns = [
    url(r"^bookmarklet/$", views.ContentBookmarkletView.as_view(), name="bookmarklet"),
    url(r"^create/$", views.ContentCreateView.as_view(), name="create"),
    url(r"^(?P<pk>[0-9]+)/~edit/$", views.ContentUpdateView.as_view(), name="update"),
    url(r"^(?P<pk>[0-9]+)/~delete/$", views.ContentDeleteView.as_view(), name="delete"),
    url(r"^(?P<pk>[0-9]+)/~reply/$", views.ContentReplyView.as_view(), name="reply"),

    # Content detail works with three different versions
    # /content/123/  # pk
    # /content/123/slug/  # pk + slug
    # /content/abcd-edfg-ffff-aaaa/  # uuid
    url(r"^(?P<pk>[0-9]+)/$", views.ContentView.as_view(), name="view"),
    url(r"^(?P<pk>[0-9]+)/(?P<slug>[-\w]+)/$", views.ContentView.as_view(), name="view-by-slug"),
    url(r"^(?P<uuid>[^/]+)/$", views.ContentView.as_view(), name="view-by-uuid"),
]
