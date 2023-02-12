from allauth.account.forms import SignupForm
from allauth.socialaccount.forms import SignupForm as SocialAccountSignupForm
from django import forms
from django.conf import settings
from django.utils.translation import ugettext_lazy as _

from socialhome.content.utils import safe_text
from socialhome.users.models import Profile, User


class ProfileForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ["name", "visibility"]

    def clean_name(self):
        return safe_text(self.cleaned_data["name"])


class UserPictureForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ["picture"]


class UserSignupFormMixin(forms.Form):
    account_request_reason = forms.CharField(
        label=_("Account request reason"),
        max_length=255,
        required=True,
        widget=forms.Textarea(),
        help_text=_("This instance requires admin approval for new accounts. Tell us why you would want to have an "
                    "account? Be descriptive with a few sentences to improve the chance of admins approving your "
                    "request."),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not settings.ACCOUNT_SIGNUP_REQUIRE_ADMIN_APPROVAL:
            del self.fields['account_request_reason']

    def save(self, request):
        # noinspection PyUnresolvedReferences
        user = super().save(request)
        if settings.ACCOUNT_SIGNUP_REQUIRE_ADMIN_APPROVAL:
            # noinspection PyUnresolvedReferences
            account_request_reason = self.cleaned_data.get("account_request_reason")
            user.account_request_reason = account_request_reason
            user.save(update_fields=["account_request_reason"])
        return user


class UserSignupForm(UserSignupFormMixin, SignupForm):
    pass


class UserSocialAccountSignupForm(UserSignupFormMixin, SocialAccountSignupForm):
    pass
