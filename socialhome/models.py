import reversion
from django.db import models
from django.utils.timezone import now
from django_fsm import FSMField, transition
from enumfields import EnumField
from markdownx.models import MarkdownxField
from model_utils.models import TimeStampedModel

from socialhome.enums import PolicyDocumentType
from socialhome.users.models import User


class ImageUpload(TimeStampedModel):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="imageuploads")
    image = models.ImageField()

    def __str__(self):
        return self.image.name


@reversion.register(ignore_duplicates=True)
class PolicyDocument(TimeStampedModel):
    content = MarkdownxField()
    version = models.DateTimeField(auto_now=True)
    published_content = MarkdownxField(editable=False, blank=True)
    published_version = models.DateTimeField(editable=False, null=True)
    state = FSMField(default='draft', choices=[
        ('draft', 'draft'),
        ('published', 'published'),
    ])
    type = EnumField(PolicyDocumentType, unique=True, max_length=30)

    def __str__(self):
        return "%s (%s - %s)" % (self.type, self.state, self.version)

    def save(self, *args, **kwargs):
        with reversion.create_revision():
            super().save(*args, **kwargs)

    @transition(field=state, source=['draft', 'published'], target='draft')
    def edit_draft(self):
        pass

    @transition(field=state, source=['draft', 'published'], target='published')
    def publish(self):
        self.published_content = self.content
        self.published_version = now()
