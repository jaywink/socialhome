from django.forms import ModelForm
from markdownx.widgets import MarkdownxWidget

from socialhome.content.models import Content
from socialhome.content.utils import safe_text_for_markdown


class ContentForm(ModelForm):
    class Meta:
        model = Content
        fields = ["text", "visibility", "pinned", "show_preview"]
        widgets = {
            "text": MarkdownxWidget()
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop("user", None)
        is_reply = kwargs.pop("is_reply", False)
        super(ContentForm, self).__init__(*args, **kwargs)
        if is_reply:
            self.fields.pop("visibility")
            self.fields.pop("pinned")
        else:
            self.fields["visibility"].widget.attrs = {"class": "form-control"}
            self.fields["pinned"].widget.attrs = {"class": "form-check"}
        self.fields["show_preview"].widget.attrs = {"class": "form-check"}
        self.fields["text"].widget.attrs = {"class": "form-control"}

    def clean_text(self):
        """Sanitize text if user is untrusted."""
        if self.user.trusted_editor:
            return self.cleaned_data["text"]
        return safe_text_for_markdown(self.cleaned_data["text"])
