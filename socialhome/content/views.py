from braces.views import UserPassesTestMixin, JSONResponseMixin, AjaxResponseMixin, LoginRequiredMixin
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect
from django.http.response import Http404
from django.shortcuts import get_object_or_404
from django.views.generic import CreateView, UpdateView, DeleteView, DetailView

from socialhome.content.forms import ContentForm
from socialhome.content.models import Content


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

    def form_valid(self, form):
        object = form.save(commit=False)
        object.save(author=self.request.user.profile)
        return HttpResponseRedirect(self.get_success_url())

    def get_form_kwargs(self):
        """Add user to form kwargs."""
        kwargs = super(ContentCreateView, self).get_form_kwargs()
        kwargs.update({"user": self.request.user, "is_reply": self.is_reply})
        return kwargs

    def get_success_url(self):
        return reverse("home")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["is_reply"] = self.is_reply
        return context


class ContentReplyView(ContentVisibleForUserMixin, ContentCreateView):
    is_reply = True

    def dispatch(self, request, *args, **kwargs):
        content_id = kwargs.get("pk")
        self.parent = get_object_or_404(Content, id=content_id)
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        object = form.save(commit=False)
        object.parent = self.parent
        object.save(author=self.request.user.profile)
        return HttpResponseRedirect(self.get_success_url())

    def get_success_url(self):
        return reverse("content:view-by-slug", kwargs={"pk": self.parent.id, "slug": self.parent.slug})


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
        return reverse("home")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["is_reply"] = self.is_reply
        return context

    @property
    def is_reply(self):
        return True if self.object.parent else False


class ContentDeleteView(UserOwnsContentMixin, DeleteView):
    model = Content
    template_name = "content/delete.html"

    def get_success_url(self):
        return reverse("home")


class ContentView(ContentVisibleForUserMixin, AjaxResponseMixin, JSONResponseMixin, DetailView):
    model = Content
    template_name = "content/detail.html"

    def get_object(self, queryset=None):
        guid = self.kwargs.get("guid")
        if guid:
            return get_object_or_404(Content, guid=guid)
        return super().get_object(queryset=queryset)

    def get_ajax(self, request, *args, **kwargs):
        self.object = self.get_object()
        return self.render_json_response(self.object.dict_for_view(request.user))

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["stream_name"] = "content__%s" % self.object.channel_group_name
        return context
