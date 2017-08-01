from django.db import models
from model_utils.models import TimeStampedModel

from socialhome.users.models import User


class ImageUpload(TimeStampedModel):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="imageuploads")
    image = models.ImageField()

    def __str__(self):
        return self.image.name
