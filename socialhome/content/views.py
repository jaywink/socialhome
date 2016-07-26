from braces.views import UserPassesTestMixin
from django.conf import settings
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect
from django.http.response import Http404
from django.views.generic import CreateView, UpdateView, TemplateView, DeleteView

from socialhome.content.enums import ContentTarget
from socialhome.enums import Visibility
from socialhome.content.forms import PostForm
from socialhome.content.models import Content, Post
from socialhome.users.views import ProfileDetailView


class ContentCreateView(CreateView):
    model = Content
    template_name = "content/edit.html"

    def get_form_class(self):
        """Get correct form class.

        Currently we support only Post's.
        """
        return PostForm

    def form_valid(self, form):
        object = form.save(commit=False)
        object.save(author=self.request.user.profile)
        form.save_m2m()
        Content.objects.create(
            target=ContentTarget.PROFILE,
            author=self.request.user.profile,
            content_object=object,
            visibility=Visibility.PUBLIC  # No other visibility atm
        )
        return HttpResponseRedirect(self.get_success_url())

    def get_form_kwargs(self):
        """Add user to form kwargs."""
        kwargs = super(ContentCreateView, self).get_form_kwargs()
        kwargs.update({"user": self.request.user})
        return kwargs

    def get_success_url(self):
        if self.kwargs.get("location") == "profile":
            return reverse("users:detail", kwargs={"nickname": self.request.user.profile.nickname})
        return reverse("home")


class UserOwnsContentMixin(UserPassesTestMixin):
    raise_exception = Http404

    def test_func(self, user):
        """Ensure user owns content."""
        object = self.get_object()
        return bool(object) and object.author == user.profile


class ContentUpdateView(UserOwnsContentMixin, UpdateView):
    model = Content
    template_name = "content/edit.html"

    def get_form_class(self):
        """Get correct form class."""
        if isinstance(self.object.content_object, Post):
            return PostForm
        raise NotImplementedError()

    def get_form_kwargs(self):
        kwargs = super(ContentUpdateView, self).get_form_kwargs()
        kwargs.update({
            "instance": self.object.content_object,
            "user": self.request.user,
        })
        return kwargs

    def form_valid(self, form):
        object = form.save()
        if object.public:
            Content.objects.filter(id=self.object.id).update(visibility=Visibility.PUBLIC)
        return HttpResponseRedirect(self.get_success_url())

    def get_success_url(self):
        if self.object.target == ContentTarget.PROFILE:
            return reverse("users:detail", kwargs={"nickname": self.object.author.nickname})
        return reverse("home")


class ContentDeleteView(UserOwnsContentMixin, DeleteView):
    model = Content
    template_name = "content/delete.html"

    def get_success_url(self):
        if self.object.target == ContentTarget.PROFILE:
            return reverse("users:detail", kwargs={"nickname": self.object.author.nickname})
        return reverse("home")

    def get_context_data(self, **kwargs):
        context = super(ContentDeleteView, self).get_context_data(**kwargs)
        context["content"] = self.object.content_object.render()
        return context

    def delete(self, request, *args, **kwargs):
        """Delete also linked object."""
        redirection = super(ContentDeleteView, self).delete(request, *args, **kwargs)
        self.object.content_object.delete()
        return redirection


class HomeView(TemplateView):
    template_name = "pages/home.html"

    def get(self, request, *args, **kwargs):
        """Redirect to user detail view if root page is a profile."""
        if settings.SOCIALHOME_ROOT_PROFILE:
            return ProfileDetailView.as_view()(request, nickname=settings.SOCIALHOME_ROOT_PROFILE)
        return super(HomeView, self).get(request, *args, **kwargs)
