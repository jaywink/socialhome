from braces.views import LoginRequiredMixin
from django.shortcuts import get_object_or_404
from django.utils.translation import gettext
from django.views.generic import ListView
from django.urls import reverse

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
                    "isUserFollowingAuthor": (
                        content.author.id in getattr(request_user_profile, "following_ids", []))
                },
                "id": content.id,
                "timestamp": content.formatted_timestamp,
                "humanizedTimestamp": content.humanized_timestamp,
                "edited": bool(content.edited),
                "childrenCount": content.children.count(),
                "isUserLocal": bool(content.author.user),
                "contentUrl": content.get_absolute_url(),
                "isUserAuthor": is_user_author,
                "updateUrl": reverse("content:update", kwargs={"pk": content.id}) if is_user_author else "",
                "replyUrl": reverse("content:reply", kwargs={"pk": content.id}) if is_user_author else "",
                "deleteUrl": reverse("content:reply", kwargs={"pk": content.id}) if is_user_author else ""
            }

        return {
            "contentList": [dump_content(content) for content in self.queryset[:self.paginate_by]],
            "currentBrowsingProfileId": getattr(request_user_profile, "id", ""),
            "streamName": stream_name,
            "isUserAuthentificated": bool(self.request.user.is_authenticated),
            "showAuthorBar": not stream_name.startswith("profile_"),
            "translations": {
                "stampedContent": {
                    "h2": gettext("Public"),
                    "p": gettext("Contains public content from around the network.")
                }
            }
        }

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
