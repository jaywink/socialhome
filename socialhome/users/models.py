from Crypto.PublicKey import RSA
from django.contrib.auth.models import AbstractUser
from django.core.urlresolvers import reverse
from django.core.validators import validate_email
from django.db import models
from django.utils.functional import cached_property
from django.utils.translation import ugettext_lazy as _
from enumfields import EnumIntegerField
from model_utils.models import TimeStampedModel

from socialhome.content.utils import safe_text
from socialhome.enums import Visibility
from socialhome.federate.utils.generic import generate_rsa_private_key
from socialhome.users.querysets import ProfileQuerySet
from socialhome.users.utils import get_pony_urls


class User(AbstractUser):

    # First Name and Last Name do not cover name patterns
    # around the globe.
    name = models.CharField(_("Name of User"), blank=True, max_length=255)

    # Trusted editor defines whether user is allowed some extra options, for example in content creation
    # Users that are trusted might be able to inject harmful content into the system, for example
    # with unlimited usage of HTML tags.
    trusted_editor = models.BooleanField(_("Trusted editor"), default=False)

    # Relationships
    # TODO remove in favour of Profile.following
    followers = models.ManyToManyField("users.Profile", verbose_name=_("Followers"), related_name="following_set")
    following = models.ManyToManyField("users.Profile", verbose_name=_("Following"), related_name="followers_set")

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

    def get_absolute_url(self):
        return reverse("users:detail", kwargs={"username": self.username})


class Profile(TimeStampedModel):
    """Profile data for local and remote users."""
    user = models.OneToOneField(User, on_delete=models.CASCADE, null=True)

    # Fields mirroring 'User' table since all our Profiles are not local
    name = models.CharField(_("Name"), blank=True, max_length=255)
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

    # Following
    following = models.ManyToManyField("self", verbose_name=_("Following"), related_name="followers", symmetrical=False)

    objects = ProfileQuerySet.as_manager()

    def __str__(self):
        return "%s (%s)" % (self.name, self.handle)

    def get_absolute_url(self):
        return reverse("users:profile-detail", kwargs={"guid": self.guid})

    def save(self, *args, **kwargs):
        # Protect against empty guids which the search indexing would crash on
        if not self.guid:
            raise ValueError("Profile must have a guid!")
        # Set default pony images if image urls are empty
        if not self.image_url_small or not self.image_url_medium or not self.image_url_large:
            ponies = get_pony_urls()
            for idx, attr in enumerate(["image_url_large", "image_url_medium", "image_url_small"]):
                if not getattr(self, attr, None):
                    setattr(self, attr, ponies[idx])
        super().save(*args, **kwargs)

    @property
    def home_url(self):
        if not self.user:
            # TODO: this is basically "diaspora" - support other networks too by looking at where user came from
            return self.remote_url
        return self.get_absolute_url()

    @property
    def remote_url(self):
        return "https://%s/people/%s" % (self.handle.split("@")[1], self.guid)

    def generate_new_rsa_key(self):
        """Generate a new RSA private key

        Also cache the public key for faster retrieval into own field.
        """
        key = generate_rsa_private_key()
        self.rsa_public_key = key.publickey().exportKey()
        self.rsa_private_key = key.exportKey()
        self.save(update_fields=("rsa_private_key", "rsa_public_key"))

    @cached_property
    def private_key(self):
        """Required by federation.

        Corresponds to private key.
        """
        return RSA.importKey(self.rsa_private_key)

    @cached_property
    def key(self):
        """Required by federation.

        Corresponds to public key.
        """
        return RSA.importKey(self.rsa_public_key)

    @property
    def public(self):
        """Is this profile public or one of the more limited visibilities?"""
        return self.visibility == Visibility.PUBLIC

    def safer_image_url(self, size):
        """Return a most likely more working image url for the profile.

        Some urls are proven to be relative to host instead of absolute urls.
        """
        attr = "image_url_%s" % size
        if getattr(self, attr).startswith("/"):
            return "https://%s%s" % (
                self.handle.split("@")[1], getattr(self, attr),
            )
        return getattr(self, attr)

    @property
    def safer_image_url_small(self):
        return self.safer_image_url("small")

    @property
    def safer_image_url_medium(self):
        return self.safer_image_url("medium")

    @property
    def safer_image_url_large(self):
        return self.safer_image_url("large")

    @cached_property
    def following_ids(self):
        return self.following.values_list("id", flat=True)

    def visible_to_user(self, user):
        """Check whether the given user should be able to see this profile."""
        if self.visibility == Visibility.PUBLIC:
            return True
        elif user.is_authenticated:
            if self.visibility == Visibility.SITE or user.profile == self:
                return True
        # TODO: handle Visibility.LIMITED once contacts are implemented
        return False

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

    @staticmethod
    def from_remote_profile(remote_profile):
        """Create a Profile from a remote Profile entity."""
        profile, _created = Profile.objects.update_or_create(
            guid=safe_text(remote_profile.guid),
            handle=safe_text(remote_profile.handle),
            defaults={
                "name": safe_text(remote_profile.name),
                "visibility": Visibility.PUBLIC if remote_profile.public else Visibility.LIMITED,
                "rsa_public_key": safe_text(remote_profile.public_key),
                "image_url_large": safe_text(remote_profile.image_urls["large"]),
                "image_url_medium": safe_text(remote_profile.image_urls["medium"]),
                "image_url_small": safe_text(remote_profile.image_urls["small"]),
                "location": safe_text(remote_profile.location),
                "email": safe_text(remote_profile.email),
            },
        )
        return profile
