from haystack.generic_views import SearchView

from socialhome.enums import Visibility


class GlobalSearchView(SearchView):
    def get_queryset(self):
        """Exclude some information from the queryset.

        If logged in, exclude own profile and SELF+LIMITED profiles
        If not logged in, exclude all but PUBLIC profiles

        We exclude SELF profiles too, though they should never even be indexed.
        """
        queryset = super().get_queryset()
        return self.filter_queryset(queryset)

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
