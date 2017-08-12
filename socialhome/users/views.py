from braces.views import StaffuserRequiredMixin
from django.contrib.auth.mixins import LoginRequiredMixin, AccessMixin
from django.core.urlresolvers import reverse
from django.shortcuts import redirect, get_object_or_404
from django.views.generic import DetailView, ListView, UpdateView, TemplateView
from rest_framework.authtoken.models import Token

from socialhome.content.models import Content
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


class ProfileViewMixin(AccessMixin, DetailView):
    model = Profile
    slug_field = "guid"
    slug_url_kwarg = "guid"
    template_name = "streams/profile.html"
    target_profile = None
    content_list = None

    def dispatch(self, request, *args, **kwargs):
        """Handle profile visibility checks.

        Redirect to login if not allowed to see profile.
        """
        self.target_profile = get_object_or_404(Profile, guid=self.kwargs.get("guid"))
        if self.target_profile.visible_to_user(self.request.user):
            return super().dispatch(request, *args, **kwargs)
        if request.user.is_authenticated:
            self.raise_exception = True
        return self.handle_no_permission()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["followers_count"] = Profile.objects.followers(self.object).count()
        return context


class ProfileDetailView(ProfileViewMixin):
    def dispatch(self, request, *args, **kwargs):
        """Ensure we have pinned content. If not, render all content instead."""
        self.content_list = self._get_contents_queryset()
        if not self.content_list.exists():
            return ProfileAllContentView.as_view()(request, guid=self.kwargs.get("guid"))
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["content_list"] = self.content_list
        context["pinned_content_exists"] = True
        context["stream_name"] = "profile__%s" % self.object.id
        context["profile_stream_type"] = "pinned"
        return context

    def _get_contents_queryset(self):
        return Content.objects.profile_pinned(self.kwargs.get("guid"), self.request.user)


class ProfileAllContentView(ProfileViewMixin):
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        qs = self._get_contents_queryset()
        context["content_list"] = qs[:30]
        if self.object.user:
            context["pinned_content_exists"] = qs.filter(pinned=True).exists()
        else:
            context["pinned_content_exists"] = False
        context["stream_name"] = "profile_all__%s" % self.object.id
        context["profile_stream_type"] = "all_content"
        return context

    def _get_contents_queryset(self):
        return Content.objects.profile(self.kwargs.get("guid"), self.request.user)


class OrganizeContentProfileDetailView(ProfileDetailView):
    template_name = "users/profile_detail_organize.html"

    def get_object(self, queryset=None):
        # Only get the Profile record for the user making the request
        return Profile.objects.get(user=self.request.user)

    def dispatch(self, request, *args, **kwargs):
        """User current user."""
        self.kwargs.update({"guid": request.user.profile.guid})
        return super().dispatch(request, *args, **kwargs)

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
