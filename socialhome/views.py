from django.conf import settings
from django.shortcuts import get_object_or_404
from django.views.generic import TemplateView

from socialhome.users.models import Profile
from socialhome.users.views import ProfileDetailView


class HomeView(TemplateView):
    template_name = "pages/home.html"

    def get(self, request, *args, **kwargs):
        """Redirect to user detail view if root page is a profile or if the user is logged in"""
        if request.user.is_authenticated:
            return ProfileDetailView.as_view()(request, guid=request.user.profile.guid)
        if settings.SOCIALHOME_ROOT_PROFILE:
            profile = get_object_or_404(Profile, user__username=settings.SOCIALHOME_ROOT_PROFILE)
            return ProfileDetailView.as_view()(request, guid=profile.guid)
        return super(HomeView, self).get(request, *args, **kwargs)
