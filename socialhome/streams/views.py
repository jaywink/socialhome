from django.views.generic import ListView

from socialhome.content.models import Content


class BaseStreamView(ListView):
    model = Content
    ordering = "-created"
    paginate_by = 30
    stream_name = ""

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["stream_name"] = self.stream_name
        return context


class PublicStreamView(BaseStreamView):
    template_name = "streams/public.html"
    queryset = Content.objects.public()
    stream_name = "public"


class TagStreamView(BaseStreamView):
    template_name = "streams/tag.html"

    def dispatch(self, request, *args, **kwargs):
        self.stream_name = "tags__%s" % kwargs.get("name")
        return super().dispatch(request, *args, **kwargs)

    def get_queryset(self):
        """Restrict to a tag."""
        return Content.objects.tags(self.kwargs.get("name"), self.request.user)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["tag_name"] = self.kwargs.get("name")
        return context
