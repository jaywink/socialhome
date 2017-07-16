from braces.views import LoginRequiredMixin
from django.shortcuts import get_object_or_404
from django.views.generic import ListView

from socialhome.content.models import Content, Tag


class BaseStreamView(ListView):
    model = Content
    ordering = "-created"
    paginate_by = 30
    stream_name = ""
    vue = False

    def dispatch(self, request, *args, **kwargs):
        self.vue = bool(request.GET.get("vue", False))
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["stream_name"] = self.stream_name
        return context

    def get_template_names(self):
        return ["streams/vue.html"] if self.vue else super().get_template_names()


class PublicStreamView(BaseStreamView):
    template_name = "streams/public.html"
    queryset = Content.objects.public()
    stream_name = "public"


class TagStreamView(BaseStreamView):
    template_name = "streams/tag.html"

    def dispatch(self, request, *args, **kwargs):
        self.tag = get_object_or_404(Tag, name=kwargs.get("name"))
        self.stream_name = "tags__%s" % self.tag.channel_group_name
        return super().dispatch(request, *args, **kwargs)

    def get_queryset(self):
        """Restrict to a tag."""
        return Content.objects.tags(self.tag, self.request.user)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["tag_name"] = self.tag.name
        return context


class FollowedStreamView(LoginRequiredMixin, BaseStreamView):
    template_name = "streams/followed.html"

    def dispatch(self, request, *args, **kwargs):
        self.stream_name = "followed__%s" % request.user.username
        return super().dispatch(request, *args, **kwargs)

    def get_queryset(self):
        return Content.objects.followed(self.request.user)
