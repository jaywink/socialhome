from django.urls import re_path

from socialhome.content import views

app_name = 'content'

urlpatterns = [
    re_path(r"^bookmarklet/$", views.ContentCreateView.as_view(), name="bookmarklet"),
    re_path(r"^create/$", views.ContentCreateView.as_view(), name="create"),
    re_path(r"^(?P<pk>[0-9]+)/~edit/$", views.ContentUpdateView.as_view(), name="update"),
    re_path(r"^(?P<pk>[0-9]+)/~delete/$", views.ContentDeleteView.as_view(), name="delete"),
    re_path(r"^(?P<pk>[0-9]+)/~reply/$", views.ContentReplyView.as_view(), name="reply"),

    # Content detail works with three different versions
    # /content/123/  # pk
    # /content/123/slug/  # pk + slug
    # /content/abcd-edfg-ffff-aaaa/  # uuid
    re_path(r"^(?P<pk>[0-9]+)/$", views.ContentView.as_view(), name="view"),
    re_path(r"^(?P<pk>[0-9]+)/(?P<slug>[-\w]+)/$", views.ContentView.as_view(), name="view-by-slug"),
    re_path(r"^(?P<uuid>[^/]+)/$", views.ContentView.as_view(), name="view-by-uuid"),
]
