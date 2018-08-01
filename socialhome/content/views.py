from braces.views import UserPassesTestMixin, LoginRequiredMixin
from django.db.models import Q
from django.urls import reverse
from django.http import HttpResponseRedirect
from django.http.response import Http404
from django.shortcuts import get_object_or_404
from django.template.loader import render_to_string
from django.templatetags.static import static
from django.views.generic import CreateView, UpdateView, DeleteView, DetailView

from socialhome.content.enums import ContentType
from socialhome.content.forms import ContentForm
from socialhome.content.models import Content
from socialhome.content.serializers import ContentSerializer
from socialhome.streams.enums import StreamType
from socialhome.utils import get_full_url


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


class ContentCreateView(LoginRequiredMixin, CreateView):
    model = Content
    form_class = ContentForm
    template_name = "content/edit.html"
    is_reply = False

    def get_form_kwargs(self):
        """Add user to form kwargs."""
        kwargs = super(ContentCreateView, self).get_form_kwargs()
        kwargs.update({"user": self.request.user, "is_reply": self.is_reply})
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["bookmarklet"] = render_to_string("content/bookmarklet.min.js", {}, request=self.request)
        context["is_reply"] = self.is_reply
        return context

    def get_initial(self):
        initial = super().get_initial()
        initial["text"] = self._get_text_initial_from_parameters()
        return initial

    def _get_text_initial_from_parameters(self):
        parameters = {}
        if self.request.GET.get("url"):
            parameters["url"] = self.request.GET.get("url")
        if self.request.GET.get("title"):
            parameters["title"] = self.request.GET.get("title")
        if self.request.GET.get("notes"):
            parameters["notes"] = self.request.GET.get("notes")
        if parameters:
            return render_to_string("content/_bookmarklet_initial.html", parameters, request=self.request)


class ContentBookmarkletView(ContentCreateView):
    template_name = "content/bookmarklet.html"


class ContentReplyView(ContentVisibleForUserMixin, ContentCreateView):
    is_reply = True

    def dispatch(self, request, *args, **kwargs):
        content_id = kwargs.get("pk")
        self.parent = get_object_or_404(Content, id=content_id)
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        self.object = form.save(parent=self.parent)
        return HttpResponseRedirect(self.get_success_url())

    def get_success_url(self):
        return self.parent.get_absolute_url()


class ContentUpdateView(UserOwnsContentMixin, UpdateView):
    model = Content
    form_class = ContentForm
    template_name = "content/edit.html"

    def get_form_kwargs(self):
        kwargs = super(ContentUpdateView, self).get_form_kwargs()
        kwargs.update({
            "instance": self.object,
            "user": self.request.user,
            "is_reply": self.is_reply,
        })
        return kwargs

    def get_success_url(self):
        return self.object.parent.get_absolute_url() if self.is_reply else self.object.get_absolute_url()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["is_reply"] = self.is_reply
        return context

    @property
    def is_reply(self):
        return True if self.object.content_type == ContentType.REPLY else False


class ContentDeleteView(UserOwnsContentMixin, DeleteView):
    model = Content
    template_name = "content/delete.html"

    def get_success_url(self):
        next = self.request.GET.get("next")
        if next:
            return next
        return reverse("home")


class ContentView(ContentVisibleForUserMixin, DetailView):
    model = Content
    template_name = "streams/base.html"

    def dispatch(self, request, *args, **kwargs):
        """If share or reply, redirect."""
        self.object = self.get_object()
        if self.object.content_type == ContentType.SHARE:
            return HttpResponseRedirect(self.object.share_of.get_absolute_url())
        elif self.object.content_type == ContentType.REPLY:
            return HttpResponseRedirect(self.object.parent.get_absolute_url())
        return super().dispatch(request, *args, **kwargs)

    def get_object(self, queryset=None):
        guid = self.kwargs.get("guid")
        if guid:
            return get_object_or_404(Content, Q(guid=guid) | Q(uuid=guid))
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
