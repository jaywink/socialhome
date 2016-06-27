from django.contrib.contenttypes.models import ContentType
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect
from django.views.generic import CreateView

from socialhome.content.enums import ContentTarget, Visibility
from socialhome.content.forms import PostForm
from socialhome.content.models import Content


class ContentCreate(CreateView):
    model = Content
    template_name = "content/create.html"

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
