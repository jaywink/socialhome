from django.db import models
from model_utils.fields import AutoCreatedField


class Payload(models.Model):
    """
    Model for federation payloads.

    For debugging purposes.
    """
    body = models.TextField()
    created = AutoCreatedField()
    entities_found = models.PositiveSmallIntegerField()
    headers = models.TextField()
    method = models.CharField(max_length=10)
    protocol = models.CharField(max_length=30)
    sender = models.CharField(max_length=1000)
    url = models.CharField(max_length=1000)
