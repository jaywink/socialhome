from haystack.generic_views import SearchView


class GlobalSearchView(SearchView):
    def get_queryset(self):
        queryset = super().get_queryset()
        if self.request.user.is_authenticated:
            return queryset.exclude(handle=self.request.user.profile.handle)
        return queryset
