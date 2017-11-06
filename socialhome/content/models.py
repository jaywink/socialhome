import datetime
import re
from uuid import uuid4

import arrow
from CommonMark import commonmark
from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models.aggregates import Max
from django.template.loader import render_to_string
from django.urls import NoReverseMatch
from django.urls import reverse
from django.utils.functional import cached_property
from django.utils.html import escape
from django.utils.text import slugify
from django.utils.translation import ugettext_lazy as _
from django_extensions.utils.text import truncate_letters
from enumfields import EnumIntegerField
from memoize import memoize, delete_memoized
from model_utils.fields import AutoCreatedField, AutoLastModifiedField

from socialhome.content.enums import ContentType
from socialhome.content.querysets import TagQuerySet, ContentQuerySet
from socialhome.content.utils import make_nsfw_safe, test_tag, process_text_links
from socialhome.enums import Visibility
from socialhome.users.models import Profile


class OpenGraphCache(models.Model):
    url = models.URLField(_("URL"), unique=True)
    title = models.CharField(_("Title"), max_length=256, blank=True)
    description = models.TextField(_("Description"), blank=True)
    image = models.URLField(_("Image URL"), blank=True)
    modified = AutoLastModifiedField(_("Modified"), db_index=True)

    def __str__(self):
        return "%s / %s" % (
            self.url, truncate_letters(self.title, 30)
        )


class OEmbedCache(models.Model):
    url = models.URLField(_("URL"), unique=True)
    oembed = models.TextField(_("OEmbed HTML content"))
    modified = AutoLastModifiedField(_("Modified"), db_index=True)

    def __str__(self):
        return self.url


class Tag(models.Model):
    name = models.CharField(_("Name"), max_length=255, unique=True)
    created = AutoCreatedField(_('Created'))

    objects = TagQuerySet.as_manager()

    def __str__(self):
        return "#%s" % self.name

    def save(self, *args, **kwargs):
        """Ensure name is lower case and stripped.

        Note this could lead to unique constraints when saving - make sure to also lower case and trim
        the name when fetching tags, or use the given manager for that.
        """
        self.name = self.name.strip().lower()
        super().save()

    @cached_property
    def channel_group_name(self):
        """Make a safe Channel group name.

        ASCII or hyphens or periods only.
        Prefix with ID as we have to slugify the name and cut long guids due to asgi library group name restriction.
        """
        return ("%s_%s" % (self.id, slugify(self.name)))[:80]


