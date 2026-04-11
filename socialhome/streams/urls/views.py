from django.urls import re_path
from django.views import View

app_name = 'streams'

urlpatterns = [
    re_path(r"^tag/uuid-(?P<uuid>[^/]+)/$", View.as_view(), name="tag-by-uuid"),
    re_path(r"^tag/(?P<name>[\w-]+)/$", View.as_view(), name="tag"),
    re_path(r"^tags/$", View.as_view(), name="tags"),
]
