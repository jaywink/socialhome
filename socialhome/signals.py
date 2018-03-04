import logging
import os

from django.conf import settings
from django.db.models.signals import post_delete
from django.dispatch import receiver

from socialhome.models import ImageUpload

logger = logging.getLogger('socialhome')


@receiver(post_delete, sender=ImageUpload, dispatch_uid="delete_upload_from_disk")
def delete_upload_from_disk(instance, **kwargs):
    """Delete the image from disk."""
    try:
        path = os.path.join(settings.MEDIA_ROOT, instance.image.path)
        logger.debug('delete_upload_from_disk: Removing file %s', path)
        os.unlink(path)
    except Exception:
        logger.exception('delete_upload_from_disk: Failed to delete upload %s', instance)
