from django.contrib.auth.mixins import LoginRequiredMixin, AccessMixin
from django.urls import reverse
from django.shortcuts import redirect, get_object_or_404
from django.utils.translation import ugettext_lazy as _
from django.views.generic import DetailView, ListView, UpdateView, TemplateView, DeleteView
from rest_framework.authtoken.models import Token

from socialhome.content.models import Content
from socialhome.streams.streams import ProfilePinnedStream, ProfileAllStream
from socialhome.streams.views import BaseStreamView
from socialhome.users.forms import ProfileForm, UserPictureForm
from socialhome.users.models import User, Profile
from socialhome.users.serializers import ProfileSerializer
from socialhome.users.tables import FollowedTable
from socialhome.utils import get_full_url


class DeleteAccountView(DeleteView):
    model = User

    def get_object(self, queryset=None):
        return User.objects.get(id=self.request.user.id)

    def get_success_url(self):
        return reverse("home")


class UserDetailView(DetailView):
    model = User
    slug_field = "username"
    slug_url_kwarg = "username"

    def get(self, request, *args, **kwargs):
        """Render ProfileDetailView for this user."""
        profile = get_object_or_404(Profile, user__username=kwargs.get("username"))
        return ProfileDetailView.as_view()(request, guid=profile.uuid)


class UserAllContentView(UserDetailView):
    def get(self, request, *args, **kwargs):
        """Render ProfileDetailView for this user."""
        profile = get_object_or_404(Profile, user__username=kwargs.get("username"))
        return ProfileAllContentView.as_view()(request, guid=profile.uuid)


class ProfileViewMixin(AccessMixin, BaseStreamView, DetailView):
    data = None
    model = Profile
    object = None
    profile_stream_type = None  # TODO: refactor to use stream type value directly
    slug_field = "uuid"
    slug_url_kwarg = "uuid"
    template_name = "streams/base.html"

    def dispatch(self, request, *args, **kwargs):
        """Handle profile visibility checks.

        Redirect to login if not allowed to see profile.
        """
        self.set_object_and_data()
        if self.data:
            return super().dispatch(request, *args, **kwargs)
        if request.user.is_authenticated:
            self.raise_exception = True
        return self.handle_no_permission()

    def get_json_context(self):
        json_context = super().get_json_context()
        json_context["profile"] = self.data
        return json_context

    def get_page_meta(self):
        meta = super().get_page_meta()
        name = self.object.name if self.object.name else self.object.fid
        meta.update({
            "title": name,
            "description": _("Profile of %s." % name),
        })
        return meta

    def set_object_and_data(self):
        if not self.object:
            self.object = self.get_object()
        if not self.data and self.object.visible_to_user(self.request.user):
            self.data = ProfileSerializer(self.object, context={'request': self.request}).data
            self.data["stream_type"] = self.profile_stream_type

    @property
    def stream_name(self):
        return "%s__%s" % (self.stream_type_value, self.object.id)


class ProfileDetailView(ProfileViewMixin):
    profile_stream_type = "pinned"
    stream_class = ProfilePinnedStream

    def dispatch(self, request, *args, **kwargs):
        """Ensure we have pinned content. If not, render all content instead."""
        self.set_object_and_data()
        if self.data and not self.data["has_pinned_content"]:
            return ProfileAllContentView.as_view()(request, guid=self.kwargs.get("uuid"))
        return super().dispatch(request, *args, **kwargs)

    def get_page_meta(self):
        meta = super().get_page_meta()
        meta.update({
            "url": get_full_url(reverse("users:profile-detail", kwargs={"uuid": self.object.uuid})),
        })
        return meta


class ProfileAllContentView(ProfileViewMixin):
    profile_stream_type = "all_content"
    stream_class = ProfileAllStream

    def get_page_meta(self):
        meta = super().get_page_meta()
        meta.update({
            "url": get_full_url(reverse("users:profile-all-content", kwargs={"uuid": self.object.uuid})),
        })
        return meta


class OrganizeContentProfileDetailView(LoginRequiredMixin, ListView):
    model = Content
    template_name = "users/profile_detail_organize.html"

    def dispatch(self, request, *args, **kwargs):
        """Use current user."""
        self.profile = get_object_or_404(Profile, user=self.request.user)
        return super().dispatch(request, *args, **kwargs)

    def get_queryset(self):
        return Content.objects.profile_pinned(self.profile, self.request.user).order_by("order")

    def post(self, request, *args, **kwargs):
        """Save sort order."""
        self._save_sort_order(request.POST.get("sort_order").split(","))
        return redirect(self.get_success_url())

    def _save_sort_order(self, card_ids):
        """Update Content `order` values according to sort order."""
        qs_ids = self.get_queryset().values_list("id", flat=True)
        for i in range(0, len(card_ids)):
            # Only allow updating cards that are in our qs
            card_id = int(card_ids[i])
            if card_id in qs_ids:
                Content.objects.filter(id=card_id).update(order=i)

    def get_success_url(self):
        return reverse("users:detail", kwargs={"username": self.request.user.username})


class ProfileUpdateView(LoginRequiredMixin, UpdateView):
    form_class = ProfileForm
    model = Profile

    def get_success_url(self):
        return reverse("users:detail", kwargs={"username": self.request.user.username})

    def get_object(self, queryset=None):
        return Profile.objects.get(id=self.request.user.profile.id)


class UserPictureUpdateView(LoginRequiredMixin, UpdateView):
    form_class = UserPictureForm
    model = User
    template_name = "users/userpicture_form.html"

    def get_success_url(self):
        return reverse("users:picture-update")

    def get_object(self, queryset=None):
        return User.objects.get(id=self.request.user.id)


class UserAPITokenView(LoginRequiredMixin, TemplateView):
    template_name = "users/user_api_token.html"

    def dispatch(self, request, *args, **kwargs):
        self.object = self.get_object()
        return super().dispatch(request, *args, **kwargs)

    def get_object(self, queryset=None):
        return User.objects.get(id=self.request.user.id)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["token"], _created = Token.objects.get_or_create(user=self.request.user)
        return context

    def get_success_url(self):
        return reverse("users:api-token")

    def post(self, request, *args, **kwargs):
        if request.POST.get("regenerate") == "regenerate":
            self.object.auth_token.delete()
        return redirect(self.get_success_url())


class ContactsFollowedView(LoginRequiredMixin, DetailView):
    model = Profile
    template_name = "users/contacts_followed.html"

    def get_object(self, queryset=None):
        return Profile.objects.get(id=self.request.user.profile.id)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        table = FollowedTable(self.object.following.all(), order_by=self.request.GET.get("sort"))
        table.paginate(page=self.request.GET.get("page", 1), per_page=25)
        context["followed_table"] = table
        return context
