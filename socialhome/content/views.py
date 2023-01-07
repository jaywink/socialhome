import logging

from braces.views import UserPassesTestMixin, LoginRequiredMixin
from django.core.exceptions import ValidationError
from django.urls import reverse
from django.http import HttpResponseRedirect
from django.http.response import Http404
from django.shortcuts import get_object_or_404
from django.template.loader import render_to_string
from django.templatetags.static import static
from django.utils.decorators import method_decorator
from django.views.generic import CreateView, UpdateView, DeleteView, DetailView
from django.views.generic.base import TemplateView
from django.views.generic.detail import SingleObjectMixin
from federation.entities.activitypub.django.views import activitypub_object_view

from socialhome.content.enums import ContentType
from socialhome.content.models import Content
from socialhome.content.serializers import ContentSerializer
from socialhome.streams.enums import StreamType
from socialhome.utils import get_full_url

logger = logging.getLogger("socialhome")


class ContentVisibleForUserMixin(UserPassesTestMixin):
    def test_func(self, user):
        """Ensure user owns content."""
        object = self.get_object()
        return (
            bool(object) and object.visible_for_user(user)
        )


class UserOwnsContentMixin(UserPassesTestMixin):
    raise_exception = Http404

    def test_func(self, user):
        """Ensure user owns content."""
        object = self.get_object()
        return (
            bool(object) and hasattr(user, "profile") and object.author == user.profile
        )


class ContentCreateView(LoginRequiredMixin, TemplateView):
    model = Content
    template_name = "content/vue.html"
    is_reply = False

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["bookmarklet"] = render_to_string("content/bookmarklet.min.js", {}, request=self.request)
        context["is_reply"] = self.is_reply
        context["json_context"] = self.get_json_context()
        return context

    def get_json_context(self):
        return {
            "currentBrowsingProfileId": getattr(getattr(self.request.user, "profile", None), "id", None),
            "isUserAuthenticated": bool(self.request.user.is_authenticated),
        }

    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)


class ContentReplyView(ContentVisibleForUserMixin, ContentCreateView, SingleObjectMixin):
    is_reply = True

    def dispatch(self, request, *args, **kwargs):
        content_id = kwargs.get("pk")
        self.object = self.get_object()
        self.parent = get_object_or_404(Content, id=content_id)
        return super().dispatch(request, *args, **kwargs)

    def get_success_url(self):
        return self.parent.get_absolute_url()

    def get_json_context(self):
        val = super().get_json_context()
        mentions = f'@{self.object.author.finger} '
        if self.object.root_parent:
            if self.object.author.finger != self.object.root_parent.author.finger:
                mentions += f'@{self.object.root_parent.author.finger} '
        val.update({'mentions': mentions, 'rendered': self.parent.rendered})
        return(val)
        

class ContentUpdateView(UserOwnsContentMixin, DetailView):
    model = Content
    template_name = "content/vue.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["is_reply"] = self.is_reply
        context["json_context"] = self.get_json_context()
        return context

    def get_json_context(self):
        context = {
            "currentBrowsingProfileId": getattr(getattr(self.request.user, "profile", None), "id", None),
            "isUserAuthenticated": bool(self.request.user.is_authenticated),
            "isReply": self.is_reply,
            "federate": self.object.federate,
            "includeFollowing": self.object.include_following,
            "pinned": self.object.pinned,
            "showPreview": self.object.show_preview,
            "visibility": self.object.visibility.value
        }

        parent_id = getattr(getattr(self.object, "parent"), "id", None)
        if parent_id is not None:
            context["parent"] = parent_id

        serialized = ContentSerializer(self.object, context={"request": self.request}).data
        context["recipients"] = serialized.get("recipients", [])
        context["text"] = serialized.get("text", "")

        return context

    @property
    def is_reply(self):
        return True if self.object.content_type == ContentType.REPLY else False


# TODO: Implement on front
class ContentDeleteView(UserOwnsContentMixin, DeleteView):
    model = Content
    template_name = "content/delete.html"

    def get_success_url(self):
        next = self.request.GET.get("next")
        if next:
            return next
        return reverse("home")


@method_decorator(activitypub_object_view, name="dispatch")
class ContentView(ContentVisibleForUserMixin, DetailView):
    model = Content
    template_name = "streams/base.html"

    def dispatch(self, request, *args, **kwargs):
        """If share or reply, redirect."""
        self.object = self.get_object()
        if self.object.content_type == ContentType.SHARE:
            return HttpResponseRedirect(self.object.share_of.get_absolute_url())
        elif self.object.content_type == ContentType.REPLY:
            return HttpResponseRedirect(self.object.root_parent.get_absolute_url())
        return super().dispatch(request, *args, **kwargs)

    def get_object(self, queryset=None):
        uuid = self.kwargs.get("uuid")
        if uuid:
            try:
                return get_object_or_404(Content, uuid=uuid)
            except ValidationError as ex:
                logger.debug("ContentView.get_object - failed at get_object_or_404: %s", ex)
                raise Http404()
        return super().get_object(queryset=queryset)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["json_context"] = self.get_json_context()
        context["meta"] = self.get_page_meta()
        return context

    def get_json_context(self):
        return {
            "currentBrowsingProfileId": getattr(getattr(self.request.user, "profile", None), "id", None),
            "isUserAuthenticated": bool(self.request.user.is_authenticated),
            "streamName": "%s__%s" % (StreamType.CONTENT.value, self.object.channel_group_name),
            "content": self.get_serialized_content(),
        }

    def get_page_meta(self):
        return {
            "type": "article",
            # TODO get longer text depending on user agent, for example twitter
            "title": self.object.short_text,
            "url": self.object.url,
            # TODO this could be for example second paragraph found
            "description": self.object.short_text,
            # TODO get image from text
            "image": get_full_url(static("images/logo/Socialhome-dark-300.png")),
            "author_url": self.object.author.home_url,
            "author_name": self.object.author.name,
        }

    def get_serialized_content(self):
        serializer = ContentSerializer(instance=self.object, context={"request": self.request})
        return serializer.data
