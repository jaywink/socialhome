from markdownx.forms import ImageForm

from socialhome.models import ImageUpload


class MarkdownXImageForm(ImageForm):
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop("user")
        super().__init__(*args, **kwargs)

    def _save(self, *args, **kwargs):
        url = super()._save(*args, **kwargs)
        ImageUpload.objects.create(image=url.replace("/media/", ""), user=self.user)
        return url
