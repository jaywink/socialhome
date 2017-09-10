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
        if self.vue:  # pragma: no cover
            context["json_context"] = self._define_context_json(self.stream_name)
        return context

    def _define_context_json(self, stream_name):  # pragma: no cover
        request_user_profile = getattr(self.request.user, "profile", None)

        def dump_content(content):
            is_user_author = (content.author == request_user_profile)
            return {
                "htmlSafe": content.rendered,
                "author": {
                    "guid": content.author.guid,
                    "name": content.author.name if content.author.name else content.author.handle,
                    "handle": content.author.handle,
                    "imageUrlSmall": content.author.safer_image_url_small,
                    "absoluteUrl": content.author.get_absolute_url(),
                    "homeUrl": content.author.home_url,
                    "isUserFollowingAuthor": (content.author.id in getattr(request_user_profile, "following_ids", []))
                },
                "id": content.id,
                "timestamp": content.timestamp,
                "humanizedTimestamp": content.humanized_timestamp,
                "edited": bool(content.edited),
                "repliesCount": content.reply_count,
                "sharesCount": content.shares_count,
                "isUserLocal": bool(content.author.user),
                "contentUrl": content.get_absolute_url(),
                "isUserAuthor": is_user_author,
                "hasShared": Content.has_shared(content.id, request_user_profile.id) if request_user_profile else False,
            }

        return {
            "contentList": [dump_content(content) for content in self.get_queryset()[:self.paginate_by]],
            "currentBrowsingProfileId": getattr(request_user_profile, "id", None),
            "streamName": stream_name,
            "isUserAuthenticated": bool(self.request.user.is_authenticated),
        }

    def get_queryset(self):
        stream = self.stream_class(last_id=self.last_id, user=self.request.user)
        return stream.get_content()

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
        return stream.get_content()

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
