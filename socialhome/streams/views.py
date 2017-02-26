from django.views.generic import ListView

from socialhome.content.models import Content, Tag
from socialhome.enums import Visibility


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
    queryset = Content.objects.filter(visibility=Visibility.PUBLIC).select_related("oembed", "opengraph")
    stream_name = "public"


class TagStreamView(BaseStreamView):
    template_name = "streams/tag.html"
    # TODO: support non-public content via visibility checks
    queryset = Content.objects.filter(visibility=Visibility.PUBLIC).select_related("oembed", "opengraph")

    def dispatch(self, request, *args, **kwargs):
        self.stream_name = "tags/%s" % kwargs.get("name")
        return super().dispatch(request, *args, **kwargs)

    def get_queryset(self):
        """Restrict to a tag."""
        try:
            tag = Tag.objects.get_by_cleaned_name(self.kwargs.get("name"))
        except Tag.DoesNotExist:
            return Content.objects.none()
        qs = super().get_queryset()
        return qs.filter(tags=tag)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["tag_name"] = self.kwargs.get("name")
        return context
