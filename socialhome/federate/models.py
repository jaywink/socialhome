from uuid import uuid4

from django.db import models
from enumfields import EnumField
from model_utils.fields import AutoCreatedField, AutoLastModifiedField


#
# class Activity(models.Model):
#     actor = models.ForeignKey("users.Profile", on_delete=models.CASCADE)
#     created = AutoCreatedField()
#     modified = AutoLastModifiedField()
#     type = EnumField(ActivityType)
#     uuid = models.UUIDField(unique=True, default=uuid4, editable=False)
#
#     def __str__(self):
#         return f"{self.type} by {self.actor} ({self.uuid})"
