from django.forms import ModelForm
from markdownx.widgets import MarkdownxWidget

from socialhome.content.models import Post
from socialhome.content.utils import safe_text_for_markdown_code


class PostForm(ModelForm):
    class Meta:
        model = Post
        fields = ["text", "public"]
        widgets = {
            "text": MarkdownxWidget()
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop("user", None)
        super(PostForm, self).__init__(*args, **kwargs)

    def clean_text(self):
        """Sanitize text if user is untrusted."""
        if self.user.trusted_editor:
            return self.cleaned_data["text"]
        return safe_text_for_markdown_code(self.cleaned_data["text"])
