# -*- coding: utf-8 -*-
from uuid import uuid4

from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver

from socialhome.users.models import User, Profile


@receiver(post_save, sender=User)
def create_user_profile(sender, **kwargs):
    if kwargs.get("created"):
        # Create the user profile
        user = kwargs.get("instance")
        profile = Profile.objects.create(
            user=user,
            name=user.name,
            nickname=user.username,
            email=user.email,
            handle="%s@%s" % (user.username, settings.SOCIALHOME_DOMAIN),
            guid=str(uuid4()),
        )
        if settings.SOCIALHOME_GENERATE_USER_RSA_KEYS_ON_SAVE:
            profile.generate_new_rsa_key()
