from braces.views import LoginRequiredMixin
from django.conf import settings
from django.shortcuts import get_object_or_404
from django.templatetags.static import static
from django.urls import reverse
from django.utils.translation import ugettext_lazy as _
from django.views.generic import TemplateView

from socialhome.content.models import Tag
from socialhome.streams.streams import PublicStream, FollowedStream, TagStream, LimitedStream
from socialhome.utils import get_full_url


class BaseStreamView(TemplateView):
    last_id = None
    throughs = None
    stream_class = None
    template_name = "streams/base.html"

    def dispatch(self, request, *args, **kwargs):
        self.last_id = request.GET.get("last_id")
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        # noinspection PyUnresolvedReferences
        context = super().get_context_data(**kwargs)
        context["json_context"] = self.get_json_context()
        context["meta"] = self.get_page_meta()

        return context

    def get_json_context(self):
        return {
            "currentBrowsingProfileId": getattr(getattr(self.request.user, "profile", None), "id", None),
            "isUserAuthenticated": bool(self.request.user.is_authenticated),
            "streamName": self.stream_name,
        }

    def get_page_meta(self):
        return {
            "title": self.request.site.name,
            "type": "website",
            "url": settings.SOCIALHOME_URL,
            "image": get_full_url(static("images/logo/Socialhome-dark-300.png")),
            "description": _("A federated social home."),
            "author_url": "",
        }

    @property
    def stream_name(self):
        return self.stream_type_value

    @property
    def stream_type_value(self):
        return self.stream_class.stream_type.value


class LimitedStreamView(LoginRequiredMixin, BaseStreamView):
    stream_class = LimitedStream

    def get_page_meta(self):
        meta = super().get_page_meta()
        meta.update({
            "title": _("Limited stream"),
            "url": get_full_url(reverse("streams:limited")),
            "description": _("Contains non-public content where you are recipient."),
        })
        return meta


class PublicStreamView(BaseStreamView):
    stream_class = PublicStream

    def get_page_meta(self):
        meta = super().get_page_meta()
        meta.update({
            "title": _("Public stream"),
            "url": get_full_url(reverse("streams:public")),
            "description": _("Contains public content from around the network."),
        })
        return meta


class TagStreamView(BaseStreamView):
    stream_class = TagStream

    def dispatch(self, request, *args, **kwargs):
        self.tag = get_object_or_404(Tag, name=kwargs.get("name"))
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["json_context"]["tagName"] = self.tag.name
        return context

    def get_page_meta(self):
        meta = super().get_page_meta()
        meta.update({
            "title": _("#%s stream" % self.tag.name),
            "url": get_full_url(reverse("streams:tag", kwargs={"name": self.tag.name})),
            "description": _("All content tagged with #%s." % self.tag.name),
        })
        return meta

    @property
    def stream_name(self):
        return "%s__%s" % (self.stream_type_value, self.tag.channel_group_name)


class FollowedStreamView(LoginRequiredMixin, BaseStreamView):
    stream_class = FollowedStream

    def get_page_meta(self):
        meta = super().get_page_meta()
        meta.update({
            "title": _("Followed stream"),
            "url": get_full_url(reverse("streams:followed")),
            "description": _("Content from followed users."),
        })
        return meta

    @property
    def stream_name(self):
        return "%s__%s" % (self.stream_type_value, self.request.user.username)
