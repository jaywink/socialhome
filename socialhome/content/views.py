from braces.views import UserPassesTestMixin, JSONResponseMixin, AjaxResponseMixin, LoginRequiredMixin
from django.conf import settings
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect
from django.http.response import Http404
from django.shortcuts import get_object_or_404
from django.views.generic import CreateView, UpdateView, TemplateView, DeleteView, DetailView

from socialhome.content.forms import ContentForm
from socialhome.content.models import Content
from socialhome.users.models import Profile
from socialhome.users.views import ProfileDetailView


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

    def form_valid(self, form):
        object = form.save(commit=False)
        object.save(author=self.request.user.profile)
        return HttpResponseRedirect(self.get_success_url())

    def get_form_kwargs(self):
        """Add user to form kwargs."""
        kwargs = super(ContentCreateView, self).get_form_kwargs()
        kwargs.update({"user": self.request.user})
        return kwargs

    def get_success_url(self):
        return reverse("home")


class ContentReplyView(ContentVisibleForUserMixin, ContentCreateView):
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
        })
        return kwargs

    def get_success_url(self):
        return reverse("home")


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


class HomeView(TemplateView):
    template_name = "pages/home.html"

    def get(self, request, *args, **kwargs):
        """Redirect to user detail view if root page is a profile or if the user is logged in"""
        if request.user.is_authenticated:
            return ProfileDetailView.as_view()(request, guid=request.user.profile.guid)
        if settings.SOCIALHOME_ROOT_PROFILE:
            profile = get_object_or_404(Profile, user__username=settings.SOCIALHOME_ROOT_PROFILE)
            return ProfileDetailView.as_view()(request, guid=profile.guid)
        return super(HomeView, self).get(request, *args, **kwargs)
