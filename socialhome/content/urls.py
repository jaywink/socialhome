from django.conf.urls import url

from socialhome.content.views import ContentCreate

urlpatterns = [
    url(r"^create/(?P<location>[\w]+)$", ContentCreate.as_view(), name="create"),
]
