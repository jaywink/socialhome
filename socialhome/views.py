from django.conf import settings
from django.shortcuts import get_object_or_404
from django.views.generic import TemplateView

from socialhome.streams.views import FollowedStreamView, PublicStreamView
from socialhome.users.models import Profile
from socialhome.users.views import ProfileDetailView, ProfileAllContentView


class HomeView(TemplateView):
    template_name = "pages/home.html"

    def get(self, request, *args, **kwargs):
        """Redirect to user detail view if root page is a profile or if the user is logged in"""
        if request.user.is_authenticated:
            landing_page = request.user.preferences.get("generic__landing_page")
            if landing_page == "profile":
                return ProfileDetailView.as_view()(request, guid=request.user.profile.guid)
            elif landing_page == "profile_all":
                return ProfileAllContentView.as_view()(request, guid=request.user.profile.guid)
            elif landing_page == "followed":
                return FollowedStreamView.as_view()(request)
            elif landing_page == "public":
                return PublicStreamView.as_view()(request)
            else:
                # Fallback to profile view
                return ProfileDetailView.as_view()(request, guid=request.user.profile.guid)
        if settings.SOCIALHOME_ROOT_PROFILE:
            profile = get_object_or_404(Profile, user__username=settings.SOCIALHOME_ROOT_PROFILE)
            return ProfileDetailView.as_view()(request, guid=profile.guid)
        return super(HomeView, self).get(request, *args, **kwargs)
