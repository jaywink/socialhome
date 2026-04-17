from django.urls import re_path
from django.views import View
from django.views.decorators.csrf import csrf_exempt

from socialhome.users.views import UserDetailView

app_name = 'users'

urlpatterns = [
    re_path(
        r"^u/(?P<username>[\w.@+-]+)/",
        # CSRF exempt needed for POST to work for ActivityPub object inboxes
        view=csrf_exempt(UserDetailView.as_view()),
        name="detail"
    ),
    re_path(
        r"^p/(?P<uuid>[^/]+)/",
        view=View.as_view(),
        name="profile-detail"
    ),
]
