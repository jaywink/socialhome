from braces.views import LoginRequiredMixin
from django.shortcuts import get_object_or_404
from django.views.generic import ListView

from socialhome.content.models import Content, Tag
from socialhome.streams.streams import PublicStream, FollowedStream, TagStream


class BaseStreamView(ListView):
    last_id = None
    model = Content
    ordering = "-created"
    paginate_by = 15
    throughs = None
    stream_class = None
    vue = False

    def dispatch(self, request, *args, **kwargs):
        use_new_stream = (
            hasattr(request.user, "preferences") and request.user.preferences.get("streams__use_new_stream")
        )
        self.vue = bool(request.GET.get("vue", False)) or use_new_stream
        self.last_id = request.GET.get("last_id")
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["stream_name"] = self.stream_name
        context["throughs"] = self.throughs
        if self.vue:  # pragma: no cover
            context["json_context"] = {
                "currentBrowsingProfileId": getattr(getattr(self.request.user, "profile", None), "id", None),
                "streamName": self.stream_name,
                "isUserAuthenticated": bool(self.request.user.is_authenticated),
            }

        return context

    def get_queryset(self):
        stream = self.stream_class(last_id=self.last_id, user=self.request.user)
        qs, self.throughs = stream.get_content()
        return qs

    def get_template_names(self):
        return ["streams/vue.html"] if self.vue else super().get_template_names()

    @property
    def stream_name(self):
        return self.stream_type_value

    @property
    def stream_type_value(self):
        return self.stream_class.stream_type.value


class PublicStreamView(BaseStreamView):
    template_name = "streams/public.html"
    stream_class = PublicStream


class TagStreamView(BaseStreamView):
    stream_class = TagStream
    template_name = "streams/tag.html"

    def dispatch(self, request, *args, **kwargs):
        self.tag = get_object_or_404(Tag, name=kwargs.get("name"))
        return super().dispatch(request, *args, **kwargs)

    def get_queryset(self):
        stream = self.stream_class(last_id=self.last_id, user=self.request.user, tag=self.tag)
        qs, self.throughs = stream.get_content()
        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["tag_name"] = self.tag.name
        if self.vue:  # pragma: no cover
            context["json_context"]["tagName"] = self.tag.name
        return context

    @property
    def stream_name(self):
        return "%s__%s" % (self.stream_type_value, self.tag.channel_group_name)


class FollowedStreamView(LoginRequiredMixin, BaseStreamView):
    stream_class = FollowedStream
    template_name = "streams/followed.html"

    @property
    def stream_name(self):
        return "%s__%s" % (self.stream_type_value, self.request.user.username)
