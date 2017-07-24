from django.conf.urls import url

from socialhome.search.views import GlobalSearchView

urlpatterns = [
    url(r"", GlobalSearchView.as_view(), name="global"),
]
