from braces.views import UserPassesTestMixin
from django.conf import settings
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect
from django.http.response import Http404
from django.views.generic import CreateView, UpdateView, TemplateView, DeleteView

from socialhome.publisher.forms import ContentForm
from socialhome.publisher.models import Content
from socialhome.users.models import Profile
from socialhome.users.views import ProfileDetailView


class ContentCreateView(CreateView):
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


class UserOwnsContentMixin(UserPassesTestMixin):
    raise_exception = Http404

    def test_func(self, user):
        """Ensure user owns content."""
        object = self.get_object()
        return bool(object) and object.author == user.profile


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

    def get_context_data(self, **kwargs):
        context = super(ContentDeleteView, self).get_context_data(**kwargs)
        context["content"] = self.object.render()
        return context


class HomeView(TemplateView):
    template_name = "pages/home.html"

    def get(self, request, *args, **kwargs):
        """Redirect to user detail view if root page is a profile."""
        if settings.SOCIALHOME_ROOT_PROFILE:
            profile = Profile.objects.get(user__username=settings.SOCIALHOME_ROOT_PROFILE)
            return ProfileDetailView.as_view()(request, guid=profile.guid)
        return super(HomeView, self).get(request, *args, **kwargs)
