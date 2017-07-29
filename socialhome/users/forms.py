from django.forms import ModelForm

from socialhome.content.utils import safe_text
from socialhome.users.models import Profile


class ProfileForm(ModelForm):
    class Meta:
        model = Profile
        fields = ["name", "visibility"]

    def clean_name(self):
        return safe_text(self.cleaned_data["name"])
