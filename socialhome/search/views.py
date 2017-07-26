from haystack.generic_views import SearchView

from socialhome.enums import Visibility


class GlobalSearchView(SearchView):
    def get_queryset(self):
        """Exclude some information from the queryset.

        If logged in, exclude own profile.
        If not logged in, exclude SITE visibility objects.
        """
        queryset = super().get_queryset()
        if self.request.user.is_authenticated:
            return queryset.exclude(handle=self.request.user.profile.handle)
        return queryset.filter(visibility=Visibility.PUBLIC)
