from django.urls import re_path

from socialhome.search.views import GlobalSearchView

app_name = 'search'

urlpatterns = [
    re_path(r"", GlobalSearchView.as_view(), name="global"),
]
