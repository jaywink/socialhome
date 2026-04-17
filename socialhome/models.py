from django.db import models
from django.utils.translation import gettext_lazy as _
from model_utils.models import TimeStampedModel

from socialhome.users.models import User


# Not used in code but required for exports
class ImageUpload(TimeStampedModel):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="imageuploads")
    image = models.ImageField()

    def __str__(self):
        return self.image.name


def media_file_name(instance, filename):
    return '{0}/{1}/{2}'.format(instance.user.id, instance.category, filename)


class MediaUpload(TimeStampedModel):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="mediauploads")
    media = models.FileField(null=True, blank=True, validators=[], upload_to=media_file_name)
    category = models.CharField(_("Upload Category"), blank=True, max_length=255)

    def __str__(self):
        return self.media.name