class Content(models.Model):
    text = models.TextField(_("Text"), blank=True)

    # It would be nice to use UUIDField but in practise this could be anything due to other server implementations
    guid = models.CharField(_("GUID"), max_length=255, unique=True)
    author = models.ForeignKey(Profile, on_delete=models.CASCADE, verbose_name=_("Author"))
    visibility = EnumIntegerField(Visibility, default=Visibility.PUBLIC, db_index=True)

    # Is this content pinned to the user profile
    pinned = models.BooleanField(_("Pinned to profile"), default=False, db_index=True)
    # Order int to allow ordering content within some context, for example profile
    order = models.PositiveIntegerField(verbose_name=_("Order"), default=1, db_index=True)

    # For example mobile, server or application name
    service_label = models.CharField(_("Service label"), blank=True, max_length=32)

    # oEmbed or preview based on OG tags
    oembed = models.ForeignKey(
        OEmbedCache, verbose_name=_("OEmbed cache"), on_delete=models.SET_NULL, null=True
    )
    opengraph = models.ForeignKey(
        OpenGraphCache, verbose_name=_("OpenGraph cache"), on_delete=models.SET_NULL, null=True
    )

    tags = models.ManyToManyField(Tag, verbose_name=_("Tags"), related_name="contents")

    parent = models.ForeignKey(
        "self", on_delete=models.CASCADE, verbose_name=_("Parent"), related_name="children", null=True, blank=True,
    )

    share_of = models.ForeignKey(
        "self", on_delete=models.CASCADE, verbose_name=_("Share of"), related_name="shares", null=True, blank=True,
    )

    remote_created = models.DateTimeField(_("Remote created"), blank=True, null=True)
    created = AutoCreatedField(_('Created'), db_index=True)
    modified = AutoLastModifiedField(_('Modified'))

    # Cached data on save
    content_type = EnumIntegerField(ContentType, default=ContentType.CONTENT, db_index=True, editable=False)
    local = models.BooleanField(_("Local"), default=False, editable=False)
    rendered = models.TextField(_("Rendered text"), blank=True, editable=False)
    reply_count = models.PositiveIntegerField(_("Reply count"), default=0, editable=False)
    shares_count = models.PositiveIntegerField(_("Shares count"), default=0, editable=False)

    objects = ContentQuerySet.as_manager()

    def __str__(self):
        return "{text} ({guid})".format(
            text=truncate_letters(self.text, 100), guid=self.guid
        )

    def cache_data(self, commit=False):
        """Calculate some extra data."""
        # Local
        self.local = self.author.user is not None
        if self.pk:
            # Reply count
            share_ids = Content.objects.filter(share_of=self).values_list("id", flat=True)
            self.reply_count = self.children.count() + Content.objects.filter(parent_id__in=share_ids).count()
            # Share count
            self.shares_count = self.shares.count()
            if commit:
                Content.objects.filter(id=self.id).update(
                    local=self.local, reply_count=self.reply_count, shares_count=self.shares_count,
                )

    def cache_related_object_data(self):
        """Update parent/shared_of cached data, for example share count"""
        if self.share_of:
            self.share_of.cache_data(commit=True)
        if self.parent:
            self.parent.cache_data(commit=True)
            if self.parent.share_of:
                self.parent.share_of.cache_data(commit=True)

    def get_absolute_url(self):
        if self.slug:
            return reverse("content:view-by-slug", kwargs={"pk": self.id, "slug": self.slug})
        return reverse("content:view", kwargs={"pk": self.id})

    @property
    def humanized_timestamp(self):
        """Human readable timestamp ie '2 hours ago'."""
        return arrow.get(self.modified).humanize()

    @cached_property
    def root(self):
        """Get root content if a reply or share."""
        if self.content_type == ContentType.CONTENT:
            return self
        elif self.content_type == ContentType.REPLY:
            return self.parent.root
        elif self.content_type == ContentType.SHARE:
            return self.share_of.root

    @property
    def timestamp(self):
        return arrow.get(self.modified).format()

    @property
    def url(self):
        return "%s%s" % (settings.SOCIALHOME_URL, self.get_absolute_url())

    @staticmethod
    @memoize(timeout=604800)  # a week
    def has_shared(content_id, profile_id):
        return Content.objects.filter(id=content_id, shares__author_id=profile_id).exists()

    def save(self, *args, **kwargs):
        if self.parent and self.share_of:
            raise ValueError("Can't be both a reply and a share!")
        self.cache_data()

        if self.parent:
            self.content_type = ContentType.REPLY
            # Ensure replies have sane values
            self.visibility = self.parent.visibility
            self.pinned = False
        elif self.share_of:
            self.content_type = ContentType.SHARE

        if not self.pk:
            if not self.guid:
                self.guid = uuid4()
            if self.pinned:
                max_order = Content.objects.top_level().filter(author=self.author).aggregate(Max("order"))["order__max"]
                if max_order is not None:  # If max_order is None, there is likely to be no content yet
                    self.order = max_order + 1

        self.fix_local_uploads()
        super().save(*args, **kwargs)
        self.cache_related_object_data()

    def save_tags(self, tags):
        """Save given tag relations."""
        current = set(self.tags.values_list("name", flat=True))
        if tags == current:
            return
        to_add = tags - current
        tags_to_add = []
        for tag_name in to_add:
            tag, _created = Tag.objects.get_or_create(name=tag_name)
            tags_to_add.append(tag)
        final_tags = tags_to_add + list(Tag.objects.filter(name__in=tags & current))
        self.tags.set(final_tags)

    def share(self, profile):
        """Share this content as the profile given."""
        if self.content_type != ContentType.CONTENT:
            # TODO: support sharing replies too
            raise ValidationError("Can only share top level content.")
        if self.author == profile:
            raise ValidationError("Cannot share own content")
        if not self.visible_for_user(profile.user):
            raise ValidationError("Content to be shared is not visible to sharer.")
        if self.shares.filter(author=profile).exists():
            raise ValidationError("Profile has already shared this content.")
        # Use get or created as a safety to stop duplicates
        share, _created = Content.objects.get_or_create(author=profile, share_of=self, defaults={
            "visibility": self.visibility,
        })
        delete_memoized(Content.has_shared, self.id, profile.id)
        return share

    def unshare(self, profile):
        """Unshare this content as the profile given."""
        if not self.shares.filter(author=profile).exists():
            raise ValidationError("No share found.")
        try:
            share = Content.objects.get(author=profile, share_of=self)
        except Content.DoesNotExist:
            # Something got before us
            pass
        else:
            share.delete()
            delete_memoized(Content.has_shared, self.id, profile.id)

    @cached_property
    def is_nsfw(self):
        return self.text.lower().find("#nsfw") > -1

    @property
    def effective_modified(self):
        if self.remote_created:
            return self.remote_created
        return self.modified

    @property
    def edited(self):
        """Determine whether Content has been edited.

        Because we do multiple saves in some cases on creation, for example for oEmbed or OpenGraph,
        and a remote content could be delivered multiple times within a short time period, for example via
        relay and original node, we allow 15 minutes before deciding that the content has been edited.

        TODO: it would make sense to store an "edited" flag on the model itself.
        """
        return self.modified > self.created + datetime.timedelta(minutes=15)

    @cached_property
    def short_text(self):
        return truncate_letters(self.text, 50) or ""

    @property
    def short_text_inline(self):
        return self.short_text.replace("\n", " ").replace("\r", "")

    @cached_property
    def slug(self):
        return slugify(self.short_text)

    @cached_property
    def channel_group_name(self):
        """Make a safe Channel group name.

        ASCII or hyphens or periods only.
        Prefix with ID as we have to cut long guids due to asgi library group name restriction.
        """
        return ("%s_%s" % (self.id, slugify(self.guid)))[:80]

    def render(self):
        """Pre-render text to Content.rendered."""
        text = self.get_and_linkify_tags()
        rendered = commonmark(text).strip()
        rendered = process_text_links(rendered)
        if self.is_nsfw:
            rendered = make_nsfw_safe(rendered)
        if self.oembed:
            rendered = "%s<br>%s" % (
                rendered, self.oembed.oembed
            )
        if self.opengraph:
            rendered = "%s%s" % (
                rendered,
                render_to_string("content/_og_preview.html", {"opengraph": self.opengraph})
            )
        self.rendered = rendered
        Content.objects.filter(id=self.id).update(rendered=rendered)

    def get_and_linkify_tags(self):
        """Find tags in text and convert them to Markdown links.

        Save found tags to the content.
        """
        found_tags = set()
        lines = self.text.splitlines(keepends=True)
        final_words = []
        code_block = False
        # Check each line separately
        for line in lines:
            if line[0:3] == "```":
                code_block = not code_block
            # noinspection PyTypeChecker
            if line.find("#") == -1 or line[0:4] == "    " or code_block:
                # Just add the whole line
                final_words.append(line)
                continue
            # Check each word separately
            # noinspection PyTypeChecker
            words = line.split(" ")
            for word in words:
                # noinspection PyTypeChecker
                candidate = word.strip().strip("([]),.!?:")
                # noinspection PyTypeChecker
                if candidate.startswith("#"):
                    # noinspection PyTypeChecker
                    candidate = candidate.strip("#")
                    if test_tag(candidate.lower()):
                        # Tag
                        found_tags.add(candidate.lower())
                        try:
                            # noinspection PyTypeChecker
                            tag_word = word.replace(
                                "#%s" % candidate,
                                "[#%s](%s)" % (
                                    candidate,
                                    reverse("streams:tag", kwargs={"name": candidate.lower()})
                                )
                            )
                            final_words.append(tag_word)
                        except NoReverseMatch:
                            # Don't linkify, seems we can't generate an url for it
                            # TODO: throw to opbeat or just logger?
                            final_words.append(word)
                    else:
                        # Not tag
                        final_words.append(word)
                else:
                    final_words.append(word)
        text = " ".join(final_words)
        self.save_tags(found_tags)
        return text

    @staticmethod
    def get_rendered_contents(qs, user, throughs=None):
        """Get JSON serialized contents.

        :param qs: QuerySet
        :param user: User object
        :param throughs: Optional dict containing through id's
        """
        rendered = []
        for content in qs:
            through = throughs.get(content.id) if throughs else None
            rendered.append(content.dict_for_view(user, through=through))
        return rendered

    def fix_local_uploads(self):
        """Fix the markdown URL of local uploads.

        Basically these need to be remote compatible. So make this:

            ![](/media/markdownx/12345.jpg

        to this:

            ![](https://socialhome.domain/media/markdownx/12345.jpg
        """
        self.text = re.sub(r"!\[\]\(/media/uploads/", "![](%s/media/uploads/" % settings.SOCIALHOME_URL, self.text)

    def dict_for_view(self, user, through=None):
        if not through:
            through = self.id
        humanized_timestamp = "%s (edited)" % self.humanized_timestamp if self.edited else self.humanized_timestamp
        is_author = bool(user.is_authenticated and self.author == user.profile)
        is_following_author = bool(user.is_authenticated and self.author_id in user.profile.following_ids)
        profile_id = user.profile.id if getattr(user, "profile", None) else ""
        return {
            "author": self.author_id,
            "author_guid": self.author.guid,
            "author_handle": self.author.handle,
            "author_home_url": self.author.home_url,
            "author_image": self.author.safer_image_url_small,
            "author_is_local": self.local,
            "author_name": escape(self.author.name) or self.author.handle,
            "author_profile_url": self.author.get_absolute_url(),
            "reply_count": self.reply_count,
            "content_type": self.content_type.string_value,
            "delete_url": reverse("content:delete", kwargs={"pk": self.id}) if is_author else "",
            "detail_url": self.get_absolute_url(),
            "formatted_timestamp": self.timestamp,
            "guid": self.guid,
            "has_shared": Content.has_shared(self.id, profile_id) if profile_id else False,
            "humanized_timestamp": humanized_timestamp,
            "id": self.id,
            "is_authenticated": bool(user.is_authenticated),
            "is_author": is_author,
            "is_following_author": is_following_author,
            "parent": self.parent_id if self.content_type == ContentType.REPLY else "",
            "profile_id": profile_id,
            "rendered": self.rendered,
            "reply_url": reverse("content:reply", kwargs={"pk": self.id}) if user.is_authenticated else "",
            "shares_count": self.shares_count,
            "slug": self.slug,
            "through": through,
            "update_url": reverse("content:update", kwargs={"pk": self.id}) if is_author else "",
        }

    def visible_for_user(self, user):
        """Check if visible to given user.

        Mirrors logic in `ContentQuerySet.visible_for_user`.
        """
        # TODO: handle also LIMITED when contacts implemented
        if self.visibility == Visibility.PUBLIC:
            return True
        if user.is_authenticated and (self.author == user.profile or self.visibility == Visibility.SITE):
            return True
        return False
