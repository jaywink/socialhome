from braces.views import LoginRequiredMixin
from django.contrib.auth.models import AnonymousUser
from django.shortcuts import get_object_or_404
from django.views import View
from django.views.generic import ListView

from socialhome.content.models import Content, Tag
from socialhome.streams.streams import PublicStream, FollowedStream, TagStream


class StreamMixin(View):
    last_id = None
    throughs = None
    stream_class = None
    vue = False

    def dispatch(self, request, *args, **kwargs):
        use_new_stream = isinstance(request.user, AnonymousUser) or (
            hasattr(request.user, "preferences") and request.user.preferences.get("streams__use_new_stream")
        )
        use_vue_preference = bool(request.GET.get("vue", None))
        self.vue = use_vue_preference if use_vue_preference is not None else use_new_stream
        self.last_id = request.GET.get("last_id")
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        # noinspection PyUnresolvedReferences
        context = super().get_context_data(**kwargs)
        context["stream_name"] = self.stream_name
        context["throughs"] = self.throughs
        if self.vue:
            context["json_context"] = self.get_json_context()

        return context

    def get_json_context(self):
        return {
            "currentBrowsingProfileId": getattr(getattr(self.request.user, "profile", None), "id", None),
            "isUserAuthenticated": bool(self.request.user.is_authenticated),
            "streamName": self.stream_name,
        }

    def get_queryset(self):
        stream = self.stream_class(last_id=self.last_id, user=self.request.user)
        qs, self.throughs = stream.get_content()
        return qs

    def get_template_names(self):
        # noinspection PyUnresolvedReferences
        return ["streams/vue.html"] if self.vue else super().get_template_names()

    @property
    def stream_name(self):
        return self.stream_type_value

    @property
    def stream_type_value(self):
        return self.stream_class.stream_type.value


class BaseStreamView(StreamMixin, ListView):
    model = Content


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
        if self.vue:
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
