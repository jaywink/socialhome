from braces.views import StaffuserRequiredMixin
from django.contrib.auth.mixins import LoginRequiredMixin, AccessMixin
from django.core.urlresolvers import reverse
from django.shortcuts import redirect, get_object_or_404
from django.views.generic import DetailView, ListView, UpdateView, TemplateView
from rest_framework.authtoken.models import Token

from socialhome.content.models import Content
from socialhome.streams.streams import ProfilePinnedStream, ProfileAllStream
from socialhome.streams.views import StreamMixin
from socialhome.users.forms import ProfileForm, UserPictureForm
from socialhome.users.models import User, Profile
from socialhome.users.tables import FollowedTable


class UserDetailView(DetailView):
    model = User
    slug_field = "username"
    slug_url_kwarg = "username"

    def get(self, request, *args, **kwargs):
        """Render ProfileDetailView for this user."""
        profile = get_object_or_404(Profile, user__username=kwargs.get("username"))
        return ProfileDetailView.as_view()(request, guid=profile.guid)


class UserAllContentView(UserDetailView):
    def get(self, request, *args, **kwargs):
        """Render ProfileDetailView for this user."""
        profile = get_object_or_404(Profile, user__username=kwargs.get("username"))
        return ProfileAllContentView.as_view()(request, guid=profile.guid)


class ProfileViewMixin(AccessMixin, StreamMixin, DetailView):
    model = Profile
    pinned_content_exists = None
    profile_stream_type = None  # TODO: refactor to use stream type value directly
    slug_field = "guid"
    slug_url_kwarg = "guid"
    template_name = "streams/profile.html"
    target_profile = None
    content_list = None

    def dispatch(self, request, *args, **kwargs):
        """Handle profile visibility checks.

        Redirect to login if not allowed to see profile.
        """
        if not self.target_profile:
            self.target_profile = self.get_target_profile(kwargs.get("guid"))
        if not self.content_list:
            self.content_list = self.get_queryset()
        if self.target_profile.visible_to_user(self.request.user):
            return super().dispatch(request, *args, **kwargs)
        if request.user.is_authenticated:
            self.raise_exception = True
        return self.handle_no_permission()

    def get_context_data(self, **kwargs):
        self.followers_count = Profile.objects.followers(self.object).count()
        context = super().get_context_data(**kwargs)
        context["content_list"] = self.content_list
        context["followers_count"] = self.followers_count
        context["profile_stream_type"] = self.profile_stream_type
        context["pinned_content_exists"] = self.pinned_content_exists
        return context

    def get_json_context(self):
        json_context = super().get_json_context()
        json_context.update({
            "profile": {
                "id": self.target_profile.id,
                "guid": self.target_profile.guid,
                "followersCount": self.followers_count,
                "followingCount": str(self.target_profile.following.count()),
                "handle": self.target_profile.handle,
                "saferImageUrlLarge": self.target_profile.safer_image_url_large,
                "streamType": self.profile_stream_type,
                "pinnedContentExists": self.pinned_content_exists,
            },
        })
        return json_context

    def get_object(self, queryset=None):
        """Ensure DetailView operates on the right queryset when fetching object.

        Since this is a StreamMixin view, we must override get_queryset which is for the content. To ensure
        DetailView works, we override get_object to pass a Profile queryset to get_object up in super.
        """
        return super().get_object(queryset=Profile.objects.all())

    def get_queryset(self):
        stream = self.stream_class(last_id=self.last_id, user=self.request.user, profile=self.target_profile)
        qs, self.throughs = stream.get_content()
        return qs

    def get_target_profile(self, guid):
        return get_object_or_404(Profile, guid=guid)

    @property
    def stream_name(self):
        return "%s__%s" % (self.stream_type_value, self.object.id)


class ProfileDetailView(ProfileViewMixin):
    pinned_content_exists = True
    profile_stream_type = "pinned"
    stream_class = ProfilePinnedStream

    def dispatch(self, request, *args, **kwargs):
        """Ensure we have pinned content. If not, render all content instead."""
        self.target_profile = self.get_target_profile(kwargs.get("guid"))
        self.content_list = self.get_queryset()
        if not self.content_list.exists():
            return ProfileAllContentView.as_view()(request, guid=self.kwargs.get("guid"))
        return super().dispatch(request, *args, **kwargs)


class ProfileAllContentView(ProfileViewMixin):
    profile_stream_type = "all_content"
    stream_class = ProfileAllStream

    def dispatch(self, request, *args, **kwargs):
        """Ensure we have pinned content. If not, render all content instead."""
        self.target_profile = self.get_target_profile(kwargs.get("guid"))
        qs = Content.objects.profile_pinned(self.target_profile, request.user)
        if qs.filter(pinned=True).exists():
            self.pinned_content_exists = True
        return super().dispatch(request, *args, **kwargs)


class OrganizeContentProfileDetailView(ProfileDetailView):
    template_name = "users/profile_detail_organize.html"

    def get_object(self, queryset=None):
        # Only get the Profile record for the user making the request
        return Profile.objects.get(user=self.request.user)

    def dispatch(self, request, *args, **kwargs):
        """Use current user."""
        kwargs.update({"guid": request.user.profile.guid})
        self.kwargs.update({"guid": request.user.profile.guid})
        return super().dispatch(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        """Save sort order."""
        self.object = self.get_object()
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
        return reverse("home")


class ProfileUpdateView(LoginRequiredMixin, UpdateView):
    form_class = ProfileForm
    model = Profile

    def get_success_url(self):
        return reverse("users:detail", kwargs={"username": self.request.user.username})

    def get_object(self, queryset=None):
        return Profile.objects.get(guid=self.request.user.profile.guid)


class UserPictureUpdateView(LoginRequiredMixin, UpdateView):
    form_class = UserPictureForm
    model = User
    template_name = "users/userpicture_form.html"

    def get_success_url(self):
        return reverse("users:picture-update")

    def get_object(self, queryset=None):
        return User.objects.get(id=self.request.user.id)


class UserListView(StaffuserRequiredMixin, ListView):
    model = User
    slug_field = "username"
    slug_url_kwarg = "username"
    redirect_unauthenticated_users = True
    raise_exception = True


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
        return Profile.objects.get(guid=self.request.user.profile.guid)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        table = FollowedTable(self.object.following.all(), order_by=self.request.GET.get("sort"))
        table.paginate(page=self.request.GET.get("page", 1), per_page=25)
        context["followed_table"] = table
        return context
