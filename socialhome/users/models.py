import logging
import os

from Crypto.PublicKey import RSA
from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.urls import reverse
from django.utils.functional import cached_property
from django.utils.translation import ugettext_lazy as _
from enumfields import EnumIntegerField
from federation.utils.text import validate_handle, decode_if_bytes
from model_utils.models import TimeStampedModel
from versatileimagefield.fields import VersatileImageField, PPOIField
from versatileimagefield.image_warmer import VersatileImageFieldWarmer
from versatileimagefield.placeholder import OnDiscPlaceholderImage

from socialhome.content.utils import safe_text
from socialhome.enums import Visibility
from socialhome.users.querysets import ProfileQuerySet
from socialhome.users.utils import get_pony_urls, generate_rsa_private_key
from socialhome.utils import get_full_media_url

logger = logging.getLogger("socialhome")


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

    # Picture
    picture = VersatileImageField(
        _("Picture"), upload_to="profiles/", width_field="picture_width", height_field="picture_height",
        placeholder_image=OnDiscPlaceholderImage(path=os.path.join(
            os.path.dirname(os.path.abspath(__file__)), "..", "static", "images", "pony300.png",
        )), blank=True, null=True, max_length=255, ppoi_field="picture_ppoi",
    )
    picture_height = models.PositiveIntegerField(_("Picture height"), blank=True, null=True)
    picture_width = models.PositiveIntegerField(_("Picture width"), blank=True, null=True)
    picture_ppoi = PPOIField("Picture PPOI")

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

    def copy_picture_to_profile(self):
        """Copy picture to profile image urls"""
        if self.picture:
            self.profile.image_url_small = get_full_media_url(self.picture.crop["50x50"].name)
            self.profile.image_url_medium = get_full_media_url(self.picture.crop["100x100"].name)
            self.profile.image_url_large = get_full_media_url(self.picture.crop["300x300"].name)
            self.profile.save(update_fields=["image_url_small", "image_url_medium", "image_url_large"])

    def init_pictures_on_disk(self):
        """Create image versions on disk."""
        picture_warmer = VersatileImageFieldWarmer(
            instance_or_queryset=self,
            rendition_key_set="profile_picture",
            image_attr="picture",
        )
        picture_warmer.warm()


