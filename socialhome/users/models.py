import logging
import os
import re
import time
from typing import Dict, Optional
from uuid import uuid4

import django_rq
# noinspection PyPackageRequirements
from Crypto.PublicKey import RSA
from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.urls import reverse
from django.utils.functional import cached_property
from django.utils.translation import gettext_lazy as _
from enumfields import EnumIntegerField
from federation.entities.activitypub.enums import ActivityType
from federation.types import UserType
from federation.utils.text import validate_handle, decode_if_bytes
from model_utils.models import TimeStampedModel
# noinspection PyPackageRequirements
from slugify import slugify
from versatileimagefield.fields import VersatileImageField, PPOIField
from versatileimagefield.image_warmer import VersatileImageFieldWarmer
from versatileimagefield.placeholder import OnDiscPlaceholderImage

from socialhome.activities.models import Activity
from socialhome.content.utils import safe_text
from socialhome.enums import Visibility
from socialhome.users.querysets import ProfileQuerySet
from socialhome.users.utils import get_pony_urls, generate_rsa_private_key
from socialhome.utils import get_full_media_url, get_redis_connection

logger = logging.getLogger("socialhome")


class User(AbstractUser):
    # User approved by an admin
    # If ACCOUNT_SIGNUP_REQUIRE_ADMIN_APPROVAL is set to True, the user wont be able to use
    # the system until approved by an admin.
    admin_approved = models.NullBooleanField(_("Admin approved"), default=None)
    # Reason for requesting an account, given on signup if approval is required
    account_request_reason = models.CharField(_("Account request reason"), blank=True, max_length=255)

    # First Name and Last Name do not cover name patterns
    # around the globe.
    name = models.CharField(_("Name of User"), blank=True, max_length=255)

    # Trusted editor defines whether user is allowed some extra options, for example in content creation
    # Users that are trusted might be able to inject harmful content into the system, for example
    # with unlimited usage of HTML tags.
    trusted_editor = models.BooleanField(_("Trusted editor"), default=False)

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

    _previous_admin_approved: bool

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._previous_admin_approved = self.admin_approved

    def __str__(self):
        return self.username

    @property
    def activity_key(self) -> str:
        return f"sh:users:activity:{self.id}"

    @property
    def url(self):
        return f'{settings.SOCIALHOME_URL}{reverse("users:detail", kwargs={"username": self.username})}'

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
        if settings.SOCIALHOME_ROOT_PROFILE == self.username:
            return "/"
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

    def mark_recently_active(self) -> None:
        """
        Flag the user as currently active.
        """
        r = get_redis_connection()
        r.set(self.activity_key, int(time.time()))
        r.expire(self.activity_key, settings.SOCIALHOME_USER_ACTIVITY_SECONDS)

    @cached_property
    def recently_active(self) -> bool:
        """
        Return True if the user is marked as "active recently"
        """
        r = get_redis_connection()
        return r.exists(self.activity_key)

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)

        # If users require approval, and we were approved, send the user an email
        if settings.ACCOUNT_SIGNUP_REQUIRE_ADMIN_APPROVAL and self.admin_approved is True and \
                self._previous_admin_approved is False:
            from socialhome.notifications.tasks import send_account_approval_user_notification
            django_rq.enqueue(send_account_approval_user_notification, user_id=self.id)


