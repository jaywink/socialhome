from uuid import uuid4

import django_rq
from django.conf import settings
from django.db import transaction
from django.db.models.signals import post_save, m2m_changed
from django.dispatch import receiver

from socialhome.notifications.tasks import send_follow_notification
from socialhome.users.models import User, Profile


@receiver(post_save, sender=User)
def create_user_profile(sender, **kwargs):
    if kwargs.get("created"):
        # Create the user profile
        user = kwargs.get("instance")
        profile = Profile.objects.create(
            user=user,
            name=user.name,
            email=user.email,
            handle="%s@%s" % (user.username, settings.SOCIALHOME_DOMAIN),
            guid=str(uuid4()),
        )
        if settings.SOCIALHOME_GENERATE_USER_RSA_KEYS_ON_SAVE:
            profile.generate_new_rsa_key()


@receiver(m2m_changed, sender=User.followers.through)
def user_followers_change(sender, instance, action, **kwargs):
    """Deliver notification on new followers."""
    if action == "post_add":
        def on_commit():
            for id in kwargs.get("pk_set"):
                django_rq.enqueue(send_follow_notification, id, instance.id)
        transaction.on_commit(on_commit)
