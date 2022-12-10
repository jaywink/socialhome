from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models
from enumfields import EnumField
from federation.entities.activitypub.enums import ActivityType
from model_utils.fields import AutoCreatedField


class Activity(models.Model):
    """
    Model for Activities done by a profile.
    """
    content_object = GenericForeignKey('content_type', 'object_id')
    content_type = models.ForeignKey(ContentType, on_delete=models.PROTECT)
    created = AutoCreatedField()
    fid = models.URLField(editable=False, max_length=255, unique=True)
    object_id = models.PositiveIntegerField()
    profile = models.ForeignKey("users.Profile", on_delete=models.CASCADE)
    type = EnumField(ActivityType)
