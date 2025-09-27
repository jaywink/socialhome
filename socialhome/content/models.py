import datetime
import punycode
import re
from uuid import uuid4

import arrow
import validators
from bs4 import BeautifulSoup
from bs4.element import NavigableString
from commonmark import commonmark
from django.conf import settings
from django.contrib.contenttypes.fields import GenericRelation
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models.aggregates import Max
from django.template.defaultfilters import truncatechars
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils.functional import cached_property
from django.utils.text import slugify
from django.utils.timezone import get_current_timezone
from django.utils.translation import get_language, gettext_lazy as _
from enumfields import EnumIntegerField
from federation.entities.activitypub.enums import ActivityType
from federation.utils.text import find_elements, TAG_PATTERN, MENTION_PATTERN, URL_PATTERN
from memoize import memoize, delete_memoized
from model_utils.fields import AutoCreatedField, AutoLastModifiedField

from socialhome.activities.models import Activity
from socialhome.content.enums import ContentType
from socialhome.content.querysets import TagQuerySet, ContentQuerySet
from socialhome.enums import Visibility
from socialhome.users.models import Profile
from socialhome.utils import get_full_url


class OpenGraphCache(models.Model):
    url = models.URLField(_("URL"), unique=True)
    title = models.CharField(_("Title"), max_length=256, blank=True)
    description = models.TextField(_("Description"), blank=True)
    image = models.URLField(_("Image URL"), blank=True, max_length=500)
    modified = AutoLastModifiedField(_("Modified"), db_index=True)

    def __str__(self):
        return "%s / %s" % (
            self.url, truncatechars(self.title, 30)
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
    uuid = models.UUIDField(unique=True, default=uuid4, editable=False)

    objects = TagQuerySet.as_manager()

    def __str__(self):
        return "#%s" % self.name

    def get_absolute_url(self):
        slugified_name = slugify(self.name)
        if not slugified_name:
            return reverse('streams:tag-by-uuid', kwargs={"uuid": str(self.uuid)})
        return reverse('streams:tag', kwargs={"name": slugified_name})

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
        """
        # TODO use just id
        return ("%s_%s" % (self.id, slugify(self.name)))[:80]


class Content(models.Model):
    # Local UUID
    uuid = models.UUIDField(unique=True, blank=True, null=True, editable=False)

    text = models.TextField(_("Text"), blank=True)

    # Federation GUID
    # Optional, related to Diaspora network platforms
    guid = models.CharField(_("GUID"), max_length=255, unique=True, editable=False, blank=True, null=True)

    author = models.ForeignKey("users.Profile", on_delete=models.CASCADE, verbose_name=_("Author"))
    visibility = EnumIntegerField(Visibility, default=Visibility.PUBLIC, db_index=True)

    # Federation identifier
    # Optional
    fid = models.URLField(_("Federation ID"), editable=False, max_length=255, unique=True, blank=True, null=True)

    # Reply collection  identifier (some AP platforms)
    # Optional
    replies_fid = models.URLField(_("Reply Collection ID"), editable=False, max_length=255, unique=True, blank=True, null=True)

    # Is this content pinned to the user profile
    pinned = models.BooleanField(_("Pinned to profile"), default=False, db_index=True)
    # Order int to allow ordering content within some context, for example profile
    order = models.PositiveIntegerField(verbose_name=_("Order"), default=1, db_index=True)

    # For example mobile, server or application name
    service_label = models.CharField(_("Service label"), blank=True, max_length=32)

    # oEmbed or preview based on OG tags
    show_preview = models.BooleanField(
        _("Show OEmbed or OpenGraph preview"), default=True,
        help_text=_("Disable to turn off fetching and showing an OEmbed or OpenGraph preview using the links in "
                    "the text."),
    )
    oembed = models.ForeignKey(
        OEmbedCache, verbose_name=_("OEmbed cache"), on_delete=models.SET_NULL, null=True
    )
    opengraph = models.ForeignKey(
        OpenGraphCache, verbose_name=_("OpenGraph cache"), on_delete=models.SET_NULL, null=True
    )

    mentions = models.ManyToManyField("users.Profile", verbose_name=_("Mentions"), related_name="mentioned_in")
    tags = models.ManyToManyField(Tag, verbose_name=_("Tags"), related_name="contents")

    parent = models.ForeignKey(
        "self", on_delete=models.CASCADE, verbose_name=_("Parent"), related_name="children", null=True, blank=True,
    )

    share_of = models.ForeignKey(
        "self", on_delete=models.CASCADE, verbose_name=_("Share of"), related_name="shares", null=True, blank=True,
    )

    federate = models.BooleanField(
        _("Federate to remote servers"), default=True,
        help_text=_("Disable to skip federating this version to remote servers. Note, saved content version "
                    "will still be updated to local streams.")
    )

    # Fields relevant for Visibility.LIMITED only
    limited_visibilities = models.ManyToManyField(
        "users.Profile", verbose_name=_("Limitied visibilities"), related_name="limited_visibilities",
    )
    include_following = models.BooleanField(
        _("Include people I follow"), default=False,
        help_text=_("Automatically includes all the people you follow as recipients."),
    )

    # Dates
    remote_created = models.DateTimeField(_("Remote created"), blank=True, null=True)
    created = AutoCreatedField(_('Created'), db_index=True)
    modified = AutoLastModifiedField(_('Modified'))

    # Cached data on save
    content_type = EnumIntegerField(ContentType, default=ContentType.CONTENT, db_index=True, editable=False)
    local = models.BooleanField(_("Local"), default=False, editable=False)
    rendered = models.TextField(_("Rendered text"), blank=True, editable=False)
    reply_count = models.PositiveIntegerField(_("Reply count"), default=0, editable=False)
    shares_count = models.PositiveIntegerField(_("Shares count"), default=0, editable=False)
    through = models.PositiveIntegerField(_("Latest share id"), default=0, editable=False, db_index=True)
    # Indirect parent in the hierarchy
    root_parent = models.ForeignKey(
        "self", on_delete=models.CASCADE, verbose_name=_("Root parent"), related_name="all_children", null=True,
        blank=True,
    )
    # Whether any local users have replied to this root content.
    # Relevant for root content only.
    has_had_local_replies = models.BooleanField(_("Has root content had local replies"), default=False)

    # Other relations
    activities = GenericRelation(Activity)

    objects = ContentQuerySet.as_manager()

    def __str__(self):
        return f"{truncatechars(self.text, 30)} ({self.content_type}, {self.visibility}, {self.fid or self.guid})"

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
            self.through = self.shares.values_list('id', flat=True).last() or self.id
            if commit:
                Content.objects.filter(id=self.id).update(
                    local=self.local, reply_count=self.reply_count, shares_count=self.shares_count, through=self.through,
                )

    def cache_related_object_data(self):
        """Update parent/shared_of cached data, for example share count"""
        if self.share_of:
            self.share_of.cache_data(commit=True)
        if self.parent:
            self.parent.cache_data(commit=True)
            if self.parent.share_of:
                self.parent.share_of.cache_data(commit=True)
        if self.root_parent:
            self.root_parent.cache_data(commit=True)

    def create_activity(self, activity_type: ActivityType) -> Activity:
        """
        Create and link a matching activity.
        """
        from django.contrib.contenttypes.models import ContentType as DjangoContentType
        return Activity.objects.create(
            content_type=DjangoContentType.objects.get_for_model(Content),
            fid=f"{self.author.fid}#activities/{uuid4()}",
            object_id=self.id,
            profile=self.author,
            type=activity_type,
        )

    def extract_mentions(self):
        # TODO locally created mentions should not have to be ripped out of text
        # For now we just rip out diaspora and AP style mentions until we have UI layer
        from socialhome.users.models import Profile
        mentions = re.findall(r'@{?[\S ]?[^{}@]+[@;]?\s*[\w\-./@]+[\w/]+}?', self.text)
        if not mentions:
            self.mentions.clear()

        handles = set()
        text = self.text
        for mention in mentions:
            handle = mention.lstrip('@{') if ';' not in mention else mention.split(';')[1]
            handle = handle.strip('} ')
            if handle.startswith('http'):
                try:
                    profile = Profile.objects.get(fid=handle)
                    if not profile.handle: continue
                    handle = profile.handle
                except Profile.DoesNotExist:
                    continue
            handles.add(handle)
            # sanitize text and let federation adjust for protocol
            text = text.replace(mention, '@'+handle)
        if self.text != text:
            self.text = text
            Content.objects.filter(id=self.id).update(text=text)

        existing_handles = set(self.mentions.values_list('handle', flat=True))
        to_remove = existing_handles.difference(handles)
        to_add = handles.difference(existing_handles)
        for handle in to_remove:
            try:
                self.mentions.remove(Profile.objects.get(handle=handle))
            except Profile.DoesNotExist:
                pass
        for handle in to_add:
            try:
                self.mentions.add(Profile.objects.get(handle=handle))
            except Profile.DoesNotExist:
                pass

    def get_absolute_url(self):
        if self.slug:
            return reverse("content:view-by-slug", kwargs={"pk": self.id, "slug": self.slug})
        return reverse("content:view", kwargs={"pk": self.id})

    @property
    def has_twitter_oembed(self):
        return self.rendered.find('class="twitter-tweet"') > -1

    @property
    def humanized_timestamp(self):
        """Human readable timestamp ie '2 hours ago'."""
        try:
            humanized = arrow.get(self.modified).humanize(locale=get_language())
        except ValueError:
            humanized = arrow.get(self.modified).humanize()
        return humanized

    @property
    def timestamp_epoch(self):
        return self.modified.astimezone(get_current_timezone()).strftime('%s')

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
        return arrow.get(self.modified.astimezone(get_current_timezone())).format()

    @property
    def url(self):
        return "%s%s" % (settings.SOCIALHOME_URL, self.get_absolute_url())

    @property
    def url_uuid(self):
        return "%s%s" % (settings.SOCIALHOME_URL, reverse("content:view-by-uuid", kwargs={"uuid": self.uuid}))

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
            if self.visibility is None:
                self.visibility = self.root.visibility
            self.pinned = False
            self.root_parent = self.root
            if self.local and not self.root_parent.has_had_local_replies:
                Content.objects.filter(id=self.root_parent.id).update(has_had_local_replies=True)
        elif self.share_of:
            self.content_type = ContentType.SHARE

        if not self.uuid:
            self.uuid = uuid4()
        if not self.pk and self.local:
            if not self.guid:
                self.guid = str(self.uuid)
            if not self.fid:
                self.fid = self.url_uuid
            if self.pinned:
                max_order = Content.objects.top_level().filter(author=self.author).aggregate(Max("order"))["order__max"]
                if max_order is not None:  # If max_order is None, there is likely to be no content yet
                    self.order = max_order + 1

        if not self.fid and not self.guid:
            raise ValueError("Content must have either a fid or a guid")

        self.fix_local_uploads()
        super().save(*args, **kwargs)
        self.cache_related_object_data()
        if self.through == 0 and self.content_type != ContentType.SHARE:
            self.through = self.id
            Content.objects.filter(id=self.id).update(through=self.through)


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
            raise ValidationError("Cannot share own content") # why not?
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
        # Remove html
        cleaned_text = BeautifulSoup(self.rendered, 'html.parser').text
        # Remove urls
        cleaned_text = re.sub(r"http\S+", "", cleaned_text)
        return truncatechars(cleaned_text, 50) or ""

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
        """
        # TODO use only id
        return ("%s_%s" % (self.id, self.uuid))

    def render_for_federation(self):
        """Fix tag and mention links."""
        soup = BeautifulSoup(self.rendered, 'html.parser')
        # Do tag links. Set the hashtag class in case we're dealing with old content
        for link in soup.find_all('a', string=TAG_PATTERN):
            if 'hashtag' not in link.get('class', []):
                link['class'] = ['hashtag'] + link.get('class', [])
            if not link['href'].startswith('http'):
                link['href'] = get_full_url(link['href'])

        # Do mention links
        for link in soup.find_all('a', attrs={'class':'mention'}):
            puny = link.text.split('@')
            puny[-1] = punycode.convert(puny[-1])
            profile = self.mentions.get(finger__iexact='@'.join(puny).lstrip('@'))
            if profile and not profile.is_local:
                link['href'] = profile.remote_url or profile.fid

        # Remove preview
        if self.show_preview:
            if self.oembed:
                oembed = soup.find('iframe')
                oembed.previous.extract()
                oembed.extract()
            if self.opengraph:
                # this may break if content/_og_preview.html changes
                og = soup.find(attrs={'class':'opengraph-card'})
                og.extract()

        return str(soup)

    def render(self):
        """Pre-render text to Content.rendered."""
        self._soup = BeautifulSoup(commonmark(self.text, ignore_html_blocks=True).strip(), 'html.parser')

        self.get_and_linkify_tags()
        self.linkify_mentions()
        self.process_text_links()
        rendered = str(self._soup)

        if self.show_preview:
            if self.oembed:
                rendered = "%s<br>%s" % (
                    rendered, self.oembed.oembed
                )
            if self.opengraph:
                image_in_text = self.opengraph.image and self.text.find(self.opengraph.image) > -1
                rendered = "%s%s" % (
                    rendered,
                    render_to_string("content/_og_preview.html", {
                        "image_in_text": image_in_text,
                        "opengraph": self.opengraph,
                    })
                )

        self.rendered = rendered
        Content.objects.filter(id=self.id).update(rendered=rendered)

    def get_and_linkify_tags(self):
        """Find tags in text and convert them to HTML links.

        Save found tags to the content.
        """
        found_tags = set()
        # federation sets the data-hashtag attributes on inbound AP HTML payloads
        for link in self._soup.find_all('a', attrs={'data-hashtag':True}):
            tag = link['data-hashtag'].lstrip('#')
            found_tags.add(tag)
            if 'hashtag' not in link.get('class', []):
                link['class'] = ['hashtag'] + link.get('class', [])

        for tag in find_elements(self._soup, TAG_PATTERN):
            # ignore url fragments in link text
            final = tag.text.lstrip('#').lower()
            link = tag.find_parent('a')
            if link:
                if link.text != tag.text: continue
                if 'hashtag' not in link.get('class', []):
                    link['class'] = ['hashtag'] + link.get('class', [])
            else:
                sibling = tag.previous_sibling
                if isinstance(sibling, NavigableString) and re.search(URL_PATTERN.pattern+'$', sibling): continue
                link = self._soup.new_tag('a')
                link.append(tag.text)
                link['class'] = 'hashtag'
                tag.replace_with(link)

            #  prepare for linkification
            found_tags.add(final)
            link['data-hashtag'] = final

        self.save_tags(found_tags)
        # linkify
        for link in self._soup.find_all('a', attrs={'data-hashtag':True}):
            link['href'] = reverse("streams:tag", kwargs={"name": link['data-hashtag']})
            del link['data-hashtag']

    def linkify_mentions(self):
        # Linkify mentions
        # federation sets the data-mention attributes on inbound AP HTML payloads
        for link in self._soup.find_all('a', attrs={'data-mention':True}):
            mention = link['data-mention']
            try:
                profile = self.mentions.get(finger__iexact=mention)
            except Profile.DoesNotExist:
                continue
            link['href'] = get_full_url(reverse("users:profile-detail", kwargs={"uuid": profile.uuid}))
            if 'mention' not in link.get('class', []):
                link['class'] = ['mention'] + link.get('class', [])
            del link['data-mention']

        for mention in find_elements(self._soup, MENTION_PATTERN):
            try:
                profile = self.mentions.get(finger__iexact=mention.text.lstrip('@'))
            except Profile.DoesNotExist:
                continue
            link = self._soup.new_tag('a')
            puny = mention.text.split('@')
            puny[-1] = punycode.convert(puny[-1])
            link.append('@'.join(puny))
            link['href'] = get_full_url(reverse("users:profile-detail", kwargs={"uuid": profile.uuid}))
            link['class'] = 'mention'
            mention.replace_with(link)

    def process_text_links(self):
        """Process links in text, adding some attributes and linkifying textual links."""
        for link in self._soup.find_all('a', href=True):
            if link['href'].startswith('/'): continue
            if 'nofollow' not in link.get('rel', []):
                link['rel'] = ['nofollow'] + link.get('rel', [])
            link['target'] = '_blank'
            if not (link.text or link.next):
                link.string = link['href']

        for url in find_elements(self._soup, URL_PATTERN):
            if url.find_parent('a'): continue
            href = url.text
            if not href.startswith('http'):
                href = 'https://' + href
            if validators.url(href):
                link = self._soup.new_tag('a')
                link['href'] = href
                link.string = url.text
                link['rel'] = ['nofollow']
                link['target'] = '_blank'
                url.replace_with(link)

    def fix_local_uploads(self):
        """Fix the markdown URL of local uploads.

        Basically these need to be remote compatible. So make this:

            ![](/media/markdownx/12345.jpg

        to this:

            ![](https://socialhome.domain/media/markdownx/12345.jpg
        """
        self.text = re.sub(r"!\[\]\(/media/uploads/", "![](%s/media/uploads/" % settings.SOCIALHOME_URL, self.text)

    def visible_for_user(self, user):
        """Check if visible to given user.

        Mirrors logic in `ContentQuerySet.visible_for_user`.
        """
        if self.visibility == Visibility.PUBLIC:
            return True
        if user.is_authenticated:
            if self.author == user.profile or self.visibility == Visibility.SITE:
                return True
            if self.limited_visibilities.filter(id=user.profile.id).exists():
                return True
        return False

    def visible_for_fed_user(self, fid):
        """
        Filter by visibiity to given remote fid
        Assumes the fid is extracted from a signed AP request
        """
        if self.visibility == Visibility.PUBLIC:
            return True
        profile = Profile.objects.filter(fid=fid).first()
        if profile:
            if self.limited_visibilities.filter(id=profile.id).exists():
                return True
        return False
