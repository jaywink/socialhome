from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect
from django.views.generic import CreateView, UpdateView

from socialhome.content.enums import ContentTarget, Visibility
from socialhome.content.forms import PostForm
from socialhome.content.models import Content, Post


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
        object.save(user=self.request.user)
        form.save_m2m()
        Content.objects.create(
            target=ContentTarget.PROFILE,
            user=self.request.user,
            content_object=object,
            visibility=Visibility.PUBLIC  # No other visibility atm
        )
        return HttpResponseRedirect(self.get_success_url())

    def get_success_url(self):
        if self.kwargs.get("location") == "profile":
            return reverse("users:detail", kwargs={"username": self.request.user.username})
        return reverse("home")


class ContentUpdateView(UpdateView):
    model = Content
    template_name = "content/edit.html"

    def get_form_class(self):
        """Get correct form class."""
        if isinstance(self.object.content_object, Post):
            return PostForm
        raise NotImplementedError()

    def get_form_kwargs(self):
        kwargs = super(ContentUpdateView, self).get_form_kwargs()
        kwargs.update({"instance": self.object.content_object})
        return kwargs

    def form_valid(self, form):
        object = form.save()
        if object.public:
            Content.objects.filter(id=self.object.id).update(visibility=Visibility.PUBLIC)
        return HttpResponseRedirect(self.get_success_url())

    def get_success_url(self):
        if self.object.target == ContentTarget.PROFILE:
            return reverse("users:detail", kwargs={"username": self.request.user.username})
        return reverse("home")
