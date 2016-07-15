# -*- coding: utf-8 -*-
from __future__ import unicode_literals, absolute_import

import uuid

from Crypto.PublicKey import RSA
from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.core.urlresolvers import reverse
from django.db import models
from django.utils.encoding import python_2_unicode_compatible
from django.utils.translation import ugettext_lazy as _
from enumfields import EnumIntegerField

from socialhome.enums import Visibility
from socialhome.federate.utils import generate_rsa_private_key


@python_2_unicode_compatible
class User(AbstractUser):

    # First Name and Last Name do not cover name patterns
    # around the globe.
    name = models.CharField(_("Name of User"), blank=True, max_length=255)

    # Globally unique identifier
    guid = models.UUIDField(_("GUID"), default=uuid.uuid4, editable=False, unique=True)

    # RSA key
    rsa_private_key = models.TextField(_("RSA private key"), null=True, editable=False)
    rsa_public_key = models.TextField(_("RSA public key"), null=True, editable=False)

    # Local vs remote users
    # Remote users cannot log in and don't have basic local user identity things like a private key
    local = models.BooleanField(_("Local"), default=True, editable=False)

    # Profile visibility
    visibility = EnumIntegerField(Visibility, verbose_name=_("Profile visibility"), default=Visibility.SELF)

    # Trusted editor defines whether user is allowed some extra options, for example in content creation
    # Users that are trusted might be able to inject harmful content into the system, for example
    # with unlimited usage of HTML tags.
    trusted_editor = models.BooleanField(_("Trusted editor"), default=False)

    def __str__(self):
        return self.username

    def get_absolute_url(self):
        return reverse('users:detail', kwargs={'username': self.username})

    def generate_new_rsa_key(self):
        """Generate a new RSA private key

        Also cache the public key for faster retrieval into own field.
        """
        key = generate_rsa_private_key()
        self.rsa_public_key = key.publickey().exportKey()
        self.rsa_private_key = key.exportKey()

    def get_first_name(self):
        """Return User.first_name or part of User.name"""
        if self.first_name:
            return self.first_name
        elif self.name:
            return self.name.split(" ")[0]
        return ""

    def get_last_name(self):
        """Return User.last_name or part of User.name"""
        if self.last_name:
            return self.last_name
        elif self.name:
            try:
                return self.name.split(" ", 1)[1]
            except IndexError:
                return ""
        return ""

    def save(self, *args, **kwargs):
        """Make sure local user always has a key pair."""
        if self.local and (not self.rsa_private_key or not self.rsa_public_key) and \
                settings.SOCIALHOME_GENERATE_USER_RSA_KEYS_ON_SAVE:
            self.generate_new_rsa_key()
        return super(User, self).save(*args, **kwargs)

    @property
    def key(self):
        """Required by Social-Federation."""
        return RSA.importKey(self.rsa_private_key)
