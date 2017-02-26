import re
from uuid import uuid4

from CommonMark import commonmark
from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.db.models import Q
from django.template.loader import render_to_string
from django.urls import NoReverseMatch
from django.urls import reverse
from django.utils.functional import cached_property
from django.utils.translation import ugettext_lazy as _
from django_extensions.utils.text import truncate_letters
from enumfields import EnumIntegerField
from model_utils.fields import AutoCreatedField, AutoLastModifiedField

from socialhome.content.utils import make_nsfw_safe, test_tag
from socialhome.enums import Visibility
from socialhome.users.models import User, Profile
from socialhome.utils import safe_clear_cached_property


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


class TagQuerySet(models.QuerySet):
    def get_by_cleaned_name(self, name):
        """Get by name after making sure it's lower case and trimmed."""
        cleaned = name.strip().lower()
        return self.get(name=cleaned)

    def exists_by_cleaned_name(self, name):
        """Exists filter by name after making sure it's lower case and trimmed."""
        cleaned = name.strip().lower()
        return self.filter(name=cleaned).exists()


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


class Content(models.Model):
    text = models.TextField(_("Text"), blank=True)
    rendered = models.TextField(_("Rendered text"), blank=True, editable=False)

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

    remote_created = models.DateTimeField(_("Remote created"), blank=True, null=True)
    created = AutoCreatedField(_('Created'), db_index=True)
    modified = AutoLastModifiedField(_('Modified'))

    def __str__(self):
        return "{text} ({guid})".format(
            text=truncate_letters(self.text, 100), guid=self.guid
        )

    def save(self, author=None, *args, **kwargs):
        if self.pk:
            # Old instance, bust the cache
            self.bust_cache()
        elif author:
            # New with author, set a GUID and author
            self.guid = uuid4()
            self.author = author
        self.fix_local_uploads()
        return super(Content, self).save(*args, **kwargs)

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

    def bust_cache(self):
        """Clear relevant caches for this instance."""
        safe_clear_cached_property(self, "is_nsfw")

    @cached_property
    def is_nsfw(self):
        return self.text.lower().find("#nsfw") > -1

    @property
    def is_local(self):
        if self.author.user:
            return True
        return False

    @property
    def effective_created(self):
        if self.remote_created:
            return self.remote_created
        return self.created

    def render(self):
        """Pre-render text to Content.rendered."""
        text = self.get_and_linkify_tags()
        rendered = commonmark(text).strip()
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
            if line.find("#") == -1 or line[0:4] == "    " or code_block:
                # Just add the whole line
                final_words.append(line)
                continue
            # Check each word separately
            words = line.split(" ")
            for word in words:
                candidate = word.strip().strip("([]),.!?:")
                if candidate.startswith("#"):
                    candidate = candidate.strip("#")
                    if test_tag(candidate.lower()):
                        # Tag
                        found_tags.add(candidate.lower())
                        try:
                            tag_word = word.replace(
                                "#%s" % candidate,
                                "[#%s](%s)" % (
                                    candidate,
                                    reverse("streams:tags", kwargs={"name": candidate.lower()})
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
    def get_contents_for_user(ids, user):
        contents = Content.objects.filter(id__in=ids)
        if not user.is_authenticated():
            contents = contents.filter(visibility=Visibility.PUBLIC)
        else:
            contents = contents.filter(
                Q(author=user.profile) | Q(visibility__in=[Visibility.SITE, Visibility.PUBLIC])
            )
        return contents.order_by("created")

    @staticmethod
    def get_rendered_contents_for_user(ids, user):
        contents = Content.get_contents_for_user(ids, user)
        rendered = []
        for content in contents:
            rendered.append({
                "id": content.id,
                "author": content.author_id,
                "rendered": content.rendered
            })
        return rendered

    def fix_local_uploads(self):
        """Fix the markdown URL of local uploads.

        Basically these need to be remote compatible. So make this:

            ![](/media/markdownx/12345.jpg

        to this:

            ![](https://socialhome.domain/media/markdownx/12345.jpg
        """
        self.text = re.sub(r"!\[\]\(/media/markdownx/", "![](%s/media/markdownx/" % settings.SOCIALHOME_URL, self.text)