# noinspection PyCallingNonCallable
class Profile(TimeStampedModel):
    """Profile data for local and remote users."""
    # Local UUID
    uuid = models.UUIDField(unique=True, blank=True, null=True, editable=False)

    # User object for local profiles
    user = models.OneToOneField(User, on_delete=models.CASCADE, null=True)

    # Fields mirroring 'User' table since all our Profiles are not local
    name = models.CharField(_("Name"), blank=True, max_length=255)
    email = models.EmailField(_("email address"), blank=True)

    # Federation GUID
    # Optional, related to Diaspora network platforms
    guid = models.CharField(_("GUID"), max_length=255, unique=True, editable=False, blank=True, null=True)

    # Globally unique handle in format username@domain.tld
    # Optional, only exists for Diaspora and some other platforms
    handle = models.CharField(_("Handle"), editable=False, max_length=255, unique=True, blank=True, null=True)

    # Federation identifier
    # Optional
    fid = models.URLField(_("Federation ID"), editable=False, max_length=255, unique=True, blank=True, null=True)

    # webfinger subject
    # Optional
    finger = models.CharField(_("Webfinger subject"), editable=False, max_length=255, unique=True, blank=True, null=True)

    # RSA key
    rsa_private_key = models.TextField(_("RSA private key"), null=True, editable=False)
    rsa_public_key = models.TextField(_("RSA public key"), null=True, editable=False)

    # Key ID
    # Optional
    key_id = models.URLField(_("AP Public Key ID"), editable=False, max_length=255, unique=True, blank=True, null=True)

    # Profile visibility
    visibility = EnumIntegerField(Visibility, verbose_name=_("Profile visibility"), default=Visibility.PUBLIC)

    # Image urls
    image_url_large = models.URLField(_("Image - large"), blank=True, max_length=500)
    image_url_medium = models.URLField(_("Image - medium"), blank=True, max_length=500)
    image_url_small = models.URLField(_("Image - small"), blank=True, max_length=500)

    # Location
    location = models.CharField(_("Location"), max_length=128, blank=True)

    # NSFW status
    nsfw = models.BooleanField(_("NSFW"), default=False, help_text=_("Should users content be considered NSFW?"))

    # Following
    following = models.ManyToManyField("self", verbose_name=_("Following"), related_name="followers", symmetrical=False)

    # Followers fid
    # optional
    followers_fid = models.URLField(_("AP Followers FID"), editable=False, max_length=255, unique=True, blank=True, null=True)

    # Tags
    followed_tags = models.ManyToManyField(
        "content.Tag", verbose_name=_("Followed tags"), related_name="following_profiles",
    )

    # Federation endpoints
    inbox_private = models.URLField(_("Private inbox"), blank=True)
    inbox_public = models.URLField(_("Public inbox"), blank=True)

    # Federation protocol
    protocol = models.CharField(_("Protocol"), blank=True, max_length=20)

    objects = ProfileQuerySet.as_manager()

    def __str__(self) -> str:
        return f"{self.name} ({self.fid or self.handle})"

    def create_activity(self, activity_type: ActivityType, object_id: int = None) -> Activity:
        """
        Create and link a matching activity.
        """
        from django.contrib.contenttypes.models import ContentType as DjangoContentType
        return Activity.objects.create(
            content_type=DjangoContentType.objects.get_for_model(Profile),
            fid=f"{self.fid}#activities/{uuid4()}",
            object_id=object_id or self.id,
            profile=self,
            type=activity_type,
        )

    def get_absolute_url(self):
        return reverse("users:profile-detail", kwargs={"uuid": self.uuid})

    def get_recipient_for_matrix_appservice(self) -> Optional[Dict]:
        if settings.SOCIALHOME_MATRIX_ENABLED:
            return {
                "endpoint": settings.SOCIALHOME_MATRIX_APPSERVICE_BASE_URL,
                "fid": self.mxid,
                "public": self.visibility == Visibility.PUBLIC,
                "protocol": "matrix",
            }

    def get_recipient_for_visibility(self, visibility: Visibility) -> Dict:
        """
        Get a recipient dictionary based on visibility.
        """
        if visibility == Visibility.PUBLIC:
            return {
                "endpoint": self.inbox_public,
                "fid": self.fid,
                "public": True,
                "protocol": self.protocol,
            }
        elif visibility == Visibility.LIMITED:
            return {
                "endpoint": self.inbox_private,
                "fid": self.fid,
                "public": False,
                "protocol": self.protocol,
                "public_key": self.rsa_public_key,
            }
        else:
            raise ValueError("get_recipient_for_visibility - Invalid visibility for federating, "
                             "should be public or limited")

    @property
    def federable(self):
        return UserType(
            id=self.fid or self.handle,
            private_key=self.rsa_private_key,
            handle=self.handle,
            mxid=self.mxid,
        )

    @property
    def home_url(self):
        if not self.user:
            # TODO: this is basically "diaspora" - support other networks too by looking at where user came from
            return self.remote_url
        return self.url

    @property
    def local_url(self) -> str:
        if self.is_local:
            return f"{settings.SOCIALHOME_URL}{self.user.get_absolute_url()}"
        return self.url

    @property
    def mxid(self) -> Optional[str]:
        if not settings.SOCIALHOME_MATRIX_ENABLED:
            return None
        if self.is_local:
            return f"@{self.username_part}:{settings.SOCIALHOME_DOMAIN}"
        # Remote is a bit trickier, we want our shortcode namespace and a globally unique username part
        template = f"@_{settings.SOCIALHOME_MATRIX_APPSERVICE_SHORTCODE}_%%USERNAME%%:{settings.SOCIALHOME_DOMAIN}"
        max_username_part_length = 255 - len(template) + 10  # Leave a few chars for safety
        # Also replace '@' with '_' to not have it fully filtered out.
        handle_or_fid = (self.handle or self.fid).replace("@", "_")
        # And filter out any protocol part
        handle_or_fid = re.sub(r"https?://", "", handle_or_fid)
        # Then replace rest of /'s with _'s
        handle_or_fid = handle_or_fid.replace("/", "_")
        # Compile
        remote_username_part = slugify(handle_or_fid, regex_pattern='^[a-z\\._=-]$')[:max_username_part_length]
        return template.replace("%%USERNAME%%", remote_username_part)

    @property
    def name_or_handle(self):
        return self.name or self.handle or self.fid

    @property
    def remote_url(self):
        # TODO fix this
        # TODO this is completely broken, remove or something better
        return ""
        # return "https://%s/people/%s" % (self.handle.split("@")[1], self.uuid)

    def save(self, *args, **kwargs):
        if not self.uuid:
            self.uuid = uuid4()
        if not self.pk and self.is_local:
            if not self.guid:
                self.guid = str(self.uuid)
            if not self.fid:
                self.fid = self.user.url
            # Default protocol for all new profiles
            self.protocol = "activitypub"

        if not self.fid and not self.handle:
            raise ValueError("Profile must have either a fid or a handle")

        if self.handle:
            # Ensure handle is *always* lowercase
            self.handle = self.handle.lower()
            if not validate_handle(self.handle):
                raise ValueError("Not a valid handle")
        else:
            self.handle = None

        if self.finger:
            # Ensure finger is *always* lowercase
            self.finger = self.finger.lower()
            if not validate_handle(self.finger):
                raise ValueError("Not a valid wefinger subject")
        else:
            self.finger = None

        if self.guid == "":
            self.guid = None

        if not self.key_id:
            self.key_id = None

        if not self.followers_fid:
            self.followers_fid = None

        # Set default pony images if image urls are empty
        if not self.image_url_small or not self.image_url_medium or not self.image_url_large:
            ponies = get_pony_urls()
            for idx, attr in enumerate(["image_url_large", "image_url_medium", "image_url_small"]):
                if not getattr(self, attr, None):
                    setattr(self, attr, ponies[idx])

        # Ensure keys are converted to str before saving
        self.rsa_private_key = decode_if_bytes(self.rsa_private_key)
        self.rsa_public_key = decode_if_bytes(self.rsa_public_key)

        # Set default federation endpoints for local users
        if self.is_local:
            if not self.inbox_private:
                self.inbox_private = f"{self.fid}inbox/"
            if not self.inbox_public:
                self.inbox_public = f"{settings.SOCIALHOME_URL}{reverse('federate:receive-public')}"

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
        if getattr(self, attr).startswith("/") and self.handle:
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
        if not self.handle:
            return ""
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

        if url.startswith("/") and profile.handle:
            return "https://%s%s" % (
                profile.handle.split("@")[1], url,
            )
        return url

    @staticmethod
    def from_remote_profile(remote_profile, force: bool = False):
        """Create a Profile from a remote Profile entity."""
        logger.info("from_remote_profile - Create or updating %s", remote_profile)
        # noinspection PyProtectedMember
        values = {
            "name": safe_text(remote_profile.name),
            "visibility": Visibility.PUBLIC,  # Any profile that has been federated has to be public
            "image_url_large": Profile.absolute_image_url(remote_profile, "large"),
            "image_url_medium": Profile.absolute_image_url(remote_profile, "medium"),
            "image_url_small": Profile.absolute_image_url(remote_profile, "small"),
            "location": safe_text(remote_profile.location),
            "email": safe_text(remote_profile.email),
            "inbox_private": safe_text(remote_profile.inboxes.get("private", "")),
            "inbox_public": safe_text(remote_profile.inboxes.get("public", "")),
            "protocol": remote_profile._source_protocol,
        }
        public_key = safe_text(remote_profile.public_key)
        if public_key:
            # Only update public key if it has a value
            values["rsa_public_key"] = public_key
        for img_size in ["small", "medium", "large"]:
            # Possibly fix some broken by bleach urls
            values["image_url_%s" % img_size] = values["image_url_%s" % img_size].replace("&amp;", "&")
        fid = safe_text(remote_profile.id)
        values['handle'] = safe_text(remote_profile.handle)
        values['guid'] = safe_text(remote_profile.guid)
        values['finger'] = safe_text(remote_profile.finger)
        if fid.startswith('http'):
            # only needed for activitypub profiles
            values['followers_fid'] = safe_text(remote_profile.followers)
            values["key_id"] = safe_text(remote_profile.key_id)
        logger.debug("from_remote_profile - values %s", values)
        if values["guid"]:
            extra_lookups = {"guid": values["guid"]}
        else:
            extra_lookups = {}
        profile, created = Profile.objects.fed_update_or_create(fid, values, extra_lookups, force)
        logger.info("from_remote_profile - created %s, profile %s", created, profile)
        return profile
