from django.forms import ModelForm
from markdownx.widgets import MarkdownxWidget

from socialhome.content.models import Content
from socialhome.content.utils import safe_text_for_markdown_code


class ContentForm(ModelForm):
    class Meta:
        model = Content
        fields = ["text", "visibility", "pinned"]
        widgets = {
            "text": MarkdownxWidget()
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop("user", None)
        super(ContentForm, self).__init__(*args, **kwargs)

    def clean_text(self):
        """Sanitize text if user is untrusted."""
        if self.user.trusted_editor:
            return self.cleaned_data["text"]
        return safe_text_for_markdown_code(self.cleaned_data["text"])
