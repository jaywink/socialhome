from braces.views import LoginRequiredMixin
from django.conf import settings
from django.http import Http404
from django.shortcuts import get_object_or_404
from django.templatetags.static import static
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from django.views.generic import TemplateView

from socialhome.content.models import Tag
from socialhome.streams.streams import PublicStream, FollowedStream, TagStream, LimitedStream, LocalStream, TagsStream
from socialhome.utils import get_full_url
from socialhome.users.serializers import ProfileSerializer


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
        if self.request.user.is_authenticated:
            profile = ProfileSerializer(self.request.user.profile, context={'request': self.request}).data
        else:
            profile = {}
        return {
            "currentBrowsingProfileId": getattr(getattr(self.request.user, "profile", None), "id", None),
            "isUserAuthenticated": bool(self.request.user.is_authenticated),
            "streamName": self.stream_name,
            "ownProfile": profile,
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
        name_base = f"{self.stream_type_value}"
        if self.stream_name_extra:
            name_base = f"{name_base}__{self.stream_name_extra}"
        if self.request.user.is_authenticated:
            return f"{name_base}__{self.request.user.id}"
        return name_base

    @property
    def stream_name_extra(self):
        return ""

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


class LocalStreamView(BaseStreamView):
    stream_class = LocalStream

    def get_page_meta(self):
        meta = super().get_page_meta()
        meta.update({
            "title": _("Local stream"),
            "url": get_full_url(reverse("streams:local")),
            "description": _("Contains content from local users."),
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
    tag = None

    def dispatch(self, request, *args, **kwargs):
        if kwargs.get("name"):
            arguments = {"name": kwargs.get("name")}
        elif kwargs.get("uuid"):
            arguments = {"uuid": kwargs.get("uuid")}
        else:
            raise Http404
        self.tag = get_object_or_404(Tag, **arguments)
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["json_context"]["tag"] = {
            "name": self.tag.name,
            "uuid": self.tag.uuid,
        }
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
    def stream_name_extra(self):
        return str(self.tag.id)


class TagsStreamView(LoginRequiredMixin, BaseStreamView):
    stream_class = TagsStream

    def get_page_meta(self):
        meta = super().get_page_meta()
        meta.update({
            "title": _("Followed tags stream"),
            "url": get_full_url(reverse("streams:tags")),
            "description": _("Content from followed tags."),
        })
        return meta


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

