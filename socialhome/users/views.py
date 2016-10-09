# -*- coding: utf-8 -*-
from django.contrib.auth.mixins import LoginRequiredMixin, AccessMixin
from django.core.urlresolvers import reverse
from django.shortcuts import redirect
from django.views.generic import DetailView, ListView, RedirectView, UpdateView

from socialhome.enums import Visibility
from socialhome.publisher.models import Content
from socialhome.users.models import User, Profile


class UserDetailView(DetailView):
    model = User
    slug_field = "username"
    slug_url_kwarg = "username"

    def get(self, request, *args, **kwargs):
        """Render ProfileDetailView for this user."""
        profile = Profile.objects.get(user__username=kwargs.get("username"))
        return ProfileDetailView.as_view()(request, guid=profile.guid)


class ProfileDetailView(AccessMixin, DetailView):
    model = Profile
    slug_field = "guid"
    slug_url_kwarg = "guid"

    def get_context_data(self, **kwargs):
        context = super(ProfileDetailView, self).get_context_data(**kwargs)
        context["contents"] = self._get_contents_queryset()
        return context

    def _get_contents_queryset(self):
        """Get queryset for content objects.

        Limit by content visibility.
        """
        contents = Content.objects.filter(pinned=True, author=self.object)
        if not self.request.user.is_authenticated():
            contents = contents.filter(visibility=Visibility.PUBLIC)
        elif self.request.user.profile != self.target_profile:
            # TODO: filter out also LIMITED until contacts implemented
            contents = contents.exclude(visibility__in=[Visibility.LIMITED, Visibility.SELF])
        return contents.order_by("order")

    def dispatch(self, request, *args, **kwargs):
        """Handle profile visibility checks.

        Redirect to login if not allowed to see profile.
        """
        self.target_profile = Profile.objects.get(guid=self.kwargs.get("guid"))
        if self.target_profile.visibility == Visibility.PUBLIC:
            return super(ProfileDetailView, self).dispatch(request, *args, **kwargs)
        if request.user.is_authenticated():
            if self.target_profile.visibility == Visibility.SITE:
                return super(ProfileDetailView, self).dispatch(request, *args, **kwargs)
            # TODO: handle Visibility.LIMITED once contacts are implemented
            # Currently falls back to lowest level, ie SELF
            elif self.target_profile.visibility in (Visibility.SELF, Visibility.LIMITED) and \
                    request.user.profile == self.target_profile:
                return super(ProfileDetailView, self).dispatch(request, *args, **kwargs)
        return self.handle_no_permission()


class OrganizeContentProfileDetailView(ProfileDetailView):
    template_name = "users/profile_detail_organize.html"

    def get_object(self, queryset=None):
        # Only get the Profile record for the user making the request
        return Profile.objects.get(user=self.request.user)

    def dispatch(self, request, *args, **kwargs):
        """User current user."""
        self.kwargs.update({"guid": request.user.profile.guid})
        return super(OrganizeContentProfileDetailView, self).dispatch(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        """Save sort order."""
        self.object = self.get_object()
        self._save_sort_order(request.POST.get("sort_order").split(","))
        return redirect(self.get_success_url())

    def _save_sort_order(self, card_ids):
        """Update Content `order` values according to sort order."""
        qs_ids = self._get_contents_queryset().values_list("id", flat=True)
        for i in range(0, len(card_ids)):
            # Only allow updating cards that are in our qs
            id = int(card_ids[i])
            if id in qs_ids:
                Content.objects.filter(id=id).update(order=i)

    def get_success_url(self):
        return reverse("home")


class UserRedirectView(LoginRequiredMixin, RedirectView):
    permanent = False

    def get_redirect_url(self):
        return reverse("users:detail", kwargs={"username": self.request.user.username})


class ProfileUpdateView(LoginRequiredMixin, UpdateView):
    fields = ["name", "visibility"]
    model = Profile

    def get_success_url(self):
        return reverse("users:detail", kwargs={"username": self.request.user.username})

    def get_object(self, queryset=None):
        return Profile.objects.get(guid=self.request.user.profile.guid)


class UserListView(LoginRequiredMixin, ListView):
    model = User
    # These next two lines tell the view to index lookups by username
    slug_field = "username"
    slug_url_kwarg = "username"