class Profile(TimeStampedModel):
    """Profile data for local and remote users."""
    user = models.OneToOneField(User, on_delete=models.CASCADE, null=True)

    # Fields mirroring 'User' table since all our Profiles are not local
    name = models.CharField(_("Name"), blank=True, max_length=255)
    email = models.EmailField(_("email address"), blank=True)

    # GUID
    guid = models.CharField(_("GUID"), max_length=255, unique=True, editable=False, blank=True, null=True)

    # Globally unique handle in format username@domain.tld
    handle = models.CharField(_("Handle"), editable=False, max_length=255, unique=True, blank=True, null=True)

    # Federation identifier
    fid = models.URLField(_("Federation ID"), editable=False, max_length=255, unique=True)

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

    def __str__(self) -> str:
        # TODO if no handle something else
        return f"{self.name} ({self.handle} / {self.fid})"

    def get_absolute_url(self):
        # TODO if no handle, something else?
        return reverse("users:profile-detail", kwargs={"guid": self.guid})

    @property
    def home_url(self):
        if not self.user:
            # TODO: this is basically "diaspora" - support other networks too by looking at where user came from
            return self.remote_url
        return self.url

    @property
    def name_or_handle(self):
        # TODO or guid or fid?
        return self.name or self.handle

    @property
    def remote_url(self):
        # TODO fix this
        return "https://%s/people/%s" % (self.handle.split("@")[1], self.guid)

    def save(self, *args, **kwargs):
        # Protect against empty guids which the search indexing would crash on
        # TODO need to ditch this requirement
        if not self.guid:
            raise ValueError("Profile must have a guid!")
        # TODO need to ditch this requirement
        if not validate_handle(self.handle):
            raise ValueError("Not a valid handle")
        # Set default pony images if image urls are empty
        if not self.image_url_small or not self.image_url_medium or not self.image_url_large:
            ponies = get_pony_urls()
            for idx, attr in enumerate(["image_url_large", "image_url_medium", "image_url_small"]):
                if not getattr(self, attr, None):
                    setattr(self, attr, ponies[idx])
        # Ensure handle is *always* lowercase
        # TODO only if handle
        self.handle = self.handle.lower()
        # Ensure keys are converted to str before saving
        self.rsa_private_key = decode_if_bytes(self.rsa_private_key)
        self.rsa_public_key = decode_if_bytes(self.rsa_public_key)
        # Ensure local profile has a fid
        if not self.fid and self.is_local:
            self.fid = self.url
        super().save(*args, **kwargs)

    @property
    def url(self):
        return "%s%s" % (settings.SOCIALHOME_URL, self.get_absolute_url())

    def generate_new_rsa_key(self, bits=4096):
        """Generate a new RSA private key

        Also cache the public key for faster retrieval into own field.
        """
        key = generate_rsa_private_key(bits=bits)
        self.rsa_public_key = key.publickey().exportKey()
        self.rsa_private_key = key.exportKey()
        self.save(update_fields=("rsa_private_key", "rsa_public_key"))

    @cached_property
    def private_key(self):
        """Required by federation.

        Corresponds to private key.
        """
        if self.rsa_private_key:
            return RSA.importKey(self.rsa_private_key)

    @cached_property
    def key(self):
        """Required by federation.

        Corresponds to public key.
        """
        if self.rsa_public_key:
            return RSA.importKey(self.rsa_public_key)

    @property
    def public(self):
        """Is this profile public or one of the more limited visibilities?"""
        return self.visibility == Visibility.PUBLIC

    @property
    def is_local(self):
        """If the profile has a user, it's local."""
        return self.user is not None

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

    @property
    def username_part(self):
        # TODO only if handle
        return self.handle.split("@")[0]

    def visible_to_user(self, user):
        """Check whether the given user should be able to see this profile.

        User not logged in: see on PUBLIC
        User logged in: see own or LIMITED + SITE
        """
        if self.visibility == Visibility.PUBLIC:
            return True
        elif user.is_authenticated:
            if self.visibility != Visibility.SELF or user.profile == self:
                return True
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
    def absolute_image_url(profile, image_name):
        """Returns absolute version of image URL of given size if they wasn't absolute"""
        url = safe_text(profile.image_urls[image_name])

        if url.startswith("/"):
            return "https://%s%s" % (
                profile.handle.split("@")[1], url,
            )
        return url

    @staticmethod
    def from_remote_profile(remote_profile):
        """Create a Profile from a remote Profile entity."""
        logger.info("from_remote_profile - Create or updating %s", remote_profile)
        defaults = {
            "name": safe_text(remote_profile.name),
            "visibility": Visibility.PUBLIC if remote_profile.public else Visibility.LIMITED,
            "image_url_large": Profile.absolute_image_url(remote_profile, "large"),
            "image_url_medium": Profile.absolute_image_url(remote_profile, "medium"),
            "image_url_small": Profile.absolute_image_url(remote_profile, "small"),
            "location": safe_text(remote_profile.location),
            "email": safe_text(remote_profile.email),
        }
        public_key = safe_text(remote_profile.public_key)
        if public_key:
            # Only update public key if it has a value
            defaults["rsa_public_key"] = public_key
        for img_size in ["small", "medium", "large"]:
            # Possibly fix some broken by bleach urls
            defaults["image_url_%s" % img_size] = defaults["image_url_%s" % img_size].replace("&amp;", "&")
        logger.debug("from_remote_profile - defaults %s", defaults)
        profile, created = Profile.objects.update_or_create(
            # TODO only use fid here?
            guid=safe_text(remote_profile.guid),
            handle=safe_text(remote_profile.handle),
            fid=safe_text(remote_profile.id),
            defaults=defaults,
        )
        logger.info("from_remote_profile - created %s, profile %s", created, profile)
        return profile
