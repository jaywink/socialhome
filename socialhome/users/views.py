# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals

from django.core.urlresolvers import reverse
from django.shortcuts import redirect
from django.views.generic import DetailView, ListView, RedirectView, UpdateView

from django.contrib.auth.mixins import LoginRequiredMixin, AccessMixin

from socialhome.content.enums import ContentTarget
from socialhome.content.models import Content
from socialhome.enums import Visibility
from .models import User


class UserDetailView(AccessMixin, DetailView):
    model = User
    # These next two lines tell the view to index lookups by username
    slug_field = "username"
    slug_url_kwarg = "username"

    def get_context_data(self, **kwargs):
        context = super(UserDetailView, self).get_context_data(**kwargs)
        context["contents"] = self._collect_contents()
        return context

    def _collect_contents(self):
        """Collect rendered content objects."""
        contents_qs = self._get_contents_queryset()
        contents = []
        for content in contents_qs:
            contents.append({
                "content": content.content_object.render(),
                "obj": content,
            })
        return contents

    def _get_contents_queryset(self):
        """Get queryset for content objects.

        Limit by content visibility.
        """
        contents = Content.objects.filter(target=ContentTarget.PROFILE, user=self.object)
        if not self.request.user.is_authenticated():
            contents = contents.filter(visibility=Visibility.PUBLIC)
        elif self.request.user != self.target_user:
            # TODO: filter out also LIMITED until contacts implemented
            contents = contents.exclude(visibility__in=[Visibility.LIMITED, Visibility.SELF])
        return contents.order_by("order")

    def dispatch(self, request, *args, **kwargs):
        """Handle profile visibility checks.

        Redirect to login if not allowed to see profile.
        """
        self.target_user = User.objects.get(username=self.kwargs.get("username"))
        if self.target_user.visibility == Visibility.PUBLIC:
            return super(UserDetailView, self).dispatch(request, *args, **kwargs)
        if request.user.is_authenticated():
            if self.target_user.visibility == Visibility.SITE:
                return super(UserDetailView, self).dispatch(request, *args, **kwargs)
            # TODO: handle Visibility.LIMITED once contacts are implemented
            # Currently falls back to lowest level, ie SELF
            elif self.target_user.visibility in (Visibility.SELF, Visibility.LIMITED) and \
                    request.user == self.target_user:
                return super(UserDetailView, self).dispatch(request, *args, **kwargs)
        return self.handle_no_permission()


class OrganizeContentUserDetailView(UserDetailView):
    template_name = "users/user_detail_organize.html"

    def get_object(self):
        # Only get the User record for the user making the request
        return User.objects.get(username=self.request.user.username)

    def post(self, request, *args, **kwargs):
        """Save sort order."""
        self._save_sort_order(request.POST.get("sort_order").split(","))
        return redirect(self.get_success_url())

    def _save_sort_order(self, card_ids):
        """Update Content `order` values according to sort order."""
        qs_ids = self._get_contents_queryset().values_list("id", flat=True)
        for i in range(0, len(card_ids)):
            # Only allow updating cards that are in our qs
            if card_ids[i] in qs_ids:
                Content.objects.filter(id=card_ids[i]).update(order=i)

    def get_success_url(self):
        return reverse("users:detail", kwargs={"username": self.request.user.username})


class UserRedirectView(LoginRequiredMixin, RedirectView):
    permanent = False

    def get_redirect_url(self):
        return reverse("users:detail",
                       kwargs={"username": self.request.user.username})


class UserUpdateView(LoginRequiredMixin, UpdateView):

    fields = ["name", "visibility"]

    # we already imported User in the view code above, remember?
    model = User

    # send the user back to their own page after a successful update
    def get_success_url(self):
        return reverse("users:detail",
                       kwargs={"username": self.request.user.username})

    def get_object(self):
        # Only get the User record for the user making the request
        return User.objects.get(username=self.request.user.username)


class UserListView(LoginRequiredMixin, ListView):
    model = User
    # These next two lines tell the view to index lookups by username
    slug_field = "username"
    slug_url_kwarg = "username"
