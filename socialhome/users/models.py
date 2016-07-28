# -*- coding: utf-8 -*-
from __future__ import unicode_literals, absolute_import

from Crypto.PublicKey import RSA
from django.contrib.auth.models import AbstractUser
from django.core.urlresolvers import reverse
from django.core.validators import validate_email
from django.db import models
from django.utils.encoding import python_2_unicode_compatible
from django.utils.translation import ugettext_lazy as _
from enumfields import EnumIntegerField
from model_utils.fields import AutoCreatedField, AutoLastModifiedField

from socialhome.enums import Visibility
from socialhome.federate.utils import generate_rsa_private_key


@python_2_unicode_compatible
class User(AbstractUser):

    # First Name and Last Name do not cover name patterns
    # around the globe.
    name = models.CharField(_("Name of User"), blank=True, max_length=255)

    # Trusted editor defines whether user is allowed some extra options, for example in content creation
    # Users that are trusted might be able to inject harmful content into the system, for example
    # with unlimited usage of HTML tags.
    trusted_editor = models.BooleanField(_("Trusted editor"), default=False)

    def __str__(self):
        return self.username

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


class Profile(models.Model):
    """Profile data for local and remote users."""
    user = models.OneToOneField(User, on_delete=models.CASCADE, null=True)

    # Fields partly mirroring 'User' table since all our Profiles are not local
    name = models.CharField(_("Name"), blank=True, max_length=255)
    nickname = models.CharField(_("Nickname"),
        max_length=64, unique=True, help_text=_("Usually username, for local users at least."),
        editable=False
    )
    email = models.EmailField(_("email address"), blank=True)

    # GUID
    guid = models.CharField(_("GUID"), max_length=255, unique=True, editable=False)

    # Globally unique handle in format username@domain.tld
    handle = models.CharField(_("Handle"), editable=False, max_length=255, unique=True, validators=[validate_email])

    # RSA key
    rsa_private_key = models.TextField(_("RSA private key"), null=True, editable=False)
    rsa_public_key = models.TextField(_("RSA public key"), null=True, editable=False)

    # Profile visibility
    visibility = EnumIntegerField(Visibility, verbose_name=_("Profile visibility"), default=Visibility.SELF)

    # Image urls
    image_url_large = models.URLField(_("Image - large"), blank=True)
    image_url_medium = models.URLField(_("Image - medium"), blank=True)
    image_url_small = models.URLField(_("Image - small"), blank=True)

    # Location
    location = models.CharField(_("Location"), max_length=128, blank=True)

    # NSFW status
    nsfw = models.BooleanField(_("NSFW"), default=False, help_text=_("Should users content be considered NSFW?"))

    created = AutoCreatedField(_("Created"))
    modified = AutoLastModifiedField(_("Modified"))

    def __str__(self):
        return "%s (%s)" % (self.name, self.nickname)

    def get_absolute_url(self):
        return reverse("users:detail", kwargs={"nickname": self.nickname})

    def generate_new_rsa_key(self):
        """Generate a new RSA private key

        Also cache the public key for faster retrieval into own field.
        """
        key = generate_rsa_private_key()
        self.rsa_public_key = key.publickey().exportKey()
        self.rsa_private_key = key.exportKey()

    @property
    def key(self):
        """Required by Social-Federation."""
        return RSA.importKey(self.rsa_private_key)

    @property
    def public(self):
        """Is this profile public or one of the more limited visibilities?"""
        return self.visibility == Visibility.PUBLIC

    def get_first_name(self):
        """Return User.first_name or part of Profile.name"""
        if self.user and self.user.first_name:
            return self.user.first_name
        elif self.name:
            return self.name.split(" ")[0]
        return ""

    def get_last_name(self):
        """Return User.last_name or part of Profile.name"""
        if self.user and self.user.last_name:
            return self.user.last_name
        elif self.name:
            try:
                return self.name.split(" ", 1)[1]
            except IndexError:
                return ""
        return ""
