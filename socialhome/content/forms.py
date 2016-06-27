from django.forms import ModelForm
from markdownx.widgets import MarkdownxWidget

from socialhome.content.models import Post


class PostForm(ModelForm):
    class Meta:
        model = Post
        fields = ["text", "public"]
        widgets = {
            "text": MarkdownxWidget()
        }
