import xml

from django.core.exceptions import ValidationError
from django.core.validators import validate_email
from django.shortcuts import redirect
from django.urls import reverse
from federation.fetchers import retrieve_remote_profile
from haystack.generic_views import SearchView

from socialhome.content.utils import safe_text
from socialhome.enums import Visibility
from socialhome.users.models import Profile


class GlobalSearchView(SearchView):
    def get_queryset(self):
        """Exclude some information from the queryset.

        If logged in, exclude own profile and SELF+LIMITED profiles
        If not logged in, exclude all but PUBLIC profiles

        We exclude SELF profiles too, though they should never even be indexed.
        """
        queryset = super().get_queryset()
        return self.filter_queryset(queryset)

    def get(self, request, *args, **kwargs):
        """See if we have a direct match. If so redirect, if not, search.

        Try fetching a remote profile if the search term is a handle.
        """
        try:
            q = safe_text(request.GET.get("q"))
            if q:
                q = q.strip().lower()
            validate_email(q)
        except ValidationError:
            pass
        else:
            profile = None
            try:
                profile = Profile.objects.visible_for_user(request.user).get(handle=q)
            except Profile.DoesNotExist:
                # Try a remote search
                try:
                    remote_profile = retrieve_remote_profile(q)
                except (AttributeError, ValueError, xml.parsers.expat.ExpatError):
                    # Catch various errors parsing the remote profile
                    return super().get(request, *args, **kwargs)
                if remote_profile:
                    profile = Profile.from_remote_profile(remote_profile)
            if profile:
                return redirect(reverse("users:profile-detail", kwargs={"guid": profile.guid}))
        return super().get(request, *args, **kwargs)

    def filter_queryset(self, queryset):
        """Do some of our own filtering on the queryset before returning."""
        if self.request.user.is_authenticated:
            queryset = queryset.exclude(handle=self.request.user.profile.handle)
            if self.request.user.is_staff:
                return queryset
            else:
                # TODO: LIMITED profiles are excluded from searches even though the user might already be following
                # one of them. This is an unfortunate issue that should be tackled at some point, to allow searching for
                # LIMITED profiles that the user has a follow relationship with.
                return queryset.exclude(profile_visibility__in=[
                    Visibility.SELF.value, Visibility.LIMITED.value
                ])
        return queryset.exclude(profile_visibility__in=[
            Visibility.LIMITED.value, Visibility.SITE.value, Visibility.SELF.value
        ])
