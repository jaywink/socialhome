from django.contrib.postgres.search import SearchVector
from django.views.generic import TemplateView

from socialhome.search.tables import ProfileSearchTable
from socialhome.users.models import Profile


class SearchView(TemplateView):
    template_name = "search/results.html"

    def dispatch(self, request, *args, **kwargs):
        self.term = request.GET.get("q")
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["profile_table"] = self.get_profile_table()
        return context

    def get_profile_table(self):
        results = Profile.objects.visible_for_user(self.request.user).annotate(
            search=SearchVector("handle", "name")
        ).filter(search__contains=self.term)
        profile_table = ProfileSearchTable(results, order_by=self.request.GET.get("sort"))
        profile_table.paginate(page=self.request.GET.get("page", 1), per_page=25)
        return profile_table
